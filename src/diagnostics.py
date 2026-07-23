from server import mcp
from docker_client import get_client
from helper import _container_usage

_SENSITIVE_PORTS = {
    "5432": "PostgreSQL",
    "3306": "MySQL/MariaDB",
    "1433": "MSSQL",
    "6379": "Redis",
    "27017": "MongoDB",
    "9200": "Elasticsearch",
    "5984": "CouchDB",
    "11211": "Memcached",
    "9092": "Kafka",
    "2375": "Docker daemon API (unencrypted)",
    "2376": "Docker daemon API (TLS)",
    "2379": "etcd",
    "8500": "Consul",
    "9000": "Portainer/admin panel",
    "5601": "Kibana",
    "15672": "RabbitMQ management",
}

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


@mcp.tool()
def check_exposed_ports() -> str:
    """
    Scans all running containers' published port bindings and flags anything
    worth a second look: known database/admin-panel ports (Postgres, MySQL,
    Redis, MongoDB, Elasticsearch, the Docker daemon API, etc.) and any port
    bound to 0.0.0.0/all interfaces rather than localhost. Meant to catch
    services that ended up reachable from the network when they were only
    meant for local access. Does not distinguish trusted vs. untrusted
    networks — a flagged binding may be fine on an isolated host, so review
    findings in context.
    """
    client = get_client()
    try:
        containers = client.containers.list()
    except Exception as e:
        return f"Failed to list containers: {e}"

    if not containers:
        return "No running containers."

    findings = []
    for c in containers:
        ports = c.attrs.get("NetworkSettings", {}).get("Ports") or {}
        for container_port, bindings in ports.items():
            if not bindings:
                continue
            port_num = container_port.split("/")[0]
            service = _SENSITIVE_PORTS.get(port_num)
            for binding in bindings:
                host_ip = binding.get("HostIp") or "0.0.0.0"
                host_port = binding.get("HostPort")
                exposed_all = host_ip in ("0.0.0.0", "::")

                if service and exposed_all:
                    findings.append(
                        f"{c.name}: {service} (port {port_num}) exposed on "
                        f"{host_ip}:{host_port} — reachable from any network interface"
                    )
                elif service:
                    findings.append(
                        f"{c.name}: {service} (port {port_num}) published to {host_ip}:{host_port}"
                    )
                elif exposed_all:
                    findings.append(
                        f"{c.name}: port {port_num} exposed on all interfaces ({host_ip}:{host_port})"
                    )

    if not findings:
        return f"Checked {len(containers)} running container(s) — no sensitive or broadly-exposed ports found."
    return "\n".join(findings)
