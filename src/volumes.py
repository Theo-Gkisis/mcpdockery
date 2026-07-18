from server import mcp
from docker_client import get_client

@mcp.tool()
def list_volumes() -> str:
    """
    Lists all Docker volumes with their driver and mountpoint
    """
    try:
        client = get_client()
        volumes = client.volumes.list()
        if not volumes:
            return "No volumes found"
        lines = []
        for v in volumes:
            lines.append(f"{v.name} {v.attrs.get('Driver')} {v.attrs.get('Mountpoint')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list volumes: {e}"
    

@mcp.tool()
def remove_volume(volume_name: str) -> str:
    """
    Deletes a Docker volume by name. Data stored in it is permanently lost.
    Fails if the volume is currently in use by a container.
    Args:
        volume_name: name of the volume to remove
    """
    try:
        client = get_client()
        volume = client.volumes.get(volume_name)
        volume.remove()
        return f"Removed volume {volume_name}"
    except Exception as e:
        return f"Failed to remove volume {volume_name}: {e}"


@mcp.tool()
def create_volume(volume_name: str, driver: str = "local") -> str:
    """
    Creates a new Docker volume.
    Args:
        volume_name: name to give the new volume
        driver: volume driver to use (default "local")
    """
    try:
        client = get_client()
        volume = client.volumes.create(name=volume_name, driver=driver)
        return f"Created volume {volume.name} (driver: {volume.attrs.get('Driver')})"
    except Exception as e:
        return f"Failed to create volume {volume_name}: {e}"