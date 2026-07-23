from server import mcp
from docker_client import get_client
from helper import _container_usage

@mcp.tool()
def docker_doctor(cpu_threshold: float = 80.0, mem_threshold: float = 80.0) -> str:
    """
    Scans every container and reports only the ones that need attention:
    OOM kills, restart loops, unhealthy health checks, crashed containers,
    or high CPU/memory usage. Returns a clean-bill-of-health message if
    nothing is flagged — use this instead of checking containers one by one.

    Args:
        cpu_threshold: CPU %% above which a running container is flagged (default 80.0)
        mem_threshold: memory %% of its limit above which a container is flagged (default 80.0)
    """
    client = get_client()
    try:
        containers = client.containers.list(all=True)
    except Exception as e:
        return f"Failed to list containers: {e}"

    if not containers:
        return "No containers found."

    issues = []
    for c in containers:
        try:
            state = c.attrs.get("State", {})

            if state.get("OOMKilled"):
                issues.append(f"{c.name}: killed by OOM (out of memory)")

            restart_count = c.attrs.get("RestartCount", 0)
            if restart_count > 0:
                issues.append(f"{c.name}: restarted {restart_count} time(s) — possible crash loop")

            health = state.get("Health", {}).get("Status")
            if health and health != "healthy":
                issues.append(f"{c.name}: health check status is '{health}'")

            if state.get("Status") == "exited" and state.get("ExitCode", 0) != 0:
                issues.append(f"{c.name}: exited with code {state.get('ExitCode')}")

            if state.get("Status") == "running":
                cpu_percent, mem_usage, mem_limit = _container_usage(c.stats(stream=False))
                mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0
                if cpu_percent > cpu_threshold:
                    issues.append(f"{c.name}: high CPU usage ({cpu_percent:.1f}%)")
                if mem_percent > mem_threshold:
                    issues.append(f"{c.name}: high memory usage ({mem_percent:.1f}% of limit)")
        except Exception as e:
            issues.append(f"{c.name}: failed to inspect ({e})")

    if not issues:
        return f"All {len(containers)} containers look healthy."
    return "\n".join(issues)
