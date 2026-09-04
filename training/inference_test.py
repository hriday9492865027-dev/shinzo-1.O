"""
Manual smoke-test script for a trained Shinzo LoRA adapter.

Runs a short interactive REPL so you can chat with the adapter directly
before integrating it back into the FastAPI application.

Usage:
    python -m training.inference_test --adapter ./shinzo_adapter
    python -m training.inference_test --adapter ./shinzo_adapter --model Qwen/Qwen2.5-7B-Instruct
"""
from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def run_repl(adapter_path: str, model_name: str) -> None:
    from app.model.prompts import build_system_prompt
    from app.model.provider_base import LocalHFProvider

    print(f"\n🔮 Shinzo Inference Test — adapter: {adapter_path}")
    print("Type a message and press Enter. Ctrl+C or 'quit' to exit.\n")

    provider = LocalHFProvider(model_name=model_name, adapter_path=adapter_path)

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break
        if not user_input:
            continue

        reply = provider.generate(
            system_prompt=build_system_prompt(),
            user_message=user_input,
        )
        print(f"Shinzo: {reply}\n")


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(description="Shinzo adapter smoke-test REPL")
    parser.add_argument("--adapter", required=True, help="Path to trained adapter directory")
    parser.add_argument(
        "--model",
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Base model name (must match the adapter)",
    )
    args = parser.parse_args()
    run_repl(args.adapter, args.model)


if __name__ == "__main__":
    main()
