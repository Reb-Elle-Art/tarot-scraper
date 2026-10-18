# Tarot RAG Bot — Project Plan

## Overview

Building a dedicated tarot RAG (Retrieval Augmented Generation) bot on Telegram. The bot answers natural language questions about tarot by retrieving relevant card passages from a local corpus and synthesizing answers with a local model pipeline.

**Interface:** Telegram bot (lean, minimal)
**Models (all local, OpenAI-compatible endpoints):**
- Embedding: Owen-3.8
- Reranker: Quen-3.8
- Generation: Gemma-4-26b-a4b

---

## Current Status

**Phase 1 (Chunking + Tagging):** COMPLETE.

All 78 card tag files generated and saved to `tags/*.json`. Each tag file includes:
- `astrological` — planet or zodiac sign (from astrological-correspondences.json), null for aces
- `themes` — up to 8 themes extracted from card text
- `keywords` — 15 keywords from card text
- `symbols` — up to 10 symbols detected from card text
- `brief_summary` — one sentence from the upright section

Awaiting Elle's review/edit pass before Phase 2.

**Astrological correspondences:** Compiled from 7 sources (Golden Dawn tradition), saved to `tags/astrological-correspondences.json` and `.md`.

---

## Architecture

```
User message (Telegram)
    ↓
Intent detection (keyword matching)
    ↓
Template selection
    ↓
Embedding (Owen-3.8) → Chroma search
    ↓
Reranking (Quen-3.8) → top candidates
    ↓
Generation (Gemma-4-26b-a4b) → response
    ↓
Telegram reply
```

---

## Intent Templates

### 1. thematic_search
**Triggers:** "what cards touch on", "cards about", "cards dealing with", "completion", "endings", etc.
**Behavior:** Semantic search across all card sections, returns top 5 cards with relevance explanation.
**Default position:** Upright (unless reversed is specified)
**Sections prioritized:** Upright, Deeper Meaning

### 2. card_lookup
**Triggers:** "tell me about [card]", "what does [card] mean", "[card] tarot"
**Behavior:** Direct card retrieval, returns full card content.
**Position handling:** Default upright; "reversed" or "inverted" triggers reversed section.

### 3. random_draw
**Triggers:** "draw a card", "give me a card", "random card"
**Behavior:** Random selection from 78 cards, returns full card content.

### 4. spread (simplified v1)
**Triggers:** "give me a reading", "do a reading", "6 card spread"
**Behavior:** Draws 6 cards, assigned to:
- Past (2 cards)
- Present (2 cards)
- Future (2 cards)
Returns each card with position context.

**Celtic Cross / complex spreads:** Deferred to later version.

---

## Data Structure

### Repo Location
```
/home/enid/.openclaw/workspace/projects/tarot-scraper/
https://github.com/Reb-Elle-Art/tarot-scraper
```

### Source Files
Canonical source: `cards/major/`, `cards/minor/`, `cards/court/` (78 cards total)

```
cards/
├── major/    # 22 cards — Death.txt, Fool.txt, etc.
├── minor/    # 40 cards — ace-of-cups.txt through ten-of-wands.txt
└── court/   # 16 cards — king-of-cups.txt through page-of-wands.txt
```

### Card File Format (.txt with YAML frontmatter)
```yaml
---
card_id: "death"
card_name: "Death"
card_type: "major"
card_number: "13"
source_url: "https://www.aeclectic.net/tarot/tarot-card-meanings/major-arcana/death.shtml"
date_scraped: "2026-10-17"
---

**Symbols:**
[raw text]

**Story:**
[raw text]

**Upright Meaning:**
[raw text]

**Deeper Meaning:**
[raw text]

**Reversed:**
[raw text]

**in Love:**
[raw text]
```

### Generated Tags (per card — stored in tags/)
```yaml
themes: [array of strings]    # e.g. ["endings", "transformation", "cycles"]
keywords: [array of strings]  # e.g. ["death", "ending", "rebirth"]
symbols: [array of strings]   # e.g. ["skeleton", "white horse", "scythe"]
astrological: string | null   # e.g. "Scorpio", "Mars", "Cancer" (planet or zodiac sign)
```

**Astrological field:** Optional. When provided, either a zodiac sign (e.g. "Scorpio") or planet (e.g. "Mars"). If a card has no astrological association, leave as `null`. Elle will provide the correspondence list.

---

## Chunking Strategy

**Decision:** One chunk per named section per card.

Rationale: Fine-grained retrieval. If user asks about "completion," you get the specific section that addresses it rather than the whole card. Tags apply at chunk level.

Example — Death card becomes multiple chunks:
- Chunk 1: Symbols section + metadata
- Chunk 2: Story section + metadata
- Chunk 3: Upright Meaning + metadata
- Chunk 4: Deeper Meaning + metadata
- Chunk 5: Reversed section + metadata
- Chunk 6: in Love section + metadata

---

## Phases

### Phase 1 — Chunking + Tagging
- [x] Add astrological tag field to card schema
- [x] Receive and compile astrological correspondence list (researched via Tavily, 7 sources)
- [x] Generate themes/keywords/symbols for all 78 cards
- [x] Merge astrological tags into all 78 tag files
- [ ] Review/edit pass (Elle reviews output — keyword quality, brief_summary coherence)
- [x] Finalize tag files in tags/ directory

### Phase 2 — Index Build
- [ ] Parse all 78 cards, chunk by section
- [ ] Attach metadata + generated tags
- [ ] Embed with Owen-3.8
- [ ] Store in Chroma (file-based)
- [ ] Index reranker (Quen-3.8)

### Phase 3 — Bot Build
- [ ] Intent template system (4 templates)
- [ ] Retrieval pipeline (embed → search → rerank → generate)
- [ ] Telegram bot interface
- [ ] System prompt: domain rules only (no tarot reader persona), default upright

### Phase 4 — Test + Tune
- [ ] Run queries, fix retrieval issues
- [ ] Tune reranking thresholds
- [ ] User testing

---

## Project Structure

```
tarot-scraper/               # Repo root
├── cards/
│   ├── major/              # 22 .txt files
│   ├── minor/              # 40 .txt files
│   └── court/             # 16 .txt files
├── tags/                   # Tag files (78 .json + index.json)
│   ├── astrological-correspondences.json   # Astrological lookup (all 78)
│   ├── astrological-correspondences.md     # Human-readable reference
│   ├── index.json                           # Master index
│   └── [card_id].json     # One per card (78 files)
├── scripts/
│   └── generate_tags.py   # Re-run to regenerate all tag files
├── archive/                # Old/scraped versions
├── venv/                   # Python virtualenv
├── scrape.py               # Full scrape script
├── RAG-BOT-PLAN.md         # This file
└── README.md
```

**Out of scope for repo:** chroma_db/, src/, requirements.txt — these will be added in Phase 2-3 when the actual bot is built.

---

## Out of Scope (v1)
- Complex spreads (Celtic Cross, etc.)
- Tarot reader persona
- Multi-card comparison queries
- Reading history / persistence
- Image generation for cards

---

## Waiting On
- Elle's review/edit pass on Phase 1 tag output (keyword quality, brief_summary coherence)

---

_Last updated: 2026-10-18_
