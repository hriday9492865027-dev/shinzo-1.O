"""
Fine-tuning entry point for Shinzo AI.

Uses TRL's SFTTrainer with PEFT LoRA (optionally QLoRA via bitsandbytes).
Reads config from training/configs/lora_config.yaml.

NOTE: Requires GPU + Hugging Face Hub access. Run in an environment with:
  - torch >= 2.0 with CUDA
  - transformers, trl, peft, bitsandbytes, datasets, pyyaml, accelerate

Usage:
    python -m training.train
    python -m training.train --config training/configs/lora_config.yaml
    python -m training.train --model Qwen/Qwen2.5-7B-Instruct --epochs 5

See docs/MODEL_STRATEGY.md for the full swap procedure.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_training_records(jsonl_path: str) -> list[dict]:
    """Load processed JSONL and convert to chat-template format for SFTTrainer."""
    from app.model.prompts import BASE_PERSONALITY_PROMPT

    records = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            # Skip proactive records with empty user_message (no input to learn from)
            if not rec.get("user_message", "").strip():
                continue
            records.append(
                {
                    "messages": [
                        {"role": "system", "content": BASE_PERSONALITY_PROMPT},
                        {"role": "user", "content": rec["user_message"]},
                        {"role": "assistant", "content": rec["shinzo_reply"]},
                    ]
                }
            )
    logger.info("Loaded %d training records from %s", len(records), jsonl_path)
    return records


def train(config_path: str, model_override: str = "", epochs_override: int = 0) -> None:
    # ── Imports (heavy — only loaded when training actually runs) ──────────────
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    cfg = load_config(config_path)
    model_name: str = model_override or cfg["model"]["name"]
    adapter_output: str = cfg["model"]["adapter_output_dir"]
    lora_cfg: dict = cfg["lora"]
    quant_cfg: dict = cfg["quantization"]
    train_cfg: dict = cfg["training"]
    data_cfg: dict = cfg["data"]

    if epochs_override:
        train_cfg["num_train_epochs"] = epochs_override

    logger.info("Loading tokenizer: %s", model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Quantization config ────────────────────────────────────────────────────
    bnb_config = None
    if quant_cfg.get("enabled"):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=quant_cfg["load_in_4bit"],
            bnb_4bit_quant_type=quant_cfg["bnb_4bit_quant_type"],
            bnb_4bit_compute_dtype=getattr(torch, quant_cfg["bnb_4bit_compute_dtype"]),
        )
        logger.info("4-bit quantization (QLoRA) enabled")

    logger.info("Loading base model: %s", model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # ── LoRA config ────────────────────────────────────────────────────────────
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        bias=lora_cfg["bias"],
        target_modules=lora_cfg["target_modules"],
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # ── Dataset ────────────────────────────────────────────────────────────────
    train_file = data_cfg["train_file"]
    if not Path(train_file).exists():
        raise FileNotFoundError(
            f"Training file not found: {train_file}\n"
            "Run the dataset pipeline first:\n"
            "  python -m dataset.scripts.pipeline dataset/custom/shinzo_core_v1.jsonl "
            "dataset/processed/shinzo_core_v1_processed.jsonl"
        )
    records = build_training_records(train_file)
    dataset = Dataset.from_list(records)

    val_split = data_cfg.get("validation_split", 0.0)
    if val_split > 0:
        split = dataset.train_test_split(test_size=val_split, seed=42)
        train_ds, eval_ds = split["train"], split["test"]
    else:
        train_ds, eval_ds = dataset, None

    # ── SFTTrainer ─────────────────────────────────────────────────────────────
    sft_args = SFTConfig(
        output_dir=adapter_output,
        num_train_epochs=train_cfg["num_train_epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        warmup_ratio=train_cfg["warmup_ratio"],
        lr_scheduler_type=train_cfg["lr_scheduler_type"],
        weight_decay=train_cfg["weight_decay"],
        max_seq_length=train_cfg["max_seq_length"],
        fp16=train_cfg.get("fp16", False),
        bf16=train_cfg.get("bf16", False),
        logging_steps=train_cfg["logging_steps"],
        save_strategy=train_cfg["save_strategy"],
        eval_strategy=train_cfg["eval_strategy"] if eval_ds else "no",
        load_best_model_at_end=bool(eval_ds),
        metric_for_best_model=train_cfg["metric_for_best_model"],
        report_to=train_cfg.get("report_to", "none"),
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
    )

    logger.info("Starting fine-tuning...")
    trainer.train()

    logger.info("Saving adapter to %s", adapter_output)
    trainer.model.save_pretrained(adapter_output)
    tokenizer.save_pretrained(adapter_output)
    logger.info("Done. Set LLM_ADAPTER_PATH=%s in your .env to use this adapter.", adapter_output)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Shinzo LoRA fine-tuning")
    parser.add_argument(
        "--config",
        default="training/configs/lora_config.yaml",
        help="Path to lora_config.yaml",
    )
    parser.add_argument("--model", default="", help="Override model name from config")
    parser.add_argument("--epochs", type=int, default=0, help="Override epoch count from config")
    args = parser.parse_args()
    train(args.config, model_override=args.model, epochs_override=args.epochs)


if __name__ == "__main__":
    main()
