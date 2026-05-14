---
name: sketch
description: "Throwaway HTML mockups: 2-3 design variants to compare."
version: 1.0.0
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
metadata:
  hermes:
    tags: [sketch, mockup, design, ui, prototype, html, variants, exploration, wireframe, comparison]
    related_skills: [spike, claude-design, popular-web-designs, excalidraw]
---

# Sketch

Use this skill when the user wants to **see a design direction before committing** to one — exploring a UI/UX idea as disposable HTML mockups. The point is to generate 2-3 interactive variants so the user can compare visual directions side-by-side, not to produce shippable code.

Load this when the user says things like "sketch this screen", "show me what X could look like", "compare layout A vs B", "give me 2-3 takes on this UI", "let me see some variants", "mockup this before I build".

## When NOT to use this

- User wants a production component — use `claude-design` or build it properly
- User wants a polished one-off HTML artifact (landing page, deck) — `claude-design`
- User wants a diagram — `excalidraw`, `architecture-diagram`
- The design is already locked — just build it

## Alternative: Business proposal / requirements documentation HTML pages

When the user wants a **single comprehensive informational/documentation HTML page** (not mockup variants):

- **Business requirement docs** — comparing solutions (e.g. Feishu vs Mini-program), cost analysis, feature breakdowns
- **Project proposals** — multi-section pages with sidebar navigation, timelines, pricing cards
- **Internal knowledge base pages** — reference documentation for team processes

Use `templates/business-proposal.html` as a starter — it provides:

- **Left sidebar nav** with section links (fixed, scrollable)
- **Multiple page sections** navigated via JS hash routing
- **Comparison tables** with `.compare-table` styling
- **Price/cost cards** with `.price-row` + `.price-card` structure
- **Feature grids** with `.feature-grid` + `.feature-item`
- **Timeline visualization** with `.timeline` component
- **Status tags/badges** (`.tag-green`, `.tag-yellow`, `.tag-red`, `.badge-blue`, etc.)
- **Responsive breakpoint** at 768px

### Chinese B2B business user UI preferences (腾哥)

When iterating on a Chinese business proposal page, embed these defaults **from the first version** — they were repeatedly corrected:

**Typography:**
- Font family: `"Microsoft YaHei", "PingFang SC", "Helvetica Neue", sans-serif` — **ONLY** these, NO Lato/Inter/English-first font stacks
- Body font-size: **17px** minimum, with line-height: **2** (very generous leading)
- Card headings: **22px**, page titles: **30px**, card body text: **16px**
- Table text: **15px**, sidebar nav: **15px**
- Tags/badges: **13px** — these are the only small elements permissible
- The user will complain if text feels "小" (small) — when in doubt, go bigger

**Layout & visual style (Theme-Next Gemini style):**
- Body background: `#f5f5f5` (light gray)
- Card background: `#fff` (pure white)
- Cards have **NO border-radius** (0px) — flat corners are the Gemini aesthetic
- Cards have subtle `box-shadow: 0 1px 3px rgba(0,0,0,0.04)`
- Left sidebar: dark background `#222` / `#2c3e50`, white text
- Section dividers in sidebar: thin, low-opacity lines
- **Dark/light mode** via CSS custom properties + class toggle on `<body>`
- Theme toggle: always include (user expects it, even if they rarely use it)

**Navigation structure:**
- Left sidebar with group labels (e.g. "飞书多维表格方案" / "微信小程序方案")
- Sub-items indented under group labels (e.g. "方案总览" → "功能详解与操作")
- Active page indicator: left border color highlight on `.active` link
- Sidebar navigation items: click triggers JS function that shows/hides page sections

**Information components:**
- **Comparison tables**: dark header row (same color as sidebar), clean white rows, no border-radius
- **Process flows**: icon-card layout (emoji icons at 28px + text labels at 14px in flex rows, with arrow separators), NOT text tag chains
- **Feature grids**: 2-column grid, gray background on items, icon+title+description
- **Phone mockups**: 9:16 portrait aspect ratio (NOT landscape), with status bar, navbar at bottom, mock real app content
- **Step lists**: numbered circles (blue) with descriptive text, generous line-height
- **Price cards**: side-by-side cards with featured variant highlighted with accent border

**Copy conventions:**
- Compare "找公司/个人开发者" vs "腾哥+AI助手" with ¥0 development cost emphasis
- Use "✅ 可实现" / "❌ 无法实现" split columns
- Keep copy professional but conversational — this is a business proposal, not a marketing page

When iterating on such a page:

1. Ship version 1 as a complete HTML file first
2. If the user says the design is "不美观" (not beautiful enough), **do NOT try to guess a new style**. Instead, search for blog/site design references the user can click on (Chinese sites load fast for Chinese users):
   - Chinese personal blogs: `blog.zhheo.com`, `theme-next.js.org`
   - Chinese template galleries: `bootstrapmb.com/muban/geren`
   - Use `web_search(query="...")` with Chinese search terms to find demo URLs
3. Let the user pick a visual direction, then rebuild the page matching that style
4. **Critical**: When the user says a design is not good enough, ASK for a reference rather than guessing. The first version should already follow the Chinese B2B preferences above.

**⚠️ CDP pitfall**: CDP-based browser tools (like `agent-browser`) may not be available. In that case, use `web_search` to find reference URLs and give them to the user to open themselves. Do NOT try to extract/screenshot template sites without a working browser.

## If the user has the full GSD system installed

If `gsd-sketch` shows up as a sibling skill (installed via `npx get-shit-done-cc --hermes`), prefer **`gsd-sketch`** for the full workflow: persistent `.planning/sketches/` with MANIFEST, frontier mode analysis, consistency audits across past sketches, and integration with the rest of GSD. This skill is the lightweight standalone version — one-off sketching without the state machinery.

## Core method

```
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

### 1. Intake (skip if the user already gave you enough)

Before generating variants, get three things — one question at a time, not all at once:

1. **Feel.** "What should this feel like? Adjectives, emotions, a vibe." — *"calm, editorial, like Linear"* tells you more than *"minimal"*.
2. **References.** "What apps, sites, or products capture the feel you're imagining?" — actual references beat abstract descriptions.
3. **Core action.** "What's the single most important thing a user does on this screen?" — the variants should all serve this well; if they don't, they're just decoration.

Reflect each answer briefly before the next question. If the user already gave you all three upfront, skip straight to variants.

### 2. Variants (2-3, never 1, rarely 4+)

Produce **2-3 variants** in one go. Each variant is a complete, standalone HTML file. Don't describe variants — build them. The point is comparison.

Each variant should take a **different design stance**, not different pixel values. Three good variant axes:

- **Density:** compact / airy / ultra-dense (pick two contrasting poles)
- **Emphasis:** content-first / action-first / tool-first
- **Aesthetic:** editorial / utilitarian / playful
- **Layout:** single-column / sidebar / split-pane
- **Grounding:** card-based / bare-content / document-style

Pick one axis and pull apart from it. Two variants that differ only in accent color are wasted effort — the user can't distinguish them.

**Variant naming:** describe the stance, not the number.

```
sketches/
├── 001-calm-editorial/
│   ├── index.html
│   └── README.md
├── 001-utilitarian-dense/
│   ├── index.html
│   └── README.md
└── 001-playful-split/
    ├── index.html
    └── README.md
```

### 3. Make them real HTML

Each variant is a **single self-contained HTML file**:

- Inline `<style>` — no build step, no external CSS
- System fonts or one Google Font via `<link>`
- Tailwind via CDN (`<script src="https://cdn.tailwindcss.com"></script>`) is fine
- Realistic fake content — actual sentences, actual names, not "Lorem ipsum"
- **Interactive**: links clickable, hovers real, at least one state transition (open/close, filter, toggle). A frozen static image is a worse spike than a sloppy animated one.

Open it in a browser. If it looks broken, fix it before showing the user.

**Verify variants visually — use Hermes' browser tools.** Don't just write HTML and hope it renders; load each variant and look at it:

```
browser_navigate(url="file:///absolute/path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean and readable? Any visible bugs (overlapping text, unstyled elements, broken images)?")
```

`browser_vision` returns an AI description of what's actually on the page plus a screenshot path — catches layout bugs that pure source inspection misses (e.g. a font import that silently failed, a flex container that collapsed). Fix and re-navigate until each variant looks right.

**Default CSS reset + system font stack** for fast starts:

```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: #1a1a1a;
    background: #fafafa;
    line-height: 1.5;
  }
</style>
```

### 4. Variant README

Each variant's `README.md` answers:

```markdown
## Variant: {stance name}

### Design stance
One sentence on the principle driving this variant.

### Key choices
- Layout: ...
- Typography: ...
- Color: ...
- Interaction: ...

### Trade-offs
- Strong at: ...
- Weak at: ...

### Best for
- The kind of user or use case this variant actually serves
```

### 5. Head-to-head

After all variants are built, present them as a comparison. Don't just list — **opinionate**:

```markdown
## Three takes on the home screen

| Dimension | Calm editorial | Utilitarian dense | Playful split |
|-----------|----------------|-------------------|---------------|
| Density   | Low            | High              | Medium        |
| Primary action visibility | Low | High | Medium |
| Scan-ability | High | Medium | Low |
| Feel | Calm, trusted | Sharp, tool-like | Inviting, energetic |

**My take:** Utilitarian dense for power users, calm editorial for content-forward audiences. Playful split is weakest — tries to do both and commits to neither.
```

Let the user pick a winner, or combine two into a hybrid, or ask for another round.

## Theming (when the project has a visual identity)

If the user has an existing theme (colors, fonts, tokens), put shared tokens in `sketches/themes/tokens.css` and `@import` them in each variant. Keep tokens minimal:

```css
/* sketches/themes/tokens.css */
:root {
  --color-bg: #fafafa;
  --color-fg: #1a1a1a;
  --color-accent: #0066ff;
  --color-muted: #666;
  --radius: 8px;
  --font-display: "Inter", sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, sans-serif;
}
```

Don't over-tokenize a throwaway sketch — three colors and one font is usually enough.

## Interactivity bar

A sketch is interactive enough when the user can:

1. **Click a primary action** and something visible happens (state change, modal, toast, navigation feint)
2. **See one meaningful state transition** (filter a list, toggle a mode, open/close a panel)
3. **Hover recognizable affordances** (buttons, rows, tabs)

More than that is over-engineering a throwaway. Less than that is a screenshot.

## Frontier mode (picking what to sketch next)

If sketches already exist and the user says "what should I sketch next?":

- **Consistency gaps** — two winning variants from different sketches made independent choices that haven't been composed together yet
- **Unsketched screens** — referenced but never explored
- **State coverage** — happy path sketched, but not empty / loading / error / 1000-items
- **Responsive gaps** — validated at one viewport; does it hold at mobile / ultrawide?
- **Interaction patterns** — static layouts exist; transitions, drag, scroll behavior don't

Propose 2-4 named candidates. Let the user pick.

## Output

- Create `sketches/` (or `.planning/sketches/` if the user is using GSD conventions) in the repo root
- One subdir per variant: `NNN-stance-name/index.html` + `README.md`
- Tell the user how to open them: `open sketches/001-calm-editorial/index.html` on macOS, `xdg-open` on Linux, `start` on Windows
- Keep variants disposable — a sketch that you felt the need to preserve should be promoted into real project code, not curated as an asset

**Typical tool sequence for one variant:**

```
terminal("mkdir -p sketches/001-calm-editorial")
write_file("sketches/001-calm-editorial/index.html", "<!doctype html>...")
write_file("sketches/001-calm-editorial/README.md", "## Variant: Calm editorial\n...")
browser_navigate(url="file://$(pwd)/sketches/001-calm-editorial/index.html")
browser_vision(question="How does this look? Any obvious layout issues?")
```

Repeat for each variant, then present the comparison table.

## Attribution

Adapted from the GSD (Get Shit Done) project's `/gsd-sketch` workflow — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). The full GSD system ships persistent sketch state, theme/variant pattern references, and consistency-audit workflows; install with `npx get-shit-done-cc --hermes --global`.
