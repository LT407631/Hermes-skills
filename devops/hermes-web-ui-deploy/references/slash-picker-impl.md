# Slash Command Picker — 注入式 JS 改造记录

> 文件位置：`/home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/client/assets/js/slash-picker.js`  
> 注入方式：`client/index.html` 第45行 `<script src="/assets/js/slash-picker.js"></script>`  
> 修改日期：2026-05-14

## 功能概述

在 Hermes Web UI 的聊天输入框中输入 `/` 弹出命令面板，支持键盘导航和主题自适应。

## 命令列表

| 分类 | 命令 | 类型 | 说明 |
|------|------|------|------|
| 💬 会话 | /stop | 前端 | 停止生成 |
| | /clear | 前端 | 清空记录 |
| 🧠 模型 | /model | 后端 | 切换模型 |
| | /think | 后端 | 推理等级（含子菜单） |
| | /fallback | 后端 | 备用模型 |
| | /reasoning | 后端 | 显示/隐藏推理 |
| 🛠️ 其他 | /backup | 后端 | 创建备份 |
| | /help | 前端 | 显示命令列表 |

## 关键技术实现

### 主题自适应
使用 CSS 变量 `var(--xxx)` 而非硬编码色值。Web UI 的 `MarkdownRenderer-xEKocnSy.css` 已经在全局 `:root` 和 `.dark` 上定义了 CSS 变量，可以直接引用。

```css
#slash-picker {
  background: var(--bg-card,#18181e);
  border: 1px solid var(--border-color,#2a2a3a);
  color: var(--text-primary,#eee);
}
```

### 键盘导航
- `⬆⬇` — 上下选择命令/子菜单选项
- `⏎` — 执行选中命令/确认子选项
- `➡` — 展开子菜单（/think）
- `⬅` — 返回上级菜单
- `Esc` — 关闭菜单/返回上级

使用 `selectedIndex` 和 `subSelectedIndex` 跟踪位置。

### ⚠️ 已知 Bug 修复记录

**Bug 1：输入 `/` 后按回车把 / 发出去了**

**根因**：Enter 在 textarea 的 keydown 中提交了消息。

**修复**：在 `attachEvents` 中拦截 Enter：
```javascript
if (e.key === 'Enter' && self.visible) {
  e.preventDefault();
  // 注意：不要 stopPropagation！否则 handleKeydown 收不到事件
}
```
同时，关闭 picker 时自动清除文本框中残留的 `/`：
```javascript
hide: function () {
  if (ta) {
    var val = ta.value;
    if (val === '/' || val === ' /') {
      ta.value = '';
    }
  }
}
```

**Bug 2：子菜单/键盘选择失效**

**根因**：Enter 拦截时用了 `e.stopPropagation()`，导致 `handleKeydown` 收不到回车事件。

**修复**：去掉 `stopPropagation`，只保留 `preventDefault`。

## 修改方式

hermes-web-ui 装在全局 npm 路径中，直接编辑 dist 文件即可生效：

```bash
# 文件路径
/home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/client/assets/js/slash-picker.js

# 重启生效
kill $(cat ~/.hermes-web-ui/server.pid)
/home/lt-pc/.hermes/node-v23/bin/node \
  /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js \
  > ~/.hermes-web-ui/server.log 2>&1 &
```

每次修改后需重启 Web UI 进程才能生效。
