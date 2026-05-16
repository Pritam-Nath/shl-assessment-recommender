# Approach

This solution implements a stateless FastAPI service for conversational SHL assessment recommendation. The service accepts the full message history on every `POST /chat` call and stores no per-user state. `GET /health` returns `{"status":"ok"}`.

## Catalog and Retrieval

The scraper downloads the SHL product catalog with `type=1`, which corresponds to Individual Test Solutions, and ignores Pre-packaged Job Solutions. It caches assessment names, catalog URLs, test type letters, remote/adaptive flags, descriptions, job levels, languages, and durations in `data/shl_catalog.json`.

The agent uses deterministic retrieval rather than relying on an external LLM at runtime. Each catalog entry is converted into a searchable document from name, description, job levels, language, and test types. User history is tokenized, expanded with skill synonyms, and scored with a lightweight TF-IDF-style ranker plus domain boosts for exact assessment names, requested test types, seniority, stakeholder/communication needs, and common technical skills.

## Conversation Design

The agent has four main paths:

1. Clarify vague requests such as "I need an assessment" before recommending.
2. Recommend 1 to 10 catalog assessments when the role or skill context is sufficient.
3. Refine naturally because each request re-reads the full conversation history, including changed constraints like "add personality tests".
4. Compare assessments by matching names to catalog records and answering only from cached catalog fields.

The agent refuses off-topic hiring, legal, compensation, and prompt-injection requests. All returned recommendation URLs come directly from the scraped SHL catalog.

## Evaluation

I included focused tests for schema-safe behavior: clarification, catalog-only recommendations, and off-topic refusal. For further iteration, I would add the public conversation traces, calculate Recall@10 for each final shortlist, inspect misses, and tune synonym expansion and ranking boosts. A deterministic baseline is useful because it is low-latency, cheap to deploy, and easier to defend in a technical interview.

## AI Usage

AI assistance was used to scaffold the FastAPI service, scraper, deterministic ranking logic, and this approach document. The design intentionally keeps runtime behavior explainable and independent of paid model availability.
