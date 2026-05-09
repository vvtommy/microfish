<img src=".github/assets/microfish-logo.png" width="128" vertical-align="middle">

# microfish

[![PyPI](https://img.shields.io/pypi/v/microfish)](https://pypi.org/project/microfish/) [![Docker](https://img.shields.io/badge/ghcr.io-microfish-blue)](https://ghcr.io/vvtommy/microfish) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> TinyFish 的纯免费 MCP 网关 — 仅暴露 Search 和 Fetch，别无其他。
> 

## 为什么选 microfish？

|  | 官方 MCP | microfish |
| --- | --- | --- |
| Search & Fetch（免费） | ✅ | ✅ |
| Agent / Browser / Batch（付费） | ✅ 已暴露 | ❌ 已剥离 |
| Agent 误触付费工具 | ⚠️ 可能 | 🚫 不可能 |
| API Key 池 | ❌ | ✅ 内置 |
| Rate limit | 单 key | 多 key 池化，更高吞吐 |
- **🔒 仅免费接口** — 只注册 `search`、`fetch_content`、`get_search_usage`、`list_fetch_usage` 四个工具。付费 API 从未暴露，agent 看不到也调不到 — 不会产生意外费用，不会浪费 token。
- **⚡ 内置 Key 池** — 配置多个 TinyFish API Key，microfish 自动轮转分配。单 key 失败自动 fallback 到下一个（最多 3 次重试），有效突破单 key 速率限制。

## 快速开始

> 免费获取 API Key → https://agent.tinyfish.ai/api-keys
> 

### stdio（推荐）

**Claude Code:**

```bash
TINYFISH_KEYS=<KEY> \
  claude mcp add microfish --env TINYFISH_KEYS -- uvx microfish
```

**Cursor / 其他 MCP 客户端:**

```json
{
  "mcpServers": {
    "microfish": {
      "command": "uvx",
      "args": ["microfish"],
      "env": { "TINYFISH_KEYS": "<KEY>" }
    }
  }
}
```

### HTTP

```bash
MICROFISH_TRANSPORT=http TINYFISH_KEYS=<KEY> uvx microfish
# 端点: http://localhost:8000/mcp
```

## 工具

### ✅ 可用

| 工具 | 说明 |
| --- | --- |
| `search` | 网页搜索（免费） |
| `fetch_content` | 拓取并提取网页内容（免费） |
| `get_search_usage` | 搜索用量统计 |
| `list_fetch_usage` | 拓取用量统计 |

### 🚫 已屏蔽

Agent 自动化 · 批量自动化 · 浏览器会话 · 运行生命周期

## 认证

**1. 客户端自带 key** — 不设置 `TINYFISH_KEYS`，客户端通过 `Authorization: Bearer` 传递自己的 key。

**2. 服务端单 key** — 设置 `TINYFISH_KEYS=<key>`，可选 `MCP_AUTH_TOKEN` 保护端点。

**3. 服务端 key 池** ⚡ — 设置 `TINYFISH_KEYS=k1,k2,k3`，按序轮转，失败自动切换（最多 3 次重试）。

## 配置

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `TINYFISH_KEYS` | — | 逗号分隔的 API keys，启用服务端管理模式 |
| `MCP_AUTH_TOKEN` | — | 客户端访问令牌（服务端管理模式） |
| `MICROFISH_TRANSPORT` | `stdio` | `stdio` 或 `http` |
| `MICROFISH_HOST` | `0.0.0.0` | 绑定地址（HTTP 模式） |
| `MICROFISH_PORT` | `8000` | 绑定端口（HTTP 模式） |
| `MICROFISH_MCP_PATH` | `/mcp` | MCP 端点路径（HTTP 模式） |

## 客户端配置示例

- Claude Code
    
    **HTTP:**
    
    ```bash
    # 无认证
    claude mcp add --transport http microfish http://localhost:8000/mcp
    
    # 有认证
    claude mcp add --transport http microfish http://localhost:8000/mcp \
      --header "Authorization: Bearer <YOUR_MCP_OR_TINYFISH_TOKEN>"
    ```
    
    **stdio:**
    
    ```bash
    TINYFISH_KEYS=<KEY> \
      claude mcp add microfish --env TINYFISH_KEYS -- uvx microfish
    ```
    
- Codex
    
    **HTTP:**
    
    ```toml
    [mcp_servers.microfish]
    url = "http://localhost:8000/mcp"
    bearer_token_env_var = "MICROFISH_MCP_BEARER"
    ```
    
    将 `MICROFISH_MCP_BEARER` 设置为 TinyFish API key（客户端自带模式）或 MCP auth token（服务端管理模式）。
    
    **stdio:**
    
    ```toml
    [mcp_servers.microfish]
    command = "uvx"
    args = ["microfish"]
    env = { TINYFISH_KEYS = "<KEY>" }
    ```
    
- Cursor
    
    **HTTP:**
    
    ```json
    {
      "mcpServers": {
        "microfish": {
          "url": "http://localhost:8000/mcp",
          "headers": {
            "Authorization": "Bearer ${env:MICROFISH_MCP_BEARER}"
          }
        }
      }
    }
    ```
    
    无需认证时删除 `headers` 块。
    
    **stdio:**
    
    ```json
    {
      "mcpServers": {
        "microfish": {
          "command": "uvx",
          "args": ["microfish"],
          "env": { "TINYFISH_KEYS": "<KEY>" }
        }
      }
    }
    ```
    

## 部署

### 本地运行

```bash
uvx microfish              # 直接运行，无需 clone
```

### Docker

```bash
docker compose up -d       # 拉取 ghcr.io/vvtommy/microfish:latest
```

- `docker-compose.yml` — 拉取发布镜像
- `docker-compose_build.yml` — 本地构建

<aside>
⚠️

不要在 compose 文件中写入 API key，请使用环境变量。

</aside>

## 参与贡献

欢迎提交 PR 和 Issue。重大改动请先开 issue 讨论。

## 发布

推送 `vX.Y.Z` tag 触发：PyPI 发布 + GHCR 镜像发布。

## 许可证

MIT