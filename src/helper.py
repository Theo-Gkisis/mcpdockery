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

_SECRET_ENV_KEY = re.compile(
    r"(SECRET|PASSWORD|PASSWD|PWD|TOKEN|API[_-]?KEY|PRIVATE[_-]?KEY|"
    r"ACCESS[_-]?KEY|CREDENTIAL|AUTH|CONN(ECTION)?[_-]?STRING|DSN)",
    re.IGNORECASE,
)


def _redact_env(env_vars: list[str]) -> list[str]:
    """Masks values of env vars whose key looks secret-shaped (PASSWORD,
    TOKEN, API_KEY, etc.) so they don't get echoed verbatim into the model's
    context. Keys that don't match are returned unchanged."""
    redacted = []
    for entry in env_vars:
        key, sep, value = entry.partition("=")
        if sep and _SECRET_ENV_KEY.search(key):
            redacted.append(f"{key}=***REDACTED***")
        else:
            redacted.append(entry)
    return redacted


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


def run_trivy(*args: str, timeout: int = 300) -> str:
    try:
        result = subprocess.run(
            ["trivy", *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Error: trivy timed out after {timeout}s"
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip() or "Done."


def run_hadolint(*args: str, timeout: int = 30) -> str:
    """Hadolint exits 1 when it finds lint issues, so a non-zero code isn't
    itself an error — only treat it as one if there's no stdout to show."""
    try:
        result = subprocess.run(
            ["hadolint", *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Error: hadolint timed out after {timeout}s"
    if result.stdout.strip():
        return result.stdout.strip()
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return "No issues found."