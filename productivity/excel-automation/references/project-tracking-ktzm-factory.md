# 全屋定制工厂 · 项目进度管理表设计参考

Domain: 全屋定制家具工厂/KTZM B端
This file captures the specific table design, process flow, and conditional formatting rules built for 腾哥's factory (洛阳鑫德).

## 工序全流程（16个环节）

| # | 环节 | 责任人 | 时限规则 | 预警参数 |
|---|------|-------|---------|---------|
| 1 | 项目报备 | 销售经理 | 当天 | - |
| 2 | 报价回传 | 销售经理 | 当天 | 黄1天 / 红2天 |
| 3 | 到款通知 | 销售经理 | 当天 | 黄1天 / 红2天 |
| 4 | 填写采购单 | 助理 | 当天 | 黄1天 / 红2天 |
| 5 | 确认客单号 | 助理 | 当天 | - (信息字段) |
| 6 | 精确图纸回传 | 设计师 | 3天内 | 黄3天 / 红4天 |
| 7 | 图纸拆单 | 设计师+拆单 | 7天内 | 黄7天 / 红8天 |
| 8 | 订单审核 | 拆单 | 7天内 | 黄7天 / 红8天 |
| 9 | 采购到厂 | 仓库 | 7天内 | 黄7天 / 红8天 |
| 10 | 排产备板 | 排版 | 8天内 | 黄8天 / 红9天 |
| 11 | 车间生产 | 车间 | 9天内 | 黄8天 / 红9天 |
| 12 | 完成入库 | 助理 | 15天内 | 黄15天 / 红16天 |
| 13 | 送货安排 | 助理 | 只记录时间 | 不预警 (0/0) |
| 14 | 安装完成 | 安装负责人 | 送货到现场3天内 | 黄18天 / 红20天 |
| 15 | 项目验收 | 安装负责人 | 安装后3天内 | 黄22天 / 红24天 |
| 16 | 售后服务 | 安装负责人 | 客户申请后3天内 | 不预警 (0/0) |

## 角色与权限

| 角色 | 负责环节 |
|------|---------|
| 销售经理 | 项目报备、报价回传、到款通知 |
| 助理 | 采购单、客单号确认、入库、送货 |
| 设计师 | 图纸回传、拆单配合 |
| 拆单 | 图纸拆单、订单审核 |
| 仓库 | 采购到厂 |
| 排版 | 排产备板 |
| 车间 | 车间生产 |
| 安装负责人 | 送货安排、安装完成、项目验收、售后服务 |
| 老板 | 看数据看板、超期监控 |

## 项目进度表列设计（21列）

A: 客单号
B: 销售经理
C: 经销商
D: 终端地址
E: 设计师
F: 拆单
G: 接单时间 ← **基准时间列**
H: 报价时间
I: 回款时间
J: 采购时间
K: 图纸时间
L: 拆单完成
M: 采购到厂
N: 生产开始
O: 入库完成
P: 送货时间
Q: 安装完成时间
R: 验收时间
S: 售后时间
T: 合同金额
U: 投影面积

## 参数调节表设计

Sheet: 参数调节 (插入到最前面)
Rows: 环节名 | 变黄天数 | 变红天数 | 说明

All conditional formatting formulas reference this sheet via absolute references:
`参数调节!$B$3` (yellow), `参数调节!$C$3` (red)

Key formula pattern for CF:
```
AND(H2="",TODAY()-$G2>=参数调节!$B$3,参数调节!$B$3>0)
```
The extra `参数调节!$B$3>0` condition prevents false warnings when threshold is 0.

## 技术要点

1. **CF range**: Use `H2:H1000` to cover future rows. User adds rows beyond 1000 → update formula range.
2. **Number format for date fields**: `YYYY-MM-DD`
3. **Number format for currency**: `#,##0`
4. **Skip-when-zero logic**: Delivery time (P) and after-sales time (S) use 0/0 → the `>0` condition in CF formula prevents them from triggering.
5. **Color scheme**: Blue header (#4472C4), yellow warning (#FFFF00), red overdue (#FF0000).

## 方案对比速查

When user asks about multi-role mobile form submission → this is the standard comparison:

| 方案 | 成本 | 周期 | 优点 | 缺点 |
|------|------|------|------|------|
| 飞书多维表格 | 0元/月 | 1小时 | 0成本快速验证 | 需装App, 不能ERP对接 |
| 微信小程序 | 1.5-3万开发+1100/年运维 | 4-5周 | 微信原生, 数据自主, 完全定制 | 开发周期长 |
| 腾讯文档收集表 | 0元 | 10分钟 | 微信直接填, 0安装 | 单向提交, 无自动化 |
| 钉钉宜搭 | 免费版够用 | 1天 | 分角色+自动化 | 需装钉钉 |
