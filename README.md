# Dockhand

An [MCP](https://modelcontextprotocol.io/) server that gives an LLM (Claude, etc.) direct control over your local Docker daemon — run and manage containers, images, volumes, networks, and Compose stacks through natural language.

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) and the [Docker SDK for Python](https://docker-py.readthedocs.io/).

## Requirements

- Python >= 3.14
- [Docker](https://www.docker.com/) installed and running locally (Docker Desktop, Docker Engine, etc.)
- Docker Compose v2 CLI (`docker compose`) available on `PATH` — required for the stack/compose tools
- [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

```bash
git clone <this-repo>
cd dockhand
uv sync
```

This creates a `.venv` and installs the dependencies pinned in `uv.lock`.

## Running

```bash
uv run main.py
```

The server communicates over stdio, so it's meant to be launched by an MCP client rather than run standalone in a terminal.

### Connecting to Claude Desktop / Claude Code

Add an entry to your MCP client's configuration (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "dockhand": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/dockhand", "run", "main.py"]
    }
  }
}
```

Restart the client and the tools below become available to the model.

## Available tools

### Containers (`containers.py`)

| Tool | Description |
|---|---|
| `run_container` | Runs a container from an image, mapping a container port to a host port |
| `stop_container` | Stops a running container |
| `container_start` | Starts a stopped container |
| `container_restart` | Restarts a container |
| `delete_container` | Force-removes a container (stops it first if needed) |
| `list_containers` | Lists all containers and their status |
| `container_logs` | Fetches the last N log lines from a container |
| `container_stats` | Reports live CPU % and memory usage |
| `container_inspect` | Shows env vars, mounts, network IPs, and health status |
| `container_exec` | Executes a shell command inside a running container |

### Images (`images.py`)

| Tool | Description |
|---|---|
| `list_images` | Lists all local images with size |
| `build_image` | Builds an image from a Dockerfile already on disk |
| `push_image` | Tags and pushes a local image to a registry (requires prior `docker login`) |
| `delete_image` | Force-removes a local image |

### Volumes & networks (`volumes.py`)

| Tool | Description |
|---|---|
| `list_volumes` | Lists volumes with driver and mountpoint |
| `remove_volume` | Deletes a volume (fails if still in use) |
| `list_networks` | Lists networks with driver and scope |

### Compose stacks (`stacks.py`)

| Tool | Description |
|---|---|
| `deploy_stack` | Deploys a stack from an inline `docker-compose.yml` (`compose up -d`) |
| `stop_stack` | Stops a stack's containers without removing them |
| `remove_stack` | Stops and removes a stack, including its volumes (`compose down -v`) |
| `list_stacks` | Lists all compose projects, including stopped ones |
| `stack_status` | Shows the status of a stack's containers (`compose ps`) |
| `stack_logs` | Collects logs from every container in a stack |

## Project structure

```
main.py            # Entrypoint: registers tool modules and starts the MCP server
server.py           # Shared FastMCP server instance
docker_client.py    # Lazy singleton Docker SDK client
compose_client.py   # Thin wrapper around the `docker compose` CLI
containers.py       # Container lifecycle & inspection tools
images.py           # Image build/push/list/delete tools
volumes.py          # Volume & network tools
stacks.py           # Compose stack tools
```

## Safety notes

This server gives the model real, unsandboxed control over your Docker daemon:

- `delete_container` and `delete_image` force-remove resources without confirmation.
- `remove_stack` deletes volumes (`-v`), which is destructive and irreversible for stateful data.
- `container_exec` runs arbitrary shell commands inside a container.
- `push_image` pushes to whatever registry you point it at, using your existing local Docker credentials.

Only connect this server to clients/agents you trust, and be deliberate about which containers and stacks you let it touch.

## License

No license specified.
