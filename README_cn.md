<img src=".github/assets/microfish-logo.png" width="128" vertical-align="middle">

# microfish

English documentation: [README.md](README.md)

microfish 是一个裁剪版 TinyFish MCP 网关，只暴露 allowlist 中的 TinyFish Search 和 Fetch 相关工具。

## 工具列表

保留工具：
- search
- fetch_content
- get_search_usage
- list_fetch_usage

屏蔽工具组：
- Agent 自动化
- 批量自动化
- 浏览器会话

## 认证与运行模式

microfish 只暴露 TinyFish Search 与 Fetch 相关 API。TinyFish Agent、Browser、batch 和 run lifecycle API 都不会注册。

### 获取 TinyFish API Key

到 https://agent.tinyfish.ai/api-keys 生成你的 API key。

### 客户端单 Key 模式

不设置 `TINYFISH_KEYS`。每个 MCP 客户端发送 `Authorization: Bearer <YOUR_TINYFISH_API_KEY>`。microfish 只在当前请求中把它转成上游 `X-API-Key`。

### 服务端单 Key 模式

将 `TINYFISH_KEYS` 设置为一个 TinyFish API key。MCP 客户端不会拿到 TinyFish key。如果设置了 `MCP_AUTH_TOKEN`，客户端发送 `Authorization: Bearer <YOUR_MCP_AUTH_TOKEN>`；如果未设置 `MCP_AUTH_TOKEN`，MCP 入口不做 Bearer 校验。

### 服务端多 Key 模式

将 `TINYFISH_KEYS` 设置为多个逗号分隔的 TinyFish API key。microfish 按顺序分配请求。整体上游请求失败时尝试下一个 key，并在该次调用试完可用 key 或完成最多三次额外重试后停止。

## 服务端配置

microfish 通过环境变量读取运行时配置：

- `MICROFISH_HOST`：HTTP 服务绑定主机，默认 `0.0.0.0`。
- `MICROFISH_PORT`：HTTP 服务绑定端口，默认 `8000`。
- `MICROFISH_MCP_PATH`：MCP 入口的 HTTP 路径，默认 `/mcp`。
- `MICROFISH_TRANSPORT`：服务传输模式。http 用于 HTTP 服务，stdio 用于 coding agent 本地子进程。默认 stdio。
- `TINYFISH_KEYS`：逗号分隔的 TinyFish API key；设置后进入服务端托管模式。
- `MCP_AUTH_TOKEN`：服务端托管模式下可选的 MCP 客户端 bearer token。

## 客户端配置

microfish 支持两种传输方式：
- **stdio 传输(默认)**（`MICROFISH_TRANSPORT=stdio` 或 `--transport stdio`）：以 `uvx microfish --transport stdio` 作为 coding agent 的本地子进程启动。
- **HTTP 传输**（`MICROFISH_TRANSPORT=http`）：以 HTTP 服务运行 microfish，客户端连接 `http://localhost:8000/mcp`。

HTTP 传输下 `Authorization: Bearer` 的取值依赖运行模式：
- **客户端单 Key 模式**：填写你的 TinyFish API key。
- **服务端单 Key 或多 Key 模式且设置了 `MCP_AUTH_TOKEN`**：填写 MCP auth token。
- **服务端托管 key 但未设置 `MCP_AUTH_TOKEN`**：省略 Authorization 头。

stdio 传输需要设置 `TINYFISH_KEYS`，因为本地子进程管道没有独立的 Authorization 头。

### Claude Code

HTTP 传输：

```bash
# 不带认证头
claude mcp add --transport http microfish http://localhost:8000/mcp

# 带认证头
claude mcp add --transport http microfish http://localhost:8000/mcp \
  --header "Authorization: Bearer <YOUR_MCP_OR_TINYFISH_TOKEN>"
```

stdio 传输：

```bash
TINYFISH_KEYS=<YOUR_TINYFISH_API_KEY> \
  claude mcp add microfish --env TINYFISH_KEYS -- uvx microfish
```

### Codex

HTTP 传输：

```toml
[mcp_servers.microfish]
url = "http://localhost:8000/mcp"
bearer_token_env_var = "MICROFISH_MCP_BEARER"
```

在 shell 环境中将 `MICROFISH_MCP_BEARER` 设置为你的 TinyFish API key（客户端单 Key 模式）或 MCP auth token（服务端托管模式）。

stdio 传输：

```toml
[mcp_servers.microfish]
command = "uvx"
args = ["microfish"]
env = { TINYFISH_KEYS = "<YOUR_TINYFISH_API_KEY>" }
```

### Cursor

HTTP 传输：

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

在环境变量中将 `MICROFISH_MCP_BEARER` 设置为你的 TinyFish API key（客户端单 Key 模式）或 MCP auth token（服务端托管模式）。如不需要认证，可移除 `headers` 块。

stdio 传输：

```json
{
  "mcpServers": {
    "microfish": {
      "command": "uvx",
      "args": ["microfish"],
      "env": {
        "TINYFISH_KEYS": "<YOUR_TINYFISH_API_KEY>"
      }
    }
  }
}
```

## 本地运行

    uv sync
    uv run microfish

或者无需克隆仓库，直接使用 `uvx microfish`。

## Docker

仓库提供两份 compose 文件：
- `docker-compose.yml` 拉取 GHCR 上发布的镜像 `ghcr.io/vvtommy/microfish:${MICROFISH_IMAGE_TAG:-latest}`。
- `docker-compose_build.yml` 使用本地 Dockerfile 构建镜像。

两份文件都将 microfish 暴露在 8000 端口。不要直接将 TinyFish key 写入 compose 文件，请通过部署环境的环境变量传递。

```bash
docker compose up -d
claude mcp add --transport http microfish http://localhost:8000/mcp \
  --header "Authorization: Bearer <YOUR_MCP_OR_TINYFISH_TOKEN>"
```

## 发布

推送形如 `vX.Y.Z` 的 SemVer tag 会触发以下 workflow：
- `.github/workflows/pypi.yml`：构建并通过 PyPI OIDC trusted publishing 发布 Python 包到 PyPI。
- `.github/workflows/docker.yml`：构建并发布 `ghcr.io/vvtommy/microfish` Docker 镜像，包含版本 tag 和 `latest`。

## MCP 端点

    http://localhost:8000/mcp
