# inspiration_pages — что нового в БД

**Добавлено:** 2026-04-27. Миграция `006_inspiration_pages.sql`. 405 строк (из 548 проанализированных JSON; 143 пропущены валидатором — список в `extracted/_FAILED_TO_FIX.md`, гитайгноред).

Источник: скриншоты с land-book, проанализированы агентами по спеке `PAGE_ANALYSIS_PROMPT.md`. Одна страница = одна строка.

## Покрытие (405 строк)

| page_type | rows |
|---|---:|
| marketing_landing | 73 |
| about | 44 |
| portfolio | 43 |
| product_listing | 38 |
| careers | 37 |
| ecommerce_home | 35 |
| blog_post | 35 |
| signup | 34 |
| blog_index | 23 |
| pricing | 23 |
| product_page | 20 |

**appearance:** light 266 / mixed 93 / dark 46. **378 уникальных** `style_family`, **194 уникальные** `industry`.

## Формат строки

```
id                  TEXT PK         "page_<slug>"
source              TEXT            "land-book"
url_guess           TEXT            nullable
captured_at         DATE
screenshot_path     TEXT            "images/<cat>/<file>.jpg" (локально, gitignored)

-- классификация (плоско, фильтруемо)
page_type           TEXT            vocab §2.1
landing_pattern_id  TEXT            soft-ref, не FK (87 ad-hoc IDs vs 34 канонических)
style_family        TEXT
industry            TEXT
product_category    TEXT
audience            TEXT
appearance          TEXT            light|dark|mixed
density             TEXT            compact|comfortable|spacious

-- тег-массивы (GIN-индексы → @> фильтры)
mood                     TEXT[]     §2.8 moods (2-6)
visual_signatures        TEXT[]     §2.3 signatures
keywords                 TEXT[]     8-20
good_for_product_types   TEXT[]     §2.8 product_types (2-6)
good_for_moods           TEXT[]     §2.8 moods (2-6)
good_for_stages          TEXT[]     §2.8 stages (1-5)
section_order            TEXT[]     §2.4 section types в порядке

-- структурированное (JSONB)
palette                JSONB        {role_intent: {primary_accent: "#...", ink: "#..."}, palette_strategy, contrast_character, notes}
typography             JSONB        heading/body family character + open-source equivalents + treatments + eyebrow_pattern
primary_cta            JSONB        {label_example, placements[], style} | null
sections               JSONB        упорядоченный массив секций (см. §3 спеки)
inspiration_metadata   JSONB        зеркало TEXT[]-тегов + standout_qualities + not_recommended_for
reference_for          JSONB        {styles[], domains[], moods[]}
effects                JSONB
interaction_cues       JSONB
generation_constraints JSONB        {hard_rules, soft_guidance} | null

-- proza (для людей)
description            TEXT         2-4 предложения, нейтральное описание
why_it_works           TEXT         2-4 предложения, UX-инсайт
generation_prompt      TEXT         обязательно для page_type ∈ (marketing_landing, signup); опционально для остальных
use_when               TEXT         1-3 предложения "ситуационного выбора" — когда брать именно эту референс-страницу (мигр. 007)
notes                  TEXT
created_at             TIMESTAMPTZ
```

## Констрейнты

- `page_type` — CHECK по 11 значениям из §2.1
- `appearance` — CHECK light/dark/mixed
- `density` — CHECK compact/comfortable/spacious (или null)
- **landing_pattern_consistency:** `landing_pattern_id` non-null IFF `page_type='marketing_landing'`
- **generation_constraints_consistency:** `generation_constraints` non-null IFF `page_type ∈ (marketing_landing, signup)` (мигр. 007 — заменила generation_consistency)
- **generation_prompt_required_for_landing_signup:** `generation_prompt` non-null для `page_type ∈ (marketing_landing, signup)`. Для остальных — допустимо, но не обязательно (мигр. 007).
- `mood` 2-6, `keywords` 8-20, `good_for_moods` 2-6, `good_for_product_types` 2-6, `good_for_stages` 1-5

## Индексы

- B-tree: `page_type`, `landing_pattern_id`, `appearance`, `style_family`, `industry`, `product_category`, `density`
- GIN на всех TEXT[]: `mood`, `visual_signatures`, `keywords`, `good_for_product_types`, `good_for_moods`, `good_for_stages`, `section_order`

## RLS

`public_read` для anon + authenticated. Запись только через service_role key.

## Ингест

Идемпотентный upsert по `id`:
```bash
python scripts/ingest_inspiration_pages.py [--dry-run] [--strict]
```
Перед заливкой каждый JSON прогоняется через `validate_extracted.py`; failing skip-аются.

## TODO

- 143 файла не прошли валидацию (vocab drift в исторических данных) — починить пачкой агентов по `extracted/_FAILED_TO_FIX.md`
- MCP-тулзы: `list_inspiration_pages` (фильтры по page_type/mood/style_family/keyword), `get_inspiration_page(id)`, `list_inspiration_page_facets`
- Скриншоты сейчас локальные (gitignored) — позже в Supabase Storage с публичными URL
- 2 битые картинки: `landing/joby-aviation-...4c4a6dd5.jpg`, `portfolio/out-of-the-valley-...affinity.jpg` — перекачать
