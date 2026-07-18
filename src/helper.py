import re
import subprocess


def _normalize_path(path: str) -> str:
    match = re.match(r"^/([a-zA-Z])/(.*)", path)
    if match:
        drive, rest = match.groups()
        return f"{drive.upper()}:\\{rest.replace('/', '\\\\')}"
    return path


def _split_tag(image: str, default_tag: str) -> tuple[str, str]:
    last_segment = image.split("/")[-1]
    if ":" in last_segment:
        repository, tag = image.rsplit(":", 1)
        return repository, tag
    return image, default_tag

def _container_usage(stats: dict) -> tuple[float, float, float]:
    """Returns (cpu_percent, mem_usage_mb, mem_limit_mb) from a Docker stats() dict."""
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
    num_cpus = stats["cpu_stats"].get("online_cpus", 1)
    cpu_percent = 0.0
    if system_delta > 0 and cpu_delta > 0:
        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

    mem_usage_mb = stats["memory_stats"].get("usage", 0) / (1024 * 1024)
    mem_limit_mb = stats["memory_stats"].get("limit", 0) / (1024 * 1024)
    return cpu_percent, mem_usage_mb, mem_limit_mb


def run_trivy(*args:str) -> str:
    result = subprocess.run(
        ["trivy",*args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip() or "Done."