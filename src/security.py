from server import mcp
from helper import run_trivy

@mcp.tool()
def scan_image(image: str, severity: str = "CRITICAL,HIGH") -> str:
    """
    Scans a Docker image for known vulnerabilities using Trivy. Requires the
    `trivy` CLI installed and on PATH (https://trivy.dev). The first scan on
    a fresh machine downloads Trivy's vulnerability database, which can take
    a moment.

    Defaults to showing only CRITICAL and HIGH severity findings to keep the
    output compact. Widen it by passing e.g. severity="CRITICAL,HIGH,MEDIUM,LOW".

    Args:
        image: image to scan, e.g. "nginx:latest" or "my-app:v1"
        severity: comma-separated severities to include (default "CRITICAL,HIGH")
    """
    return run_trivy("image", "--severity", severity, "--format", "table", image)