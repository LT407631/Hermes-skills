# openpyxl Conditional Formatting Patterns

## FormulaRule — Time-Based Warnings

### Pattern: Cell emptiness + elapsed days

```
AND(TargetCell="", TODAY()-BaselineCell>=Days)
```

**Parameters:**
- `TargetCell` — the cell being formatted (e.g., `H2`)
- `BaselineCell` — the date cell to calculate from (e.g., `$G2`)
- `Days` — threshold in days

### Variable Reference Syntax

| Syntax | Meaning |
|--------|---------|
| `H2` | Relative column+row — adjusts when rule is applied across range |
| `$G2` | Absolute column (G), relative row (2) — each row checks its own G value |
| `$G$2` | Fully absolute — rarely used in per-row rules |

### Cross-Sheet Reference Syntax (Parameter-Driven)

When thresholds live on a separate "参数调节" (parameter) sheet:

```python
f'AND({col}2="",TODAY()-$G2>=参数调节!$B${param_row})'
```

**How it works:**
- `参数调节!$B$3` — absolute reference to cell B3 on the 参数调节 sheet
- User opens the 参数调节 sheet, changes the number, saves → rules auto-update
- This is a **design pattern** for non-technical users who shouldn't edit formulas

### Full Parameter-Driven Workflow

```
┌─────────────────────────┐
│ 参数调节 sheet          │  User edits numbers here
│ 报价时间  |  1  |  2    │
│ 图纸时间  |  3  |  4    │
│ ...                     │
└─────────┬───────────────┘
          │ Conditional formatting formulas reference these cells
          ▼
┌─────────────────────────┐
│ 项目进度 sheet          │  Colors auto-update on save+reopen
│ 接单时间 | 报价时间      │
│ 05-10    | 🔴 (empty)   │
└─────────────────────────┘
```

### Color Priority

Rules are evaluated in order. Add red **after** yellow so red takes visual priority when both conditions are met:

```python
ws.conditional_formatting.add('H2:H100',
    FormulaRule(formula=['AND(H2="",TODAY()-$G2>=1)'], fill=yellow_fill))
ws.conditional_formatting.add('H2:H100',
    FormulaRule(formula=['AND(H2="",TODAY()-$G2>=2)'], fill=red_fill))
```

### Clearing Existing Rules

```python
from openpyxl.formatting.formatting import ConditionalFormattingList
ws.conditional_formatting = ConditionalFormattingList()
```

**IMPORTANT:** Import from `openpyxl.formatting.formatting`, NOT `openpyxl.formatting`.

### Inspection

```python
for cf in ws.conditional_formatting:
    for rule in cf.rules:
        print(rule.formula, rule.fill.start_color.rgb)
```

## CellIsRule — For Static Value Checks

```python
from openpyxl.formatting.rule import CellIsRule

ws.conditional_formatting.add('A1:A100',
    CellIsRule(operator='greaterThan', formula=['100'], fill=PatternFill(start_color='FF0000', ...)))
```

Operators: `'lessThan'`, `'greaterThan'`, `'between'`, `'equal'`, `'notEqual'`, etc.

## ColorScale (Heatmaps)

```python
from openpyxl.formatting.rule import ColorScaleRule

ws.conditional_formatting.add('B2:B100',
    ColorScaleRule(start_type='min', start_color='00FF00',
                   mid_type='percentile', mid_value=50, mid_color='FFFF00',
                   end_type='max', end_color='FF0000'))
```

## DataBar

```python
from openpyxl.formatting.rule import DataBarRule

ws.conditional_formatting.add('C2:C100',
    DataBarRule(start_type='min', end_type='max',
                color='0078D7', showValue=True))
```

## CRITICAL LIMITATION: TODAY() / NOW() Volatility

- `TODAY()` and `NOW()` recalculate **every time the spreadsheet file is opened**
- They CANNOT be used for immutable timestamp logging (e.g., "record the exact time this cell was filled")
- If a user fills a cell at 2pm May 12, and you use `=NOW()` to auto-fill it, the value will be 2pm May 12... until they reopen the file tomorrow, at which point it becomes tomorrow's date
- **Use case:** Live warnings only (e.g., "this task is overdue relative to today")
- **Use case it cannot handle:** Audit logs, completion timestamps, "when did this happen"

### When to recommend alternative tools

If the user's need is "auto-record timestamps when someone fills in a status" AND multiple people need to do this from mobile phones:

| User need | Tool |
|-----------|------|
| 微信内轻量提交, 无需安装, 单向汇总 | 腾讯文档 收集表 |
| 分角色填写, 自动记时间, 权限控制, 超期推送 | 飞书多维表格 表单视图 |
| 全流程审批, 流转自动化, 企业级管理 | 钉钉宜搭 / 简道云 |
