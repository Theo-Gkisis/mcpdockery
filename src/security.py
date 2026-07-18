from server import mcp
from helper import run_trivy, _normalize_path

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

@mcp.tool()
def scan_dockerfile(dockerfile_path: str, severity: str = "CRITICAL,HIGH") -> str:
    """
    Scans a Dockerfile for security misconfigurations using Trivy's config
    scanner — BEFORE the image is even built. Flags things like: missing
    USER directive (container would run as root), use of the "latest" tag,
    hardcoded secrets in ENV/ARG, missing HEALTHCHECK, and use of ADD instead
    of COPY. Requires the `trivy` CLI installed and on PATH (https://trivy.dev).

    Args:
        dockerfile_path: full path to an existing Dockerfile on this machine.
                          Accepts either a Windows path ("C:\\path\\Dockerfile")
                          or a Git Bash style path ("/c/path/Dockerfile").
        severity: comma-separated severities to include (default "CRITICAL,HIGH")
    """
    path = _normalize_path(dockerfile_path)
    return run_trivy("config", "--severity", severity, "--format", "table", path)