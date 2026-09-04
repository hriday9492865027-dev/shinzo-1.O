# Shinzo AI — Data Flow Trace (single chat turn)

1. **Ingress**: `POST /v1/chat` receives `{user_id, conversation_id, message}` (`app/api/routes/chat.py`).
2. **Auth/Rate-limit**: `app/api/middleware/auth.py` + `rate_limit.py` validate the API key and quota.
3. **Safety pre-check**: `app/safety/risk_scoring.py` scores the raw input LOW/MEDIUM/HIGH.
   - HIGH -> `app/safety/response_routing.py` returns a safety-oriented path immediately; pipeline
     below is skipped except for logging (no message content logged, only metadata).
4. **Emotion signal**: `app/emotion/classifier.py` -> `signals.py` produces a non-authoritative signal.
5. **Memory retrieval**: `app/memory/retrieval.py` embeds the current message
   (`app/memory/embeddings.py`) and queries the user's FAISS index (`app/memory/index.py`) for
   relevant, *not exhaustive*, memories.
6. **RAG retrieval** (once knowledge base exists): `app/rag/retriever.py` returns curated context if relevant.
7. **Social intent**: `app/social/social_intent.py` combines relationship state + conversation
   dynamics + rhythm to pick one intent (listen / joke / ask / give space / etc.).
8. **Language profile**: `app/language/style_profile.py` supplies formality/slang/emoji signals
   (default stays natural English; adaptation only if user demonstrates it).
9. **Context build**: `app/core/context_builder.py` merges 3-8 into a single `ContextBundle`.
10. **Generation**: `app/model/inference.py` calls the active `LLMProvider.generate()`.
11. **Human Essence + Authenticity**: `app/human/*.py` adjusts rhythm/brevity/humor, then
    `authenticity_filter.py` rejects/refines robotic or over-therapeutic output.
12. **Response**: FastAPI returns `FinalReply` to the client.
13. **Async memory write**: `app/memory/extraction.py` + `importance_scoring.py` evaluate the
    completed turn and store new memory items if they clear the relevance bar.

## Proactive Flow (background, not user-triggered)
```
APScheduler tick -> proactive.decision_engine ("should I message?")
  NO  -> stop (valid outcome)
  YES -> message_planner -> frequency_guard -> quiet_hours -> human/authenticity checks -> deliver (inbox/push)
```
