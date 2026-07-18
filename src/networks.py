from server import mcp
from docker_client import get_client

@mcp.tool()
def list_networks() -> str:
    """
    Lists all Docker networks with their driver and scope
    """
    try:
        client = get_client()
        networks = client.networks.list()
        if not networks:
            return "No networks found"
        lines = []
        for n in networks:
            lines.append(f"{n.short_id} {n.name} {n.attrs.get('Driver')} {n.attrs.get('Scope')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list networks: {e}"

@mcp.tool()
def create_network(network_name: str, driver: str = "bridge") -> str:
    """
    Creates a new Docker network.
    Args:
        network_name: name to give the new network
        driver: network driver to use, e.g. "bridge" (default), "overlay" (swarm), "macvlan"
    """
    try:
        client = get_client()
        network = client.networks.create(name=network_name, driver=driver)
        return f"Created network {network.name} ({network.short_id}, driver: {driver})"
    except Exception as e:
        return f"Failed to create network {network_name}: {e}"
