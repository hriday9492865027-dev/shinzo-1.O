# Shinzo AI — Architecture

## Module Boundaries & Contract
Every intelligence module exposes a single well-typed entry point and returns a Pydantic model.
The Orchestrator (`app/core/orchestrator.py`) never contains module-specific logic — it only
sequences calls and merges outputs into a `ContextBundle` for the LLM, then post-processes the
LLM output through Human Essence + Authenticity Filter.

## Pipeline (per reactive chat turn)
```
Request
  -> safety.risk_scoring(input)                => RiskAssessment
  -> emotion.signals(input)                     => EmotionSignal
  -> memory.retrieval(input, user_id)           => list[MemoryItem]
  -> rag.retriever(input)                       => list[RagChunk]        (once curated docs exist)
  -> social.social_intent(context)              => SocialIntent
  -> language.style_profile(user_id)            => LanguageProfile
  -> core.context_builder(all of the above)     => ContextBundle
  -> model.inference.generate(ContextBundle)    => RawReply
  -> human.authenticity_filter(RawReply)        => FinalReply
  -> memory.extraction + importance_scoring(turn)  => (async) store new memories
Response -> FinalReply
```

## LLM Provider Abstraction
`app/model/provider_base.py` defines `LLMProvider(ABC)` with `generate(context: ContextBundle) -> str`.
Concrete providers:
- `MockProvider` — deterministic, no network/model download, used for tests & offline dev.
- `LocalHFProvider` — loads a real Hugging Face instruct model (+ optional Shinzo LoRA adapter)
  via `transformers`/`PEFT`.

Selected via `LLM_PROVIDER` env var. The orchestrator only depends on the abstract interface, so
adding a new provider (e.g. a hosted API) never requires touching orchestrator/social/memory/etc.

## Data Ownership
- `app/memory/` owns the SQLite/SQLAlchemy models and is the only module allowed to write to the DB.
- `app/rag/` and `app/memory/` both use FAISS but with **separate indexes** (curated knowledge vs.
  personal memory) — never mixed, since RAG facts and personal memories have different trust levels.

## Safety Is Cross-Cutting
Safety runs first in the pipeline and can short-circuit it (see `SAFETY_POLICY.md`). No other
module may downgrade or skip a safety-routed response.
