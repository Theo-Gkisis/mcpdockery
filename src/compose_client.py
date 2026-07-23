import subprocess

def run_compose(*args: str, timeout: int = 120) -> str:
    try:
        results = subprocess.run(
            ["docker", "compose", *args],
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Error: docker compose timed out after {timeout}s"
    if results.returncode != 0:
        return f"Error: {results.stderr.strip()}"
    return results.stdout.strip() or "Done."