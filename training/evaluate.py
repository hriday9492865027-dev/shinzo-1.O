"""
Runs evaluation datasets against a trained Shinzo LoRA adapter.

Usage:
    python -m training.evaluate --adapter ./shinzo_adapter --eval-dir evaluation/

For each JSON file in eval-dir, logs the model's actual reply vs. expected behavior.
Saves results to evaluation/results/<timestamp>_results.json.
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def load_eval_cases(eval_dir: str) -> list[dict]:
    cases = []
    for p in sorted(Path(eval_dir).glob("*.json")):
        with open(p) as f:
            data = json.load(f)
        for item in data:
            item["_source_file"] = p.name
        cases.extend(data)
    logger.info("Loaded %d evaluation cases from %s", len(cases), eval_dir)
    return cases


def run_evaluation(adapter_path: str, eval_dir: str, model_name: str) -> None:
    from app.model.prompts import build_system_prompt
    from app.model.provider_base import LocalHFProvider

    provider = LocalHFProvider(model_name=model_name, adapter_path=adapter_path)

    cases = load_eval_cases(eval_dir)
    results = []

    for case in cases:
        prompt = case.get("prompt", "")
        if not prompt:
            continue  # skip proactive / empty-prompt cases
        context = case.get("context", "")
        system_prompt = build_system_prompt(extra_context=context)

        try:
            reply = provider.generate(system_prompt=system_prompt, user_message=prompt)
        except Exception as exc:
            reply = f"ERROR: {exc}"

        result = {
            "id": case.get("id"),
            "source": case.get("_source_file"),
            "prompt": prompt,
            "model_reply": reply,
            "expected_behavior": case.get("expected_behavior", ""),
            "must_avoid": case.get("must_avoid", []),
        }
        results.append(result)
        logger.info("[%s] %s → %s", case.get("id"), prompt[:60], reply[:80])

    # Save results
    out_dir = Path(eval_dir) / "results"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{ts}_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("Results saved to %s", out_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Evaluate Shinzo LoRA adapter")
    parser.add_argument("--adapter", required=True, help="Path to trained adapter directory")
    parser.add_argument("--eval-dir", default="evaluation", help="Directory of eval JSON files")
    parser.add_argument(
        "--model",
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Base model name (must match adapter)",
    )
    args = parser.parse_args()
    run_evaluation(args.adapter, args.eval_dir, args.model)


if __name__ == "__main__":
    main()
