# plus12monkeys

> SDK client for [+12 Monkeys](https://plus12monkeys.com) — generate MCP servers and SDK packages from any GitHub repo.

## Install

```bash
pip install plus12monkeys
```

## Quick Start

```python
from plus12monkeys import Client

client = Client()

# Generate an MCP server from any repo
result = client.generate_mcp("https://github.com/microsoft/BitNet.git")
result.write_to("./bitnet-mcp")

# Generate an SDK package instead
result = client.generate_sdk("https://github.com/microsoft/BitNet.git")
result.write_to("./bitnet-sdk")
```

## What You Get

### MCP Server (`generate_mcp`)
- `mcp_server.py` — fully functional MCP server
- `mcp-config.json` — Claude Desktop configuration
- `Dockerfile` — containerized deployment
- `requirements.txt` — Python dependencies
- `README.md` — setup instructions

### SDK Package (`generate_sdk`)
- `sdk.py` — typed client class (`BitnetClient`)
- `setup.py` — pip-installable package config
- `requirements.txt` — dependencies
- `README.md` — usage examples

## API Reference

### `Client(base_url, api_key, timeout)`
- `base_url` — API endpoint (default: `https://plus12monkeys.com/api/v1`)
- `api_key` — optional API key
- `timeout` — request timeout in seconds (default: 60)

### `client.generate_mcp(repo_url, project_name=None)`
Generate an MCP server wrapping the given repo.

### `client.generate_sdk(repo_url, project_name=None)`
Generate an SDK package wrapping the given repo.

### `result.write_to(directory, overwrite=False)`
Write all generated files to disk. Returns list of paths written.

### `result.file_paths()`
List all file paths in the generated package.

### `result.get_file(path)`
Get a specific generated file by path.

## License

MIT — [DeepTech AI](https://plus12monkeys.com)

