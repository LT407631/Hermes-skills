---
name: obsidian
version: 2.1.0
author: Hermes Agent
description: Read, search, create, and edit notes in the Obsidian vault. Supports cross-platform paths (WSL + Windows), research wikis, and operational knowledge bases.
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

**Finding an existing vault (before creating one):** Obsidian stores vault config in `AppData/Roaming/obsidian/obsidian.json`. On Windows: `/mnt/c/Users/<username>/AppData/Roaming/obsidian/obsidian.json`. Check this file first before creating a new vault — the user may already have one configured. The JSON has a `vaults` key mapping vault IDs to objects with a `path` field.

**Cross-platform path bridging (WSL + Windows):** Obsidian vaults on Windows are accessed from WSL via `/mnt/<drive>/`. Common patterns:
- `D:\Documents\Obsidian Vault\` → `/mnt/d/Documents/Obsidian Vault/`
- `C:\Users\<user>\Documents\Obsidian Vault\` → `/mnt/c/Users/<user>/Documents/Obsidian Vault/`
- `C:\ObsidianVault\` → `/mnt/c/ObsidianVault/`

Always resolve the Windows path from obsidian.json or the user, then translate to the `/mnt/` WSL equivalent. Vault paths often contain spaces — use quotes or shell escaping.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH`, checking whether the fallback path exists, or reading `obsidian.json`. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Wiki Structure Patterns

### Research Wiki (LLM Wiki pattern)

For deep research/knowledge domains, use a 3-layer architecture:
```
wiki/
├── SCHEMA.md           # Conventions, structure rules, domain config
├── index.md            # Sectioned content catalog with one-line summaries
├── log.md              # Chronological action log
├── raw/                # Immutable source material (articles, papers)
├── entities/           # Entity pages (people, orgs, products, models)
├── concepts/           # Concept/topic pages
├── comparisons/        # Side-by-side analyses
└── queries/            # Filed query results
```

### Operational Wiki (for content/workflows)

For business operations, marketing content, or workflow-specific knowledge, use a flatter structure organized by workflow stage:
```
vault/
├── _INDEX.md           # Master index (entry point — every note listed)
├── _SCHEMA.md          # Usage conventions
├── _CHANGELOG.md       # Update log
├── raw/                # Source material archive (file inventory + extraction records)
├── 01-core-methodology/
├── 02-sales-playbooks/
├── 03-customer-pain-points/
├── 04-process-SOPs/
├── 05-competitive-intel/
├── 06-content-library/
├── 07-industry-data/
└── 08-daily-notes/
```

Key conventions for operational wikis:
- Numbered folder prefixes (`01-`, `02-`) for sort order
- `_INDEX.md` as the single entry point (replaces `_MOC.md`)
- Every note gets YAML frontmatter: `title`, `created`, `updated`, `type`, `tags`, `sources`
- Every note has 2+ `[[wikilinks]]` cross-references
- `_CHANGELOG.md` tracks all changes
- `raw/_原始资料清单.md` indexes source files with extraction status

### Importing binary documents into the wiki

Company materials (PPTX, XLSX, DOC, PDF) cannot be read directly as text. Extract them via Python, then write structured notes into the appropriate wiki section:

```bash
# One-time install
pip install openpyxl python-pptx python-docx

# PPTX extraction
from pptx import Presentation
prs = Presentation(path)
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                if para.text.strip():
                    print(para.text)

# XLSX extraction
import openpyxl
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
for sheet in wb.sheetnames:
    ws = wb[sheet]
    for row in ws.iter_rows(values_only=True):
        ...

# Old .doc extraction
sudo apt install catdoc
catdoc file.doc
```

After extraction:
1. Write the structured content into the appropriate section as markdown notes
2. Add frontmatter with source reference `sources: [raw/filename.pptx]`
3. Update `raw/_原始资料清单.md` to mark the file as extracted
4. Cross-reference the new notes with existing pages

## 会话自动归档

当需要自动将微信对话归档到 Obsidian 时，参考 `references/session-archive-workflow.md`：
- Gateway Event Hooks（agent:end 事件触发）— 全自动
- Python 手动脚本 — 可控
