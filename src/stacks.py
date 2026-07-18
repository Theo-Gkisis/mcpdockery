import os
import tempfile

from server import mcp
from compose_client import run_compose

@mcp.tool()
def deploy_stack(project_name: str, compose_yaml: str) -> str:
    """
    Deploys a multi-container application from a docker-compose YAML definition.
    Args:
        project_name: unique name for this stack, used to group/manage its containers
        compose_yaml: full contents of a docker-compose.yml describing the services
    """
    fd, path = tempfile.mkstemp(suffix=".yml")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(compose_yaml)
        return run_compose("-p", project_name, "-f", path, "up", "-d")
    except Exception as e:
        return f"Failed to deploy stack {project_name}: {e}"
    finally:
        os.remove(path)
        
@mcp.tool()
def stop_stack(project_name: str) -> str:
    """
    Stops all containers in a compose stack without removing them, so it can be started again later.
    Args:
        project_name: unique name for this stack, used to group/manage its containers
    """
    try:
        return run_compose("-p", project_name, "stop")
    except Exception as e:
        return f"Failed to stop stack: {e}"

@mcp.tool()
def remove_stack(project_name: str) -> str:
    """
    Stops and permanently removes a compose stack: containers, networks, and volumes (data is deleted).
    Args:
        project_name: unique name for this stack, used to group/manage its containers
    """
    try:
        return run_compose("-p", project_name, "down", "-v")
    except Exception as e:
        return f"Failed to remove stack: {e}"
    
@mcp.tool()
def list_stacks() -> str:
    """
    Lists all compose projects, including stopped ones
    """
    try:
        return run_compose("ls", "-a")
    except Exception as e:
        return f"Failed to list stacks: {e}"
    
@mcp.tool()
def stack_status(project_name: str) -> str:
    """
    Shows the status of all containers in a compose stack (like docker compose ps).
    Args:
        project_name: unique name for this stack, used to group/manage its containers
    """
    try:
        return run_compose("-p", project_name, "ps")
    except Exception as e:
        return f"Failed to get status for stack {project_name}: {e}"


@mcp.tool()
def stack_logs(project_name: str, tail: int = 200) -> str:
    """
    Collects logs from all containers in a compose stack.
    Args:
        project_name: unique name for this stack, used to group/manage its containers
        tail: number of log lines to return per container (default 200)
    """
    try:
        return run_compose("-p", project_name, "logs", "--tail", str(tail))
    except Exception as e:
        return f"Failed to get logs for stack {project_name}: {e}"