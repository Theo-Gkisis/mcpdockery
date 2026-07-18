# mcpdockery

An [MCP](https://modelcontextprotocol.io/) server that gives an LLM (Claude, etc.) direct, natural-language control over your local Docker daemon — containers, images, volumes, networks, and Compose stacks.

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) and the [Docker SDK for Python](https://docker-py.readthedocs.io/).

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Running the server](#running-the-server)
- [Connecting to an MCP client](#connecting-to-an-mcp-client)
- [Available tools](#available-tools)
- [Usage examples](#usage-examples)
- [Project structure](#project-structure)
- [Safety notes](#safety-notes)
- [License](#license)

## Requirements

| Requirement | Notes |
|---|---|
| [Python](https://www.python.org/) >= 3.14 | Interpreter version pinned in `.python-version` |
| [Docker](https://www.docker.com/) | Docker Desktop or Docker Engine, running locally |
| Docker Compose v2 CLI | `docker compose` must be available on `PATH` — required for the stack/compose tools |
| [Trivy](https://trivy.dev/) | `trivy` must be available on `PATH` — required for the `scan_image` tool |
| [uv](https://docs.astral.sh/uv/) | Used for dependency management and running the server |

For pulling from or pushing to a private registry (Docker Hub, AWS ECR, GCR, etc.), authenticate with that registry beforehand using your normal `docker login` flow — this server never accepts or stores credentials itself.

## Installation

1. Clone the repository:
   ```bash
   git clone <this-repo>
   cd mcpdockery
   ```
2. Install dependencies:
   ```bash
   uv sync
   ```
   This creates a `.venv` and installs the exact dependency versions pinned in `uv.lock`.
3. Confirm Docker is running:
   ```bash
   docker info
   ```
   If this command fails, start Docker Desktop (or your Docker Engine) before continuing.

## Running the server

```bash
uv run src/main.py
```

The server communicates over stdio, so it's meant to be launched by an MCP client rather than run standalone in a terminal.

## Connecting to an MCP client

Add an entry to your MCP client's configuration (e.g. `claude_desktop_config.json` for Claude Desktop, or your project's `.mcp.json` for Claude Code):

```json
{
  "mcpServers": {
    "mcpdockery": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/mcpdockery", "run", "src/main.py"]
    }
  }
}
```

Replace `/absolute/path/to/mcpdockery` with the actual path where you cloned the repository, then restart the client. The tools listed below will become available to the model.

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
| `list_images` | Lists all local images, including untagged/intermediate ones, with size |
| `pull_image` | Pulls an image from a registry without running it; defaults to the `alpine` tag unless a different tag is requested |
| `build_image` | Builds an image from a Dockerfile already on disk |
| `push_image` | Tags and pushes a local image to a registry (requires prior `docker login`) |
| `delete_image` | Force-removes a local image |

### Volumes (`volumes.py`)

| Tool | Description |
|---|---|
| `list_volumes` | Lists volumes with driver and mountpoint |
| `create_volume` | Creates a new volume |
| `remove_volume` | Deletes a volume (fails if still in use) |

### Networks (`networks.py`)

| Tool | Description |
|---|---|
| `list_networks` | Lists networks with driver and scope |
| `create_network` | Creates a new network |

### Diagnostics (`diagnostics.py`)

| Tool | Description |
|---|---|
| `docker_doctor` | Scans all containers and reports only the ones needing attention: OOM kills, restart loops, unhealthy checks, crashes, high CPU/memory |

### Security (`security.py`)

| Tool | Description |
|---|---|
| `scan_image` | Scans an image for known vulnerabilities using Trivy; defaults to CRITICAL/HIGH severity only |
| `scan_dockerfile` | Scans a Dockerfile for misconfigurations (root user, `latest` tag, hardcoded secrets, missing HEALTHCHECK, etc.) before it's even built |

### Compose stacks (`stacks.py`)

| Tool | Description |
|---|---|
| `deploy_stack` | Deploys a stack from an inline `docker-compose.yml` (`compose up -d`) |
| `stop_stack` | Stops a stack's containers without removing them |
| `remove_stack` | Stops and removes a stack, including its volumes (`compose down -v`) |
| `list_stacks` | Lists all compose projects, including stopped ones |
| `stack_status` | Shows the status of a stack's containers (`compose ps`) |
| `stack_logs` | Collects logs from every container in a stack |

## Usage examples

Once connected, you can drive the server with natural-language requests. A few examples of what to expect:

| You ask | Tool(s) the model will likely use |
|---|---|
| "Pull the alpine version of redis" | `pull_image` |
| "Run an nginx container on port 8080" | `run_container` |
| "Show me the logs for my-app from the last hour" | `container_logs` |
| "What's using all the CPU right now?" | `list_containers`, `container_stats` |
| "Is anything broken right now?" | `docker_doctor` |
| "Deploy this docker-compose file as 'staging'" | `deploy_stack` |
| "Push my-app:latest to my ECR repo" | `push_image` |
| "Clean up the my-app container and its image" | `delete_container`, `delete_image` |
| "Scan my-app:latest for vulnerabilities" | `scan_image` |
| "Check my Dockerfile for security issues before I build it" | `scan_dockerfile` |

The model chooses which tool(s) to call based on your request — you don't need to name the tool yourself.

## Project structure

```
src/
  main.py             # Entrypoint: registers tool modules and starts the MCP server
  server.py           # Shared FastMCP server instance
  docker_client.py    # Lazy singleton Docker SDK client
  compose_client.py   # Thin wrapper around the `docker compose` CLI
  helper.py           # Shared helpers (path normalization, image tag parsing, Trivy wrapper)
  containers.py       # Container lifecycle & inspection tools
  images.py           # Image pull/build/push/list/delete tools
  volumes.py          # Volume tools
  networks.py         # Network tools
  stacks.py           # Compose stack tools
  security.py         # Image vulnerability scanning tools
  diagnostics.py      # Cross-container health triage tools
```

## Safety notes

This server gives the model real, unsandboxed control over your Docker daemon:

- `delete_container` and `delete_image` force-remove resources without confirmation.
- `remove_stack` deletes volumes (`-v`), which is destructive and irreversible for stateful data.
- `container_exec` runs arbitrary shell commands inside a container.
- `push_image` and `pull_image` use your existing local Docker credentials — the model can push to or pull from any registry you're currently authenticated with. Note that AWS ECR tokens expire after 12 hours; if a push/pull suddenly fails with an auth error, re-run your `docker login` / `aws ecr get-login-password` flow rather than assuming the tool is broken.

Only connect this server to clients/agents you trust, and be deliberate about which containers and stacks you let it touch.

## License

No license specified.
