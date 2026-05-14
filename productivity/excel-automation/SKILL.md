---
title: Excel Automation (openpyxl)
name: excel-automation
description: Read, write, style, and format .xlsx files with openpyxl — conditional formatting, formulas, data insertion, sheet management, and cross-sheet parameter-driven rules. Also provides guidance on when Excel is the wrong tool.
domain: productivity
tags:
  - excel
  - openpyxl
  - conditional-formatting
  - spreadsheet
  - data-entry
  - progress-tracking
  - project-management
triggers:
  - User asks to edit/create/modify/format an Excel file (.xlsx)
  - User wants conditional formatting, color-coded cells, data validation
  - User has a spreadsheet they need automated manipulation of
  - Project tracking, progress tables, scheduling sheets, Kanban tables
  - User asks about multi-role data entry / mobile form submission
related_skills:
  - short-video-b2b-acquisition
  - obsidian
---
# Excel Automation (openpyxl)

## Overview

Create, read, edit, and format `.xlsx` files using Python's `openpyxl` library. Covers:
- Reading sheet structure and data
- Adding/editing data rows
- Conditional formatting (color rules based on formulas)
- Cross-sheet parameter-driven conditional formatting (user-adjustable thresholds)
- Styling (headers, borders, alignment, fonts)
- Column widths and row heights
- Number formats (dates, currency)

## Prerequisites

- `openpyxl` must be installed in the active Python environment
- File path translation: Windows paths `C:\Users\...` → WSL paths `/mnt/c/Users/...`
- File must be **closed** in Excel before openpyxl can write to it

## Common Workflow

### 1. Load and Inspect the File

```python
import openpyxl
wb = openpyxl.load_workbook(path)
print('Sheet names:', wb.sheetnames)
for name in wb.sheetnames:
    ws = wb[name]
    print(f'Sheet "{name}": {ws.max_row} rows, {ws.max_column} cols')
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 5), values_only=True):
        print(row)
```

### 2. Style Headers

```python
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

for col in range(1, ws.max_column + 1):
    cell = ws.cell(row=1, column=col)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_align
    cell.border = thin_border
```

### 3. Add Data Rows

```python
from datetime import datetime

data = ['XD-2026-001', '张三', '天工全屋定制', datetime(2026, 5, 10), 58000, 86]
for col_idx, val in enumerate(data, 1):
    cell = ws.cell(row=2, column=col_idx, value=val)
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center', vertical='center')
    if isinstance(val, datetime):
        cell.number_format = 'YYYY-MM-DD'
    elif isinstance(val, (int, float)):
        cell.number_format = '#,##0'
```

### 4. Set Column Widths

```python
col_widths = {1:12, 2:12, 3:18, 4:24, 5:10}
for col, width in col_widths.items():
    ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width
```

### 5. Create a Parameter Adjustment Sheet

For project tracking tables, create a dedicated sheet so the user can adjust thresholds without editing formulas:

```python
ws_param = wb.create_sheet('参数调节', 0)  # Insert at front

# Headers: 环节 | 黄天数 | 红天数 | 说明
params = [
    ('报价时间', 1, 2, '从接单日算起'),
    ('回款时间', 1, 2, '从报价日算起'),
    ('图纸时间', 3, 4, '从接单日算起'),
    ('拆单完成', 7, 8, ''),
    ('入库完成', 15, 16, ''),
]
for row_idx, (name, yd, rd, note) in enumerate(params, 3):
    ws_param.cell(row=row_idx, column=1, value=name).border = tb
    ws_param.cell(row=row_idx, column=2, value=yd).border = tb
    ws_param.cell(row=row_idx, column=3, value=rd).border = tb
    ws_param.cell(row=row_idx, column=4, value=note).border = tb
```

### 6. Cross-Sheet Conditional Formatting (Parameter-Driven)

Clear old rules, then add new ones referencing the parameter sheet:

```python
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.formatting.rule import FormulaRule

ws.conditional_formatting = ConditionalFormattingList()

yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
red_fill = PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')

col_to_param_row = {
    'H': 3,  # 报价时间 → 参数调节!B3
    'I': 4,  # 回款时间 → 参数调节!B4
    'K': 6,  # 图纸时间 → 参数调节!B6
    'O': 10, # 入库完成 → 参数调节!B10
}

for col_letter, param_row in col_to_param_row.items():
    # Yellow: cell empty AND elapsed >= parameter sheet yellow day
    ws.conditional_formatting.add(
        f'{col_letter}2:{col_letter}1000',
        FormulaRule(formula=[
            f'AND({col_letter}2="",TODAY()-$G2>=参数调节!$B${param_row})'
        ], fill=yellow_fill)
    )
    # Red: cell empty AND elapsed >= parameter sheet red day
    ws.conditional_formatting.add(
        f'{col_letter}2:{col_letter}1000',
        FormulaRule(formula=[
            f'AND({col_letter}2="",TODAY()-$G2>=参数调节!$C${param_row})'
        ], fill=red_fill)
    )
```

**Formula syntax for cross-sheet references in conditional formatting:**
- `参数调节!$B$3` — absolute reference to parameter sheet
- `$G2` — absolute column (baseline date in progress table), relative row
- Formula is written for the **top-left cell** of the range; Excel adjusts per row

**User workflow:** Open file → Go to 参数调节 sheet → Change number → Save → Rules auto-update.

### 7. Save

```python
wb.save(path)
```

## When NOT to Use Excel

Excel cannot produce **immutable timestamps**. `TODAY()` and `NOW()` recalculate every time the file opens, so you can't auto-record "when did this status change happen."

For multi-role mobile form submission + auto timestamps, recommend these alternatives:

| Scenario | Tool | Why |
|----------|------|-----|
| 微信内轻量提交, 0安装 | **腾讯文档收集表** | 微信直接填, 数据汇总到表 |
| 分角色权限 + 自动化规则 | **飞书多维表格** | 表单视图, 自动记录时间, 免费 |
| 企业级流程管理 | **钉钉宜搭 / 简道云** | 完整审批流转, 超期自动提醒 |

**When to pivot:** User says "多个员工手机填表" + "自动记录时间" → Excel can't do it. Recommend immediately.

## Pitfalls & Gotchas

- **File must be closed** in Excel before openpyxl can write.
- **Windows → WSL path**: `C:\\Users\\...` → `/mnt/c/Users/...`
- **Conditional formatting order**: Add red AFTER yellow so red visually overrides.
- **Clearing old rules**: `ws.conditional_formatting = ConditionalFormattingList()` — the class must be imported from `openpyxl.formatting.formatting`, NOT `openpyxl.formatting`.
- **ConditionalFormattingList import**: Correct path is `from openpyxl.formatting.formatting import ConditionalFormattingList`.
- **Rule count vs actual rules**: `len(ws.conditional_formatting)` counts rule **groups**, each group may contain multiple individual rules.
- **`TODAY()` is volatile**: It recalculates every open. Use only for live warnings, NEVER for immutable audit logs.
- **Chinese fonts**: Use `'微软雅黑'` (Microsoft YaHei) for readability.
- **Number formats**: Use `'#,##0'` for amounts, `'YYYY-MM-DD'` for dates.
- **Style copying raises StyleProxy error**: `cell.font = other_cell.font` or `cell.fill = other_cell.fill` raises `TypeError: unhashable type: 'StyleProxy'`. **Never copy style objects directly.** Instead: write the value, then reapply styles from scratch using fresh PatternFill/Font/Border objects.
- **Merged cells are read-only on value assignment**: A `MergedCell` object raises `AttributeError: 'MergedCell' object attribute 'value' is read-only` when you try to set `.value = None`. **Fix:** Iterate `ws.merged_cells.ranges` first, call `ws.unmerge_cells(str(merge_range))` for any ranges you need to clear, then clear values.
- **No direct column insert in openpyxl**: There is no `ws.insert_cols()` that preserves existing data formatting across a large file. Workaround: read values from target columns, write them to new (shifted) columns, then clear old columns and write new data in between.
- **Cross-sheet CF with skip-when-zero**: To make a parameter sheet support "no warning" (set to 0), add an extra condition to the formula: `参数调节!$B${param_row}>0`. Otherwise setting the parameter to 0 would match every cell (since `TODAY()-$G2>=0` is always true).
- **Reference parameter cells with sheet name in CF formulas**: Use `参数调节!$B$3` format (absolute column/row). The sheet name must be the actual sheet name in Chinese.

## Verification

```python
wb = openpyxl.load_workbook(path)
ws = wb['SheetName']
print(f'Rules: {len(ws.conditional_formatting)}')
for cf in ws.conditional_formatting:
    print(f'Range: {cf.sqref}')
    for rule in cf.rules:
        print(f'  Formula: {rule.formula}')
```

## Related Files

- `references/openpyxl-conditional-formatting.md` — detailed API patterns, cross-sheet reference syntax, color priority
- `references/project-tracking-ktzm-factory.md` — full design reference for 全屋定制工厂 project progress tracking tables: 16-step process flow, role assignments, 21-column table layout, CF parameter patterns, and multi-role form solution comparison checklist
- `templates/project-progress-params-template.py` — starter script for creating a project progress table with parameter-driven conditional formatting
