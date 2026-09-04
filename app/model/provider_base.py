"""
Abstract LLM provider interface.

This is the single seam between Shinzo's application logic (orchestrator, routes) and any
concrete text-generation backend. Every other module (safety, memory, social, human, etc.)
depends only on `LLMProvider` and never on a specific model library — so swapping the base
model, or moving from local inference to a hosted API, never requires touching those modules.

See docs/MODEL_STRATEGY.md for the swap procedure and rationale.
"""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Concrete providers must implement `generate`."""

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """
        Produce a reply string given a system prompt (personality + context, built by
        app/core/context_builder.py) and the latest user message.
        kwargs allow provider-specific overrides (e.g. temperature) without changing the
        interface signature for every provider.
        """
        raise NotImplementedError


class MockProvider(LLMProvider):
    """
    Deterministic, dependency-free provider used for local development and automated tests.

    Why it exists: this sandbox's network egress does not include huggingface.co, so a real
    model cannot be downloaded here. MockProvider lets the entire pipeline (safety -> emotion ->
    memory -> social -> context -> generation -> human essence -> authenticity) be built and
    tested end-to-end without a real model. Swap LLM_PROVIDER=local_hf once running somewhere
    with Hugging Face Hub access (or with weights pre-mounted locally).
    """

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        # Intentionally simple and inspectable — real naturalness/authenticity work happens in
        # app/human/authenticity_filter.py and, later, the fine-tuned adapter. This mock only
        # needs to prove the pipeline wiring is correct.
        return f"[shinzo-mock reply] I hear you saying: \"{user_message.strip()}\""


class LocalHFProvider(LLMProvider):
    """
    Loads a configurable open-weight instruct model via Hugging Face `transformers`, with an
    optional PEFT/LoRA adapter once Milestone 6 fine-tuning produces one.

    Implemented but not exercised in this sandbox (no huggingface.co egress here) — see
    docs/MODEL_STRATEGY.md "Known Sandbox Constraint". Validate in an environment with HF Hub
    access before relying on it.
    """

    def __init__(self, model_name: str, adapter_path: str = "", max_new_tokens: int = 256,
                 temperature: float = 0.8):
        self.model_name = model_name
        self.adapter_path = adapter_path
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self._model = None
        self._tokenizer = None

    def _lazy_load(self) -> None:
        if self._model is not None:
            return
        # Imported lazily so importing this module never requires torch/transformers to be
        # installed unless LocalHFProvider is actually instantiated (keeps MockProvider-only
        # dev/test environments lightweight).
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name)

        if self.adapter_path:
            from peft import PeftModel

            self._model = PeftModel.from_pretrained(self._model, self.adapter_path)

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        self._lazy_load()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(prompt, return_tensors="pt")
        output = self._model.generate(
            **inputs,
            max_new_tokens=kwargs.get("max_new_tokens", self.max_new_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            do_sample=True,
        )
        full_text = self._tokenizer.decode(output[0], skip_special_tokens=True)
        return full_text[len(prompt):].strip()
