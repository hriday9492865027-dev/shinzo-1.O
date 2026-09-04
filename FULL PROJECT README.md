# SHINZO AI — Master Project README & Build Tracker

> **This file is the single source of truth for the project.**
> If development stops for any reason (session crash, technical error, context loss), upload **this README.md** plus whatever files already exist in the repo, and say: *"continue Shinzo AI from README"*. A build assistant should then be able to determine exactly what exists, what doesn't, and what to build next — without re-reading the original planning PDFs or re-deciding architecture from scratch.

**Last updated:** 2026-09-03
**Current phase:** Milestones 0-4 done. Ready to begin Milestone 5 (custom dataset — actually authoring ~100 examples).
**Next action:** Author `dataset/custom/shinzo_core_v1.jsonl` (raw JSON first, then run through `dataset/scripts/pipeline.py`), covering all 11 categories — see §10 for exact resume state.
**Verified working:** `pytest tests/` → 16/16 passing. `ruff check .` → clean. Server smoke-tested with `uvicorn app.api.main:app` (`/health` and `/v1/chat` both return correctly). Dataset pipeline CLI smoke-tested end-to-end (dedup + category coverage report confirmed correct).
**Known limitation:** This build sandbox's network does not reach huggingface.co, so `LLM_PROVIDER=mock` is what's active/tested. `LocalHFProvider` (real HF model) is implemented in `app/model/provider_base.py` but not yet exercised — validate it in an environment with Hugging Face Hub access before relying on it. See `docs/MODEL_STRATEGY.md`.

---

## 1. What Shinzo AI Is (one paragraph)

Shinzo is an emotionally intelligent AI **companion**, not a Q&A chatbot. It combines a swappable open-weight LLM with a surrounding system of custom modules — memory, emotion signals, social intelligence, human-essence/authenticity filtering, language adaptation, safety, and restrained proactive messaging — so that conversation feels contextual, natural, and non-manipulative. The differentiator is **the architecture around the model**, not the model itself. Full product philosophy lives in `docs/PRODUCT_VISION.md` (to be created).

### Non-negotiable product principles (govern every module's behavior)
1. **Human before helpful** — read the social/emotional situation before deciding to inform, ask, joke, or stay quiet.
2. **Context before response** — never interpret the latest message in isolation from history, memory, style, and emotional signal.
3. **Never force emotion** — a short or flat message isn't automatically a crisis; avoid constant psychoanalysis.
4. **Conversation is not therapy** — supportive, never clinical.
5. **Comfort without dependency** — no guilt, possessiveness, exclusivity claims, or engagement-through-coercion. "Do nothing" is always a valid proactive decision.
6. **Naturalness over perfection** — a plausible-human-friend test beats polished/therapeutic phrasing.
7. **Memory with relevance** — store selectively; retrieve only when it adds value, never just to prove memory works.

---

## 2. System Architecture (high level)

```
USER APP / CHAT INTERFACE
        │
        ▼
SHINZO API (FastAPI)
        │
        ▼
SHINZO ORCHESTRATOR  ──────────────┬───────────┬───────────┐
        │                          │           │           │
     Safety                    Emotion       Memory        RAG
        │                          │           │           │
        └──────────────┬───────────┴───────────┴───────────┘
                        ▼
                Social Intelligence
                        │
                        ▼
                 Context Builder
                        │
                        ▼
                  SHINZO LLM (provider-abstracted)
                        │
                        ▼
          Human Essence Engine → Authenticity Filter
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
         User Reply         Proactive Engine → Scheduler/Guards → Notification
```

The Orchestrator only **routes**; each module below is independently testable behind a clean interface, so any piece (especially the LLM provider) can be swapped without rewriting the rest.

---

## 3. Technology Stack (what + why, per layer)

| Layer | Technology | Why |
|---|---|---|
| Dev workflow | Git/GitHub | Version control, milestone-by-milestone commits |
| Language | Python 3.11 | One language across ML, API, orchestration |
| API | FastAPI + Uvicorn + Pydantic | Async REST, auto-validation, OpenAPI docs |
| LLM | Configurable open-weight instruct model (provider-abstracted, e.g. Qwen family candidate) | Avoids foundation-model training; swappable |
| Model runtime | Hugging Face Transformers + PyTorch | Load/run models & pretrained classifiers |
| Fine-tuning | TRL + PEFT + LoRA/QLoRA (+ optional Unsloth) | Cheap specialization of communication behavior, not knowledge/safety |
| Dataset tooling | HF Datasets + Pandas + Pydantic + JSONL | Clean, validate, structure training data |
| Memory (MVP) | SQLite + SQLAlchemy | Zero-cost structured persistence → PostgreSQL later |
| Semantic search | Sentence-Transformers + FAISS | Meaning-based memory & RAG retrieval |
| Safety | Python rules + Regex + ML classifier + risk scoring | Layered, not a single prompt |
| Emotion | Pretrained HF emotion classifier | Signal, not diagnosis |
| Social Intelligence | Custom Python + Pydantic schemas | Social-state → intent selection |
| Human Essence | Custom Python | Naturalness, rhythm, authenticity filtering |
| Language Adaptation | Python + `lingua-language-detector` + LLM | Style profiling, never forced code-switching |
| Proactive Engine | APScheduler | Decision-gated background jobs (Celery/Redis only if scale demands later) |
| Security | API keys + Argon2/bcrypt + SlowAPI (+ python-jose for JWT later) | AuthN, hashing, rate limiting |
| Notifications | Website inbox → Web Push (Service Workers, pywebpush) | Phase 1 → Phase 2 |
| Testing | Pytest + pytest-asyncio + HTTPX | Unit + async + API tests |
| Code quality | Ruff | Lint/format |
| Deployment | Docker | Packaged only after intelligence is validated |

**Zero-budget rule:** local dev, open models, SQLite, FAISS, open-source libs first. No continuously-hosted large model until product quality is proven.

---

## 4. Complete File Inventory

> **Status legend:** `⬜ Not started` · `🟨 In progress` · `✅ Done` · `🔁 Needs revision`
> Update the Status column every time a file is touched — this is what makes the project resumable.

### 4.1 `docs/` — Architecture & policy documentation (Milestone 0)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `docs/PRODUCT_VISION.md` | Full product philosophy, identity, tone rules, feature catalog (source: Product Vision PDF) | Markdown | ✅ |
| `docs/ARCHITECTURE.md` | Module boundaries, interfaces, orchestrator contract, data flow diagrams | Markdown | ✅ |
| `docs/DATA_FLOW.md` | Step-by-step trace of a message from ingress to reply/proactive send | Markdown | ✅ |
| `docs/SAFETY_POLICY.md` | Risk tiers, escalation rules, crisis handling, what safety must never do | Markdown | ✅ |
| `docs/MODEL_STRATEGY.md` | LLM provider abstraction design, candidate models, swap procedure | Markdown | ✅ |
| `docs/DEVELOPMENT_ROADMAP.md` | Milestone list with acceptance criteria (mirrors §6 below, kept in sync) | Markdown | ✅ |
| `docs/PERSONALITY_SPEC.md` | Formal personality contract: voice qualities, warmth/curiosity/humor rules, hard boundaries, prohibited robotic patterns (Milestone 3) | Markdown | ✅ |

### 4.2 Project root

| File | Purpose | Tech | Status |
|---|---|---|---|
| `README.md` | **This file.** Master tracker/resumability doc | Markdown | ✅ |
| `requirements.txt` | Pinned Python dependencies | pip | ✅ |
| `.env.example` | All required environment variables with dummy values (no real secrets) | dotenv | ✅ |
| `.gitignore` | Excludes venv, `.env`, `__pycache__`, model weights, DB files | — | ✅ |
| `docker-compose.yml` | Local orchestration of API + (future) services | Docker Compose | ⬜ |
| `Dockerfile` | Container build for the FastAPI app | Docker | ⬜ |
| `pyproject.toml` | Ruff config + project metadata | Ruff/PEP 621 | ✅ |

### 4.3 `app/api/` — HTTP layer (Milestone 16–18)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/api/main.py` | FastAPI app instance, router mounting, startup/shutdown events | FastAPI | ✅ |
| `app/api/routes/chat.py` | `POST /v1/chat` — reactive conversation endpoint | FastAPI | ✅ |
| `app/api/routes/proactive.py` | `POST /v1/proactive/trigger` — manual/scheduled proactive trigger | FastAPI | ⬜ |
| `app/api/routes/messages.py` | `GET /v1/messages`, `GET /v1/conversations/{id}` | FastAPI | ⬜ |
| `app/api/routes/health.py` | `GET /health` — liveness/readiness | FastAPI | ✅ |
| `app/api/middleware/auth.py` | API key validation middleware | Argon2/bcrypt | ⬜ |
| `app/api/middleware/rate_limit.py` | Rate limiting | SlowAPI | ⬜ |
| `app/api/schemas/chat.py` | Request/response Pydantic models for chat | Pydantic | ✅ |
| `app/api/schemas/common.py` | Shared schema types (IDs, timestamps, enums) | Pydantic | ✅ |

### 4.4 `app/core/` — Orchestration (Milestone 15)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/core/orchestrator.py` | Central router: calls safety → emotion → memory → RAG → social → context builder → LLM → human essence → authenticity, in order | Python | ⬜ |
| `app/core/context_builder.py` | Assembles the final prompt/context object from all module outputs | Python + Pydantic | ⬜ |
| `app/core/decision_router.py` | Cross-cutting routing decisions (e.g., which conversation mode applies) | Python | ⬜ |
| `app/core/config.py` | Centralized settings loader (env vars → typed config) | Pydantic Settings | ✅ |
| `app/core/logging.py` | Structured logging setup (no sensitive message content logged) | Python `logging` | ✅ |

### 4.5 `app/model/` — LLM provider abstraction (Milestone 2)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/model/loader.py` | Loads base model + optional Shinzo LoRA adapter | Transformers, PyTorch, PEFT | ✅ |
| `app/model/inference.py` | Provider-agnostic `generate()` interface used by the orchestrator | Transformers | ✅ |
| `app/model/prompts.py` | System prompt templates, personality spec injection | Python | ✅ |
| `app/model/provider_base.py` | Abstract provider interface (so swapping models needs no rewrite elsewhere) | Python ABC | ✅ |

### 4.6 `app/emotion/` (Milestone 9)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/emotion/classifier.py` | Wraps a pretrained HF emotion classification model | Transformers | ⬜ |
| `app/emotion/signals.py` | Converts raw classifier scores → structured `EmotionSignal` used downstream (never treated as diagnosis) | Python + Pydantic | ⬜ |

### 4.7 `app/safety/` (part of every milestone; core logic in Milestone 1–2, expanded ongoing)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/safety/rules.py` | Deterministic keyword/pattern rules for known critical situations | Python | ⬜ |
| `app/safety/patterns.py` | Regex pattern library | Regex | ⬜ |
| `app/safety/classifier.py` | ML classifier for ambiguous-risk language | Transformers | ⬜ |
| `app/safety/risk_scoring.py` | Combines rule + classifier signals into LOW/MEDIUM/HIGH | Python | ⬜ |
| `app/safety/response_routing.py` | Determines the safety-appropriate response path per risk tier | Python | ⬜ |

### 4.8 `app/memory/` (Milestone 8)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/memory/models.py` | SQLAlchemy ORM models: users, conversations, messages, memories, preferences | SQLAlchemy | ⬜ |
| `app/memory/db.py` | DB session/engine setup (SQLite → PostgreSQL-ready) | SQLAlchemy | ⬜ |
| `app/memory/extraction.py` | Extracts memory *candidates* from a conversation turn | Python + LLM | ⬜ |
| `app/memory/importance_scoring.py` | Scores candidates for relevance/importance before storing | Python | ⬜ |
| `app/memory/store.py` | Write path: store approved memories | SQLAlchemy | ⬜ |
| `app/memory/retrieval.py` | Semantic retrieval of relevant memories for current context | Sentence-Transformers + FAISS | ⬜ |
| `app/memory/embeddings.py` | Text → vector embedding utility | Sentence-Transformers | ⬜ |
| `app/memory/index.py` | FAISS index management (build/update/query) | FAISS | ⬜ |

### 4.9 `app/rag/` (Milestone 12)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/rag/chunking.py` | Splits curated documents into retrievable chunks | Python | ⬜ |
| `app/rag/embeddings.py` | Embeds chunks (may reuse `memory/embeddings.py`) | Sentence-Transformers | ⬜ |
| `app/rag/retriever.py` | Similarity search + context selection/injection | FAISS | ⬜ |

### 4.10 `app/social/` (Milestone 10)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/social/relationship_state.py` | Tracks user-Shinzo relationship dynamic over time | Python + Pydantic | ⬜ |
| `app/social/conversation_dynamics.py` | Reads current conversation rhythm/energy | Python | ⬜ |
| `app/social/social_intent.py` | Selects intent: listen / continue topic / ask / observe / tease / joke / change subject / reference moment / check-in / celebrate / give space / say less | Python | ⬜ |
| `app/social/interaction_planner.py` | Turns selected intent into response-planning instructions for the LLM | Python | ⬜ |

### 4.11 `app/human/` (Milestone 11)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/human/shared_context.py` | Injects shared references/callbacks naturally | Python | ⬜ |
| `app/human/spontaneity.py` | Adds contextual randomness (anti-templating) | Python | ⬜ |
| `app/human/humor_context.py` | Determines when humor/teasing is appropriate | Python | ⬜ |
| `app/human/conversation_rhythm.py` | Controls response length/pacing variability | Python | ⬜ |
| `app/human/silence_logic.py` | Decides when brevity/silence is the right response | Python | ⬜ |
| `app/human/authenticity_filter.py` | Final check: robotic / too formal / too therapeutic / repetitive / too long → refine | Python + LLM | ⬜ |

### 4.12 `app/proactive/` (Milestone 13)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/proactive/decision_engine.py` | "Should Shinzo initiate?" — evaluates inactivity, meaningful context, events, opt-in | Python | ⬜ |
| `app/proactive/message_planner.py` | Plans *what* to say if decision = yes | Python + LLM | ⬜ |
| `app/proactive/frequency_guard.py` | Cooldowns, pause mode, reduces pressure if engagement drops | Python | ⬜ |
| `app/proactive/quiet_hours.py` | User-defined do-not-disturb windows | Python | ⬜ |
| `app/proactive/scheduler.py` | Background job scheduling | APScheduler | ⬜ |

### 4.13 `app/language/` (Milestone 10–11 range)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `app/language/detector.py` | Detects primary language / code-switching | `lingua-language-detector` | ⬜ |
| `app/language/style_profile.py` | Builds a per-user `LanguageProfile` (formality, slang, emoji use, rhythm) | Python + Pydantic | ⬜ |
| `app/language/adaptation.py` | Applies profile to generation without forcing style | Python + LLM | ⬜ |

### 4.14 `dataset/` (Milestones 4–5)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `dataset/scripts/normalize.py` | Raw → normalized text | Python + Pandas | ✅ |
| `dataset/scripts/validate.py` | Schema validation of records | Pydantic | ✅ |
| `dataset/scripts/dedupe.py` | Deduplication | Python | ✅ |
| `dataset/scripts/categorize.py` | Tags records into the 11 categories (natural conversation, breakups, loneliness, etc.) | Python | ✅ |
| `dataset/scripts/export_jsonl.py` | Final JSONL export for training | Python | ✅ |
| `dataset/scripts/schema.py` | `DatasetCategory` enum (11 categories) + `TrainingRecord` Pydantic schema shared by all pipeline stages | Pydantic | ✅ |
| `dataset/scripts/pipeline.py` | CLI: runs normalize→validate→dedupe→categorize-report→export in sequence | Python | ✅ |
| `dataset/custom/shinzo_core_v1.jsonl` | ~100 hand-curated high-quality examples across all categories | JSONL | ⬜ |
| `dataset/raw/` | Unprocessed source material (gitignored if sensitive) | — | ⬜ |
| `dataset/processed/` | Output of the pipeline, ready for training | — | ⬜ |

### 4.15 `training/` (Milestone 6)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `training/configs/lora_config.yaml` | LoRA/QLoRA hyperparameters | YAML | ⬜ |
| `training/train.py` | Fine-tuning entry point | TRL + PEFT + Transformers | ⬜ |
| `training/evaluate.py` | Runs the `evaluation/` datasets against a trained adapter | Python | ⬜ |
| `training/inference_test.py` | Manual smoke-test script for a trained adapter | Python | ⬜ |

### 4.16 `evaluation/` (Milestone 7)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `evaluation/relationship.json` | Relationship-support test cases | JSON | ⬜ |
| `evaluation/loneliness.json` | Loneliness-support test cases | JSON | ⬜ |
| `evaluation/naturalness.json` | Naturalness/authenticity test cases | JSON | ⬜ |
| `evaluation/humor.json` | Humor-appropriateness test cases | JSON | ⬜ |
| `evaluation/safety.json` | Safety routing test cases | JSON | ⬜ |
| `evaluation/memory.json` | Memory accuracy/non-hallucination test cases | JSON | ⬜ |
| `evaluation/proactive.json` | Proactive-decision test cases | JSON | ⬜ |

### 4.17 `tests/` (ongoing, every milestone adds to this)

| File | Purpose | Tech | Status |
|---|---|---|---|
| `tests/test_api.py` | API endpoint tests | Pytest + HTTPX | ⬜ |
| `tests/test_memory.py` | Memory extraction/storage/retrieval tests | Pytest | ⬜ |
| `tests/test_emotion.py` | Emotion classifier wiring tests | Pytest | ⬜ |
| `tests/test_safety.py` | Safety rule/classifier/routing tests | Pytest | ⬜ |
| `tests/test_social.py` | Social intent selection tests | Pytest | ⬜ |
| `tests/test_proactive.py` | Frequency guard / decision engine tests | Pytest | ⬜ |
| `tests/test_model.py` | LLM provider interface tests | Pytest + pytest-asyncio | ⬜ |

---

## 5. Recommended Full Directory Tree

```
shinzo-ai/
├── app/
│   ├── api/{routes,middleware,schemas}/
│   ├── core/          (orchestrator, context_builder, decision_router, config, logging)
│   ├── model/         (loader, inference, prompts, provider_base)
│   ├── emotion/
│   ├── safety/
│   ├── memory/
│   ├── rag/
│   ├── social/
│   ├── human/
│   ├── proactive/
│   └── language/
├── dataset/{raw,processed,custom,scripts}/
├── training/{configs,train.py,evaluate.py,inference_test.py}
├── tests/
├── evaluation/
├── docs/
├── requirements.txt
├── .env.example
├── README.md          ← you are here
└── docker-compose.yml
```

---

## 6. Milestone Roadmap & Status

| # | Milestone | Status |
|---|---|---|
| 0 | Product architecture & docs (no code) | ✅ done — all 6 files in `docs/` |
| 1 | FastAPI foundation (skeleton, config, logging, health, pytest, ruff) | ✅ done — `pytest`/`ruff` both clean |
| 2 | Basic chat: swappable LLM provider, end-to-end message→model→response | ✅ done with `MockProvider`; `LocalHFProvider` coded but unvalidated (see limitation note above) |
| 3 | Shinzo personality specification (warmth, curiosity, humor, boundaries, anti-robotic rules) | ✅ done — `docs/PERSONALITY_SPEC.md` + compiled into `app/model/prompts.py` |
| 4 | Dataset pipeline (normalize/validate/dedupe/categorize/export) | ✅ done — `dataset/scripts/*.py`, CLI verified end-to-end |
| 5 | Custom dataset (~100 curated examples) | ⬜ |
| 6 | Fine-tuning (LoRA/QLoRA → Shinzo adapter) | ⬜ |
| 7 | Evaluation (empathy, naturalness, repetition, memory, safety, proactive) | ⬜ |
| 8 | Memory system (extraction, scoring, storage, retrieval) | ⬜ |
| 9 | Emotion engine (pretrained classifier as signal) | ⬜ |
| 10 | Social intelligence (state + intent planning) | ⬜ |
| 11 | Human essence (shared refs, rhythm, spontaneity, brevity, authenticity filter) | ⬜ |
| 12 | RAG (chunking, embeddings, FAISS, context injection) | ⬜ |
| 13 | Proactive engine (decision logic, planning, quiet hours, frequency guard) | ⬜ |
| 14 | Notifications (inbox → browser push) | ⬜ |
| 15 | Full orchestrator (wires all modules together) | ⬜ |
| 16 | Public API (versioned endpoints) | ⬜ |
| 17 | API security (keys, auth middleware, rate limits) | ⬜ |
| 18 | Website integration (secure backend-to-backend) | ⬜ |
| 19 | Full testing (functional, regression, safety, API, memory, proactive) | ⬜ |
| 20 | Deployment (Docker) | ⬜ |

**Rule:** work one milestone at a time — plan → implement one module → write tests → run tests → review → document → move on. Never let generated code outpace what's understood and verified.

---

## 7. How to Resume This Project (read this if you're picking the project back up)

1. **Upload this `README.md`** and the current project ZIP/files to the new session.
2. Check §6 for the current milestone status, and §4 for which specific files are `✅ Done` vs `⬜ Not started` vs `🟨 In progress`.
3. Read any `🟨 In progress` file's existing content first — do not overwrite silently.
4. Continue from the **first non-✅ item**, in the order listed in §4 (sections are already in build order).
5. After finishing a file, update its Status cell in this README (`⬜` → `✅`) in the same turn — this file must always reflect reality.
6. Never skip ahead to a later milestone's module before its dependencies (per §6 order) are at least stubbed and tested.
7. If unsure what a module should do, its behavioral spec is already captured in §4's "Purpose" column and in `docs/` (once created) — don't re-derive it from the original PDFs.

---

## 8. Environment Variables (to be finalized in `.env.example`)

```
SHINZO_ENV=development
DATABASE_URL=sqlite:///./shinzo.db
LLM_PROVIDER=local            # local | hosted
LLM_MODEL_NAME=               # e.g. a Qwen instruct model id
LLM_ADAPTER_PATH=             # path to fine-tuned Shinzo LoRA adapter, once trained
EMOTION_MODEL_NAME=
API_KEY_HASH_ALGO=argon2
RATE_LIMIT_PER_MINUTE=60
PROACTIVE_ENABLED=true
QUIET_HOURS_START=22:00
QUIET_HOURS_END=08:00
```

---

## 10. Current Resume State (as of last update above)

**What exists and is tested:**
- Full `docs/` set including `PERSONALITY_SPEC.md` (Milestones 0 + 3).
- Project scaffolding: `requirements.txt`, `.env.example`, `.gitignore`, `pyproject.toml` (Ruff config).
- `app/core/config.py` (typed settings) + `app/core/logging.py` (no message content ever logged).
- `app/model/provider_base.py` (`LLMProvider` ABC, `MockProvider`, `LocalHFProvider`), `loader.py` (factory), `prompts.py` (**full compiled personality prompt**, matches `docs/PERSONALITY_SPEC.md`), `inference.py` (entry point).
- `app/api/main.py` (FastAPI app w/ lifespan startup), `routes/health.py`, `routes/chat.py`, `schemas/common.py`, `schemas/chat.py`.
- `dataset/scripts/{schema,normalize,validate,dedupe,categorize,export_jsonl,pipeline}.py` — full Milestone 4 pipeline, runnable via `python -m dataset.scripts.pipeline <raw.json> <out.jsonl>`.
- `tests/test_api.py`, `tests/test_model.py`, `tests/test_personality.py`, `tests/test_dataset_pipeline.py` — 16 tests, all passing.

**How to run it:**
```bash
pip install -r requirements.txt   # or just fastapi/uvicorn/pydantic-settings/pytest/ruff/httpx for mock-only dev
cp .env.example .env
uvicorn app.api.main:app --reload
# in another shell:
curl -X POST http://127.0.0.1:8000/v1/chat -H "Content-Type: application/json" \
  -d '{"user_id":"u1","conversation_id":"c1","message":"hey"}'
pytest tests/ -v
ruff check .
```

**What does NOT exist yet (do not assume it does):**
- No orchestrator (`app/core/orchestrator.py` / `context_builder.py` / `decision_router.py`) — the chat route calls `generate_reply()` directly, bypassing safety/emotion/memory/social/human entirely. This is expected at this milestone, not a bug.
- No actual dataset content yet — `dataset/custom/shinzo_core_v1.jsonl` does not exist. The pipeline that will process it is done and tested (Milestone 4), but nobody has authored the ~100 example conversations yet (Milestone 5).
- No fine-tuning run, no memory/DB, no emotion classifier, no safety logic, no social/human/language/RAG/proactive modules, no auth/rate-limiting, no Docker.
- `app/api/routes/proactive.py` and `messages.py` referenced in §4.3 do not exist yet.

**Recommended next step:** Milestone 5 — author `dataset/custom/shinzo_core_v1.jsonl`. Write raw examples as a JSON array (see `/tmp` smoke-test format used during Milestone 4 testing, or `dataset/scripts/schema.py::TrainingRecord` for the exact fields), aiming for coverage across all 11 `DatasetCategory` values, then run `python -m dataset.scripts.pipeline <raw.json> dataset/custom/shinzo_core_v1.jsonl` to validate/dedupe/export. After that, Milestone 6 (fine-tuning) — though note fine-tuning requires real GPU/HF Hub access this sandbox doesn't have (see `docs/MODEL_STRATEGY.md`), so that milestone may need to run elsewhere.

---

## 11. Explicitly Out of Scope for MVP
- Training a foundation model from scratch.
- Hosting a large model continuously from day one.
- Celery/Redis (only if scale later requires distributed background processing).
- Native mobile push (Phase 3, after web push is validated).
- Anything that manufactures dependency, guilt, or exclusivity — this is a hard product constraint, not just a feature deferral.
