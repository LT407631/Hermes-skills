# 2026-05-13 会话：Dev/Op 多 Profile Gateway 端口分配 BUG

## 触发场景

在 Web UI 网关管理页面尝试启动 Dev 和 Op 两个 profile 的 gateway，反复失败。

## 症状

```
Gateway health check timed out after 15000ms
```

Web UI 日志：
```
Assigning port for profile "dev": 8653 → 8643
Assigning port for profile "op": 8654 → 8644
...
dev: failed to start
op: failed to start
```

## 诊断路径

### 1. 确认端口实际状态

```bash
ss -tlnp | grep -E '8653|8654'
# → 端口完全空闲，没有任何进程占用
```

### 2. 观察进程实际行为

```bash
# 查看 gateway run --replace 启动后的进程实际监听的端口
sudo lsof -i -P -n | grep <PID>
# 或从 /proc/<PID>/net/tcp 解析
```

手动用 `HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace` 启动后：
- dev 进程不监听配置的 8653，而是监听了 8651
- 且同时监听了两个端口（8646 和 8651）

### 3. 检查 config.yaml 被篡改

```bash
grep -A6 "api_server:" ~/.hermes/profiles/dev/config.yaml
# 发现 GatewayManager 把 port 从 8653 改成了 8643
# 还把 extra.key 删掉了！
```

## BUG 根因

GatewayManager 的 `resolvePort()` 方法在 WSL 环境中的问题：

1. **`checkPortAvailable()` 误判**：用 `net.createServer().listen(port, host)` 测试端口是否可用，但可能受到以下干扰：
   - WSL 的端口转发机制（Windows 到 WSL 的端口映射）
   - `allocatedPorts` 集合的内存级错误（来自之前失败的启动尝试残留）
   
2. **`findFreePort()` 递增逻辑**：从 base 端口向上递增找空闲端口，但 base 本身是空闲的，却仍然递增了 → 说明 `checkPortAvailable()` 返回了 false（误判）

3. **`hermes gateway run --replace` 自选端口**：当 `--replace` 遇到已存在的 gateway 锁文件（不同端口的），可能自行绑定到锁文件中记录的端口而不是配置端口

4. **配置文件反复损坏**：每次 GatewayManager 运行，`writeProfilePort()` 都会写入新的端口并可能丢失 `extra.key` 字段

## 修复记录

**首次修复尝试**：直接改 config.yaml 中 `api_server.extra.port` 为 8653/8654 → 失败（GatewayManager 重启后又改写）

**二次修复尝试**：删 lock/pid 文件 + 修 config + 重启 Web UI → 失败（GatewayManager 启动时再次改写）

**最终有效方案**：手动从终端启动，完全绕过 GatewayManager
```bash
HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace &
HERMES_HOME=~/.hermes/profiles/op hermes gateway run --replace &
```

## 配置正确形态（修复后）

```yaml
# ~/.hermes/profiles/dev/config.yaml
platforms:
  api_server:
    enabled: true
    key: ''
    cors_origins: '*'
    extra:
      port: 8653              # dev 占 8653
      host: 127.0.0.1
      key: lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE  # 必须保留

# ~/.hermes/profiles/op/config.yaml → port: 8654
```

## 配置文件被 Python yaml.dump 损坏的修复

```bash
# 当 dev/op config.yaml 被 Python 脚本截断或损坏时：
# 直接从 default profile 复制一份再改端口
cp ~/.hermes/config.yaml ~/.hermes/profiles/dev/config.yaml
cp ~/.hermes/config.yaml ~/.hermes/profiles/op/config.yaml

# 然后用 Python 精确修改端口
python3 -c "
import os, yaml
for pf, pt in [('dev', 8653), ('op', 8654)]:
    p = os.path.expanduser(f'~/.hermes/profiles/{pf}/config.yaml')
    with open(p) as f:
        c = yaml.safe_load(f)
    c['platforms'] = {
        'api_server': {
            'enabled': True, 'key': '', 'cors_origins': '*',
            'extra': {'port': pt, 'host': '127.0.0.1', 'key': 'lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE'}
        }
    }
    with open(p, 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    print(f'{pf}: fixed port={pt}')
"
```

## 2026-05-13 新增发现：--replace 不强制使用配置端口

### 过程复现

在已修复的配置（dev=8653, op=8654）上手动执行：
```bash
HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace &
HERMES_HOME=~/.hermes/profiles/op hermes gateway run --replace &
```

结果（ss -tlnp 观察）：

| Profile | 配置端口 | 实际监听端口 |
|---------|---------|-------------|
| dev | 8653 | 8651 |
| op | 8654 | 8646 |

端口在多次 kill+重启后保持稳定（与前一次手动启动时一致），说明 `hermes gateway run --replace` 内部的端口分配机制完全独立于 `config.yaml` 的 `api_server.extra.port` 字段。

### 被动修复法：配置对齐实际端口

既然无法通过 --replace 强制 gateway 使用配置端口，最务实的方案是：

1. 确认实际进程已正常运行（ss -tlnp | grep hermes）
2. 读取每个进程的实际端口
3. 将配置文件端口改为实际端口
4. 不需要杀进程、不需要重启

实现脚本：
```python
import os, yaml
home = os.path.expanduser('~/.hermes')
fixes = {'dev': 8651, 'op': 8646}  # 以实际端口为准
for name, actual_port in fixes.items():
    path = os.path.join(home, 'profiles', name, 'config.yaml')
    with open(path) as f:
        c = yaml.safe_load(f)
    api = c.setdefault('platforms', {}).setdefault('api_server', {})
    extra = api.setdefault('extra', {})
    extra['port'] = actual_port
    extra['host'] = '127.0.0.1'
    extra['key'] = 'lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE'
    api['enabled'] = True
    api['cors_origins'] = '*'
    with open(path, 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
```

### 进程端口映射确认方法

```bash
# 1. 找到所有 hermes gateway 进程的 PID 和端口
ss -tlnp | grep hermes

# 2. 确认每个 PID 对应的 profile
for pid in $(pgrep -f 'hermes.*gateway.*replace' | grep -v 37575); do
    echo "=== PID $pid ==="
    cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep HERMES_HOME
done

# 3. 确认实际监听端口（从 ss 输出匹配）
```

## 经验教训（更新）

1. **永远不要在 Web UI 终端内 kill gateway 进程** → 会触发 GatewayManager 的连锁篡改
2. **GatewayManager 的 resolvePort() 有 bug** → 多 profile 场景下不要依赖 Web UI 的启动按钮
3. **--replace 不强制使用配置端口** → gateway 进程内部的端口分配机制完全独立于 config.yaml 的 api_server.extra.port
4. **对不反抗，只对齐** → gateway 进程已在错误端口上正常运行时，改配置比杀进程重跑更可靠
5. **配置修复用 Python yaml.dump（默认参数）** → 不要用 line_width，某些 PyYAML 版本不支持
6. **rm 命令在 WSL 特定文件上可能超时** → 用 python3 -c "import os; os.remove(...)" 替代
