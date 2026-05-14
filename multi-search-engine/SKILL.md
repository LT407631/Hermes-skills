---
name: multi-search-engine
description: 多搜索引擎聚合查询——17 个搜索引擎一站式检索。当 web_search 不可用或需要对比多引擎结果时使用。
---

# multi-search-engine

多搜索引擎聚合查询——17 个搜索引擎一站式检索。作为 `web_search` 工具的备用方案，在 Web 搜索失效时使用，也可以与默认搜索对比效果。

**来源：** 从 skills.sh（aaaaqwq/agi-super-skills）手动导入 Hermes。

**相关技能：** `short-video-b2b-acquisition`（全屋定制 B 端获客主技能）

## 使用场景

- `web_search` 不可用/失效时作为备用
- 需要同时搜索国内外多个引擎，对比结果
- 区域性搜索（CN vs Global）
- 需要访问国内搜索引擎（百度、搜狗等）

## 支持引擎

| 区域 | 引擎 |
|------|------|
| CN | 百度、Bing CN、360、搜狗、头条搜索、微信搜狗、集思录 |
| Global | Google、Google HK、DuckDuckGo、Yahoo、Startpage、Brave、Ecosia、Qwant、WolframAlpha |

## 使用方式

### 方法一：DuckDuckGo（首选备用）

```bash
# CLI 搜索
pip install ddgs
ddgs text -q "搜索关键词" -m 5 -o json

# 带过滤
ddgs text -q "搜索关键词" -m 5 -t w   # 过去一周
ddgs text -q "搜索关键词" -m 5 -r cn-zh  # 中文区域
```

### 方法二：直接调用搜索引擎

通过 curl 或 Python requests 直接调用公开搜索引擎。

**百度搜索：**
```bash
curl -sL "https://www.baidu.com/s?wd=搜索关键词" | grep -oP '<a[^>]*href="[^"]*"[^>]*>[^<]+</a>' | head -10
```

**Bing 搜索：**
```bash
curl -sL "https://www.bing.com/search?q=搜索关键词&setlang=zh-cn" | grep -oP '<h2><a[^>]*href="([^"]+)"[^>]*>([^<]+)</a></h2>' | head -10
```

**WolframAlpha（知识查询）：**
```bash
curl -sL "https://api.wolframalpha.com/v2/query?input=计算表达式&appid=DEMO&format=plaintext"
```

### 方法三：Python 多引擎聚合

```python
import urllib.request, urllib.parse, json, re

def search_ddg(query, max_results=5):
    """DuckDuckGo 搜索"""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=10).read().decode()
    results = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<', html)
    return [{"title": t, "url": u} for u, t in results[:max_results]]

def search_baidu(query, max_results=5):
    """百度搜索"""
    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=10).read().decode()
    results = re.findall(r'<a[^>]*href="([^"]+)"[^>]* class="[^"]*result-title[^"]*"[^>]*>([^<]+)<', html)
    return [{"title": t.strip(), "url": u} for u, t in results[:max_results]]

# 使用
ddg_results = search_ddg("全屋定制 B端 获客")
baidu_results = search_baidu("全屋定制 工厂 招商")
```

## 与 web_search 的对比

| 方面 | web_search（默认） | multi-search-engine |
|------|-------------------|-------------------|
| 后端 | Firecrawl/Tavily/Exa | 直接调用搜索引擎 API |
| 速度 | 快（有 API 缓存） | 中等（实时抓取） |
| 中文搜索 | 视后端而定 | ✅ 百度/搜狗/360 原生中文 |
| API Key | 需要 | 不需要 |
| 稳定性 | 依赖 API 服务商 | 依赖搜索引擎可用性 |

## 切换策略

1. **默认优先**使用 `web_search`
2. `web_search` 无结果或报错时，**自动切换**到 `multi-search-engine`（DDG 或百度）
3. 结果差异大时，**两个引擎都跑一次**对比
