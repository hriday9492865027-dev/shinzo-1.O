# Shinzo AI — Model Strategy

## Principle
Never architect the product around one model provider. `app/model/provider_base.py` is the only
seam the rest of the system touches.

## Providers
- **MockProvider** (default in this dev sandbox): deterministic template-based replies, zero
  network dependency. Used so the full pipeline (safety/emotion/memory/social/human) can be built
  and tested end-to-end *before* any real model is wired in. This is intentional given the
  zero-budget MVP strategy — prove the architecture first.
- **LocalHFProvider**: loads a configurable open-weight instruct model via `transformers`
  (`LLM_MODEL_NAME` env var, e.g. a Qwen instruct model) with an optional PEFT/LoRA adapter
  (`LLM_ADAPTER_PATH`) once Milestone 6 fine-tuning produces one.

## Swap Procedure
1. Implement a new class in `app/model/provider_base.py` (or a new file) satisfying `LLMProvider`.
2. Register it in the provider factory (`app/model/loader.py`).
3. Set `LLM_PROVIDER` env var. No other module changes.

## Fine-Tuning (Milestone 6, not yet started)
`Base model -> Transformers -> TRL -> PEFT -> LoRA/QLoRA -> (optional Unsloth) -> Shinzo adapter`.
Fine-tuning targets communication *behavior* (warmth, brevity, non-robotic phrasing), not factual
knowledge (that's RAG's job) or safety behavior (that's the layered safety system's job).

## Known Sandbox Constraint
This development container's network egress does not include huggingface.co, so `LocalHFProvider`
cannot be exercised end-to-end here. It is implemented and unit-tested with a mocked
`from_pretrained` call; real download/inference must be validated in an environment with HF Hub
access (or with local weights pre-downloaded and mounted).
