from server import mcp
from docker_client import get_client
from helper import _container_usage, _redact_env


@mcp.tool()
def run_container(image: str, container_name: str, container_port: str, host_port: str) -> str:
    """
    Runs a Docker container locally for testing
    Args:
        image: Docker image to run, e.g. "nginx:latest"
               If no tag is specified, then usel alpine for default.It is smaller and faster to pull
        container_name: container name
        container_port: port the app listens on INSIDE the container, e.g. "80" for nginx
        host_port: port on your machine to access it, e.g. "8080" → http://localhost:8080
    """
    if ":" not in image:
        image = f"{image}:alpine"

    try:
        client = get_client()
        container = client.containers.run(
            image,
            name=container_name,
            detach=True,
            ports={f"{container_port}/tcp": host_port},
        )

        return f"Started container {container.short_id} ({container.name}) from image '{image}'"
    except Exception as e:
        return f"Error running container: {e}"


@mcp.tool()
def stop_container(container_name: str) -> str:
    """
    User will pass the container name that we need to stop
    Args:
        container_name: Docker Container name
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        container.stop()
        return f"Stopped container '{container_name}'"
    except Exception as e:
        return f"Error while trying to stop the container: {e}"


@mcp.tool()
def list_containers() -> str:
    """
    Returns all containers with their status
    """
    try:
        client = get_client()
        containers = client.containers.list(all=True)
        if not containers:
            return "No containers running at the time"
        lines = []
        for c in containers:
            lines.append(f"{c.short_id} {c.name} {c.image.tags} {c.status}")
        return "\n".join(lines)
    except Exception as e:
        return f"There was an error while tring to list the containers {e}"


@mcp.tool()
def delete_container(container_name: str) -> str:
    """
    Delete a container by its name. Stops it first if it's still running.
    Args:
        container_name: Container name that should be deleted
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        container.remove(force=True)
        return f"Deleted container {container_name}"
    except Exception as e:
        return f"Failed to delete the container: {e}"


@mcp.tool()
def container_logs(container_name: str, tail: int = 200) -> str:
    """
    Collect and display the logs for a container
    Args:
        container_name: Container name to collect logs
        tail: Number of log lines to return (default 200)
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        logs = container.logs(tail=tail)
        return logs.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Failed to retrieve logs from container {container_name}: {e}"


@mcp.tool()
def container_restart(container_name: str) -> str:
    """
    Restarting a container
    Args:
        container_name: name to restart the container
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        container.restart()
        return f"Container with name {container_name} restarted with success"
    except Exception as e:
        return f"Failed to restart container {container_name}: {e}"


@mcp.tool()
def container_start(container_name: str) -> str:
    """
    Starting a container
    Args:
        container_name: name to start the container
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        container.start()
        return f"Container with name {container_name} started with success"
    except Exception as e:
        return f"Failed to start container {container_name}: {e}"


@mcp.tool()
def container_stats(container_name: str) -> str:
    """
    Shows live CPU and memory usage for a running container.
    Args:
        container_name: Docker Container name
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        cpu_percent, mem_usage, mem_limit = _container_usage(container.stats(stream=False))
        return f"{container_name}: CPU {cpu_percent:.2f}% | Memory {mem_usage:.1f}MB / {mem_limit:.1f}MB"
    except Exception as e:
        return f"Failed to get stats for container {container_name}: {e}"

@mcp.tool()
def container_inspect(container_name: str) -> str:
    """
    Returns detailed information about a container: environment variables,
    mounts, network IP, and health status. Env var values that look like
    secrets (PASSWORD, TOKEN, API_KEY, etc.) are redacted.
    Args:
        container_name: Docker Container name
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        attrs = container.attrs

        env_vars = _redact_env(attrs["Config"].get("Env", []))
        mounts = attrs.get("Mounts", [])
        mount_lines = [f"{m['Source']} -> {m['Destination']} ({m.get('Mode', '')})" for m in mounts]

        networks = attrs["NetworkSettings"].get("Networks", {})
        ip_lines = [f"{net}: {info.get('IPAddress') or 'none'}" for net, info in networks.items()]

        health = attrs["State"].get("Health", {}).get("Status", "no healthcheck configured")
        restart_count = attrs.get("RestartCount", 0)

        lines = [
            f"Status: {attrs['State'].get('Status')}",
            f"Health: {health}",
            f"Restart count: {restart_count}",
            "Networks:",
            *([f"  {l}" for l in ip_lines] or ["  none"]),
            "Mounts:",
            *([f"  {l}" for l in mount_lines] or ["  none"]),
            "Environment:",
            *([f"  {e}" for e in env_vars] or ["  none"]),
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to inspect container {container_name}: {e}"
    
@mcp.tool()
def container_exec(container_name: str, command: str) -> str:
    """
    Executes a shell command inside a running container and returns its output.
    Args:
        container_name: Docker Container name
        command: shell command to run inside the container, e.g. "ls -la /app"
    """
    try:
        client = get_client()
        container = client.containers.get(container_name)
        exit_code, output = container.exec_run(["sh", "-c", command])
        result = output.decode("utf-8", errors="replace")
        if exit_code != 0:
            return f"Command exited with code {exit_code}:\n{result}"
        return result or "(no output)"
    except Exception as e:
        return f"Failed to execute command in container {container_name}: {e}"
