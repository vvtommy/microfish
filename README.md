<img src=".github/assets/microfish-logo.png" width="128" vertical-align="middle">

# microfish

中文文档: [README_cn.md](README_cn.md)

microfish is a restricted TinyFish MCP gateway. It exposes only the allowlisted TinyFish Search and Fetch related tools.

## Tools

Retained tools:
- search
- fetch_content
- get_search_usage
- list_fetch_usage

Blocked tool groups:
- Agent automation
- Batch automation
- Browser sessions

## Authentication and running modes

microfish only exposes TinyFish Search and Fetch related APIs. TinyFish Agent, Browser, batch, and run lifecycle APIs are intentionally not registered.

### Get a TinyFish API key

Generate your API key at https://agent.tinyfish.ai/api-keys.

### Client-owned single key

Leave `TINYFISH_KEYS` unset. Each MCP client sends `Authorization: Bearer <YOUR_TINYFISH_API_KEY>`. microfish forwards that value to TinyFish as `X-API-Key` for the current request only.

### Server-managed single key

Set `TINYFISH_KEYS` to one TinyFish API key. MCP clients do not receive the TinyFish key. If `MCP_AUTH_TOKEN` is set, clients send `Authorization: Bearer <YOUR_MCP_AUTH_TOKEN>`; if `MCP_AUTH_TOKEN` is unset, the MCP entrypoint is not protected by a bearer token.

### Server-managed key pool

Set `TINYFISH_KEYS` to multiple comma-separated TinyFish API keys. microfish assigns requests in order. When a whole upstream request fails, it tries the next key, stopping after all available keys for that call are tried or after three extra retries.

## Server configuration

microfish reads runtime settings from environment variables:

- `MICROFISH_HOST`: bind host for the HTTP server. Defaults to `0.0.0.0`.
- `MICROFISH_PORT`: bind port for the HTTP server. Defaults to `8000`.
- `MICROFISH_MCP_PATH`: HTTP path that exposes the MCP entrypoint. Defaults to `/mcp`.
- `MICROFISH_TRANSPORT`: transport for the server. Use http for the HTTP service or stdio for local coding agent subprocesses. Defaults to stdio.
- `TINYFISH_KEYS`: comma-separated TinyFish API keys; presence selects server-managed mode.
- `MCP_AUTH_TOKEN`: optional bearer token required from MCP clients in server-managed mode.

## Client configuration

microfish supports two transports:
- **stdio transport(default)** (`MICROFISH_TRANSPORT=stdio` or `--transport stdio`): launch `uvx microfish --transport stdio` as a local subprocess for coding agents.
- **HTTP transport** (`MICROFISH_TRANSPORT=http`): run microfish as an HTTP service and connect clients to `http://localhost:8000/mcp`.

For the HTTP transport, the value of `Authorization: Bearer` depends on your running mode:
- **Client-owned single key**: set it to your TinyFish API key.
- **Server-managed single/multiple keys with `MCP_AUTH_TOKEN`**: set it to the MCP auth token.
- **Server-managed keys without `MCP_AUTH_TOKEN`**: omit the Authorization header entirely.

The stdio transport requires `TINYFISH_KEYS` because there is no separate Authorization header on local subprocess pipes.

### Claude Code

HTTP transport:

```bash
# Without auth header
claude mcp add --transport http microfish http://localhost:8000/mcp

# With auth header
claude mcp add --transport http microfish http://localhost:8000/mcp \
  --header "Authorization: Bearer <YOUR_MCP_OR_TINYFISH_TOKEN>"
```

stdio transport:

```bash
TINYFISH_KEYS=<YOUR_TINYFISH_API_KEY> \
  claude mcp add microfish --env TINYFISH_KEYS -- uvx microfish
```

### Codex

HTTP transport:

```toml
[mcp_servers.microfish]
url = "http://localhost:8000/mcp"
bearer_token_env_var = "MICROFISH_MCP_BEARER"
```

Set `MICROFISH_MCP_BEARER` in your shell environment to your TinyFish API key (client-owned mode) or MCP auth token (server-managed mode).

stdio transport:

```toml
[mcp_servers.microfish]
command = "uvx"
args = ["microfish"]
env = { TINYFISH_KEYS = "<YOUR_TINYFISH_API_KEY>" }
```

### Cursor

HTTP transport:

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

Set `MICROFISH_MCP_BEARER` in your environment to your TinyFish API key (client-owned mode) or MCP auth token (server-managed mode). If no auth token is required, remove the `headers` block.

stdio transport:

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

## Run locally

    uv sync
    uv run microfish

Or run directly without cloning via `uvx microfish`.

## Docker

Two compose files are provided:
- `docker-compose.yml` pulls the published image `ghcr.io/vvtommy/microfish:${MICROFISH_IMAGE_TAG:-latest}` from GHCR.
- `docker-compose_build.yml` builds the local Dockerfile.

Both expose microfish on port 8000. Do not put TinyFish keys directly in compose files; pass them through your deployment environment.

```bash
docker compose up -d
claude mcp add --transport http microfish http://localhost:8000/mcp \
  --header "Authorization: Bearer <YOUR_MCP_OR_TINYFISH_TOKEN>"
```

## Releasing

Push a SemVer tag of the form `vX.Y.Z` to trigger publish workflows:
- `.github/workflows/pypi.yml` builds and publishes the Python package to PyPI via PyPI OIDC trusted publishing.
- `.github/workflows/docker.yml` builds and publishes `ghcr.io/vvtommy/microfish` Docker images with version tags and `latest`.

## MCP endpoint

    http://localhost:8000/mcp
