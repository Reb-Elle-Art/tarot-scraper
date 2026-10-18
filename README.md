# Tarot Card Scraper

Scrapes tarot card meanings from aeclectic.net and outputs one .txt file per card with YAML frontmatter.

## Setup

```bash
pip install requests beautifulsoup4
```

## Usage

Scrape all 78 cards:
```bash
python scrape.py
```

Scrape a single card:
```bash
python scrape.py --card king-of-cups
```

## Output

Each card is saved as `{card_id}.txt` in the `cards/` directory:

```
cards/
├── 00-the-fool.txt
├── 01-the-magician.txt
├── ...
├── ace-of-cups.txt
├── king-of-cups.txt
└── ...
```

File format:
```
---
card_id: "king-of-cups"
card_name: "King of Cups"
card_type: "court"
suit: "cups"
keywords: "Emotional maturity. A mature, determined and committed love."
source_url: "https://www.aeclectic.net/tarot/tarot-card-meanings/court-cards/king-of-cups.shtml"
date_scraped: "2026-10-17"
---

**Upright:** [raw text]

**Reversed:** [raw text]
```

## Cards Included

- Major Arcana: 22 cards (00 The Fool - 21 The World)
- Minor Arcana: 40 cards (Ace - Ten, each suit)
- Court Cards: 16 cards (King, Queen, Knight, Page, each suit)

Total: 78 cards
