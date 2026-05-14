# Web UI v0.5.17 限流源码分析 & 127.0.0.1 白名单改造

> 分析日期：2026-05-14
> 对应会话：Web UI 因 rate limit 锁住 60 分钟 → 反编译 minified JS → 本地 IP 白名单改造

## 触发场景

在 Web UI 运行时，用 curl 发起连续带错误 Bearer Token 的 API 请求（如尝试不同格式的认证头），累计 3 次失败后，127.0.0.1 被锁定 60 分钟，Web UI 页面 API 全部返回 "Too many login attempts, please try again later"。

## 源码位置与函数结构

Web UI 服务端代码（minified）在：`dist/server/index.js`

### 限流常量（底部初始化段）

```javascript
// 变量定义行（在 VY 中 S 的初始化之前）：
nd=require("fs/promises"), Ci=require("fs"), jt=require("path"),
Ai=require("os"),
Li=(0,jt.join)((0,Ai.homedir)(), ".hermes-web-ui"),
Kt=(0,jt.join)(Li, ".login-lock.json"),

// 以下常量在 VY 函数中定义（约在文件后半段）：
ki=3,                         // 单 IP 最大失败次数
Pq=15*6e4,                    // 密码失败过期时间（15分钟）
zi=60*6e4,                    // IP 锁定时长（60分钟）
Ot=1e4,                       // IP Map 清理阈值
_q=6e4,                       // 每分钟窗口时长（60秒）
$q=100,                       // 每分钟最大请求数
xi=50,                        // 全局总失败阈值
Ui=30*6e4,                    // 全局锁定时长（30分钟）
S={                           // 运行时状态
  passwordIpMap:{},
  tokenIpMap:{},
  globalMinuteCount:0,
  globalMinuteWindow:0,
  globalTotalFailures:0,
  globalLockedUntil:0
}
```

### 关键函数定义（按调用链排列）

```javascript
// IP 提取
function ql(){return Date.now()}    // 当前时间（毫秒）
function eY(I){return I?.ip||I?.request?.ip||"unknown"}  // 从 Koa 上下文取 IP

// 全局锁检查（在 Ki 和 Si 内部调用）
function Mi(){
  let I=ql();
  return S.globalLockedUntil>0&&I<S.globalLockedUntil
    ? {allowed:!1, status:503}
    : (S.globalLockedUntil>0&&I>=S.globalLockedUntil
        &&(S.globalLockedUntil=0,S.globalTotalFailures=0,kG=!0),
       I-S.globalMinuteWindow>=_q
        &&(S.globalMinuteWindow=I,S.globalMinuteCount=0),
       S.globalMinuteCount>=$q
        ? {allowed:!1, status:429}
        : null)
}

// IP 锁检查（在 Ki 和 Si 内部调用）
function nY(I,G){                       // I=IP, G=IpMap
  let l=ql(),c=G[I];
  return c&&c.lockedUntil>0&&l<c.lockedUntil
    ? {allowed:!1, status:429}
    : (c&&c.lockedUntil>0&&l>=c.lockedUntil
        &&(delete G[I], kG=!0), null)
}

// 失败次数记录（在 fi 和 Ti 内部调用）
function ji(I,G){                        // I=IpMap, G=IP
  let l=ql(),c=I[G];
  c||(c={failures:0, lockedUntil:0, firstFailureAt:l}, I[G]=c);
  let b=c.firstFailureAt||l;
  return c.lockedUntil<=0&&l-b>Pq
    ? (c.failures=0, c.firstFailureAt=l)
    : c.firstFailureAt||(c.firstFailureAt=b),
    c.failures++,                        // ← 递增失败次数
    c
}

// ⭐ 四个需要修改的函数

function Ki(I){                           // 密码登录限流检查
  let G=Mi(); if(G) return G;
  let l=nY(I,S.passwordIpMap)||nY(I,S.tokenIpMap);
  return l||(S.globalMinuteCount++,kG=!0,cm(),{allowed:!0})
}

function Si(I){                           // Token 验证限流检查
  let G=Mi(); if(G) return G;
  let l=nY(I,S.tokenIpMap)||nY(I,S.passwordIpMap);
  return l||(S.globalMinuteCount++,kG=!0,cm(),{allowed:!0})
}

function fi(I){                           // 密码失败→上锁
  let G=ji(S.passwordIpMap,I);
  S.globalTotalFailures++, kG=!0;
  if(G.failures>=ki){
    G.lockedUntil=ql()+zi, Yd(); return  // 锁定 60 分钟
  }
  if(S.globalTotalFailures>=xi){
    S.globalLockedUntil=ql()+Ui, Yd();   // 全局锁定 30 分钟
    return
  }
  Bi(S.passwordIpMap), cm()
}

function Ti(I){                           // Token 失败→上锁
  let G=ji(S.tokenIpMap,I);
  S.globalTotalFailures++, kG=!0;
  if(G.failures>=ki){
    G.lockedUntil=ql()+zi, Yd(); return
  }
  if(S.globalTotalFailures>=xi){
    S.globalLockedUntil=ql()+Ui, Yd(); return
  }
  Bi(S.tokenIpMap), cm()
}
```

### 调用链

**Token 验证失败（`Tt` 中间件 — 第 61 行附近）：**
```
Tt(I)  →  取 token  →  token 不匹配
  →  eY(G) 取 IP
  →  Si(d) 检查限流  →  如果被限就返回 503/429
  →  Ti(d) 记失败次数  →  满 3 次锁 60 分钟
  →  返回 401 Unauthorized
```

**密码登录失败（`A5` 处理函数）：**
```
A5(I)  →  取 username/password
  →  eY(I) 取 IP
  →  Ki(c) 检查限流  →  如果被限就返回 503/429
  →  sn(G,l) 验证密码  →  失败
  →  fi(c) 记失败次数  →  满 3 次锁 60 分钟
  →  返回 401 Invalid username or password
```

## 白名单修改方法

对 `Ki`、`Si`、`fi`、`Ti` 四个函数，在入口对 127.0.0.1 和 ::1（IPv6 localhost）做白名单判断：

```javascript
function Ki(I){
  if(I==="127.0.0.1"||I==="::1")return{allowed:!0};  // ← 新增
  let G=Mi(); if(G)return G; ...
}

function Si(I){
  if(I==="127.0.0.1"||I==="::1")return{allowed:!0};  // ← 新增
  let G=Mi(); if(G)return G; ...
}

function fi(I){
  if(I==="127.0.0.1"||I==="::1")return;               // ← 新增
  let G=ji(S.passwordIpMap,I); ...
}

function Ti(I){
  if(I==="127.0.0.1"||I==="::1")return;               // ← 新增
  let G=ji(S.tokenIpMap,I); ...
}
```

### 修改后验证

```bash
# 1. 重启 Web UI
kill $(cat ~/.hermes-web-ui/server.pid)
rm -f ~/.hermes-web-ui/.login-lock.json
/home/lt-pc/.hermes/node-v23/bin/node \
  /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js \
  > ~/.hermes-web-ui/server.log 2>&1 &

# 2. 测试 Token 白名单：5 次错误请求不锁
for i in 1 2 3 4 5; do
  curl -s http://localhost:8648/api/sessions \
    -H "Authorization: Bearer wrong_token$i"
done
# → 都应返回 {"error":"Unauthorized"}，无「Too many...」

# 3. 测试密码白名单：5 次错误登录不锁
for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:8648/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}'
done
# → 都应返回 {"error":"Invalid username or password"}，无「Too many...」

# 4. 锁文件应为空
cat ~/.hermes-web-ui/.login-lock.json
```

## 注意事项

1. **minified 代码，直接改 JS 文件**：修改 `dist/server/index.js` 后重启才生效。Web UI 更新后会覆盖修改，需要重新打补丁。
2. **只改源码，包管理不记录**：这不是标准配置，如果未来 `npm update` Web UI，这些修改会丢失。需要写一个 post-update hook 或手动重打。
3. **白名单只限 127.0.0.1**：其他本地 IP（如 WSL 的 172.x.x.x）和远程 IP 仍受完整限流保护。
4. **`Di(c)` 函数（清锁）不受影响**：成功登录后仍会清除该 IP 的记录。

## 其他参考

- 锁文件持久化路径：`~/.hermes-web-ui/.login-lock.json`
- 状态重置时机：每次 Web UI 启动读锁文件，清理过期条目
- 全局限流每秒清理：通过 `_i()` 定时任务（每 2 秒检查一次）
