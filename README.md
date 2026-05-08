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
- `TINYFISH_KEYS`: comma-separated TinyFish API keys; presence selects server-managed mode.
- `MCP_AUTH_TOKEN`: optional bearer token required from MCP clients in server-managed mode.

## Client configuration

All examples use `http://localhost:8000/mcp` as the default URL. Replace it with your HTTPS address for remote deployments.

The value of `Authorization: Bearer` depends on your running mode:
- **Client-owned single key**: set it to your TinyFish API key.
- **Server-managed single/multiple keys with `MCP_AUTH_TOKEN`**: set it to the MCP auth token.
- **Server-managed keys without `MCP_AUTH_TOKEN`**: omit the Authorization header entirely.

### Claude Code

```bash
# Without auth header
claude mcp add --transport http microfish http://localhost:8000/mcp

# With auth header
claude mcp add --transport http microfish http://localhost:8000/mcp \
  --header "Authorization: Bearer <YOUR_MCP_OR_TINYFISH_TOKEN>"
```

### Codex

```toml
[mcp_servers.microfish]
url = "http://localhost:8000/mcp"
bearer_token_env_var = "MICROFISH_MCP_BEARER"
```

Set `MICROFISH_MCP_BEARER` in your shell environment to your TinyFish API key (client-owned mode) or MCP auth token (server-managed mode).

### Cursor

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

## Run locally

    uv sync
    uv run microfish

## Docker

`docker-compose.yml` builds the local Dockerfile and exposes microfish on port 8000.

A published image may be used as `ghcr.io/vvtommy/microfish:<VERSION>` after the repository release workflow publishes it. Do not put TinyFish keys directly in compose files; pass them through your deployment environment.

## Docker image publishing

Push a `vX.Y.Z` tag to publish `ghcr.io/vvtommy/microfish` with version tags and `latest`.

## MCP endpoint

    http://localhost:8000/mcp
