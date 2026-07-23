from server import mcp
from helper import run_trivy, run_hadolint, _normalize_path

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
def generate_sbom(image: str, format: str = "cyclonedx") -> str:
    """
    Generates a Software Bill of Materials (SBOM) for a Docker image using
    Trivy — a full inventory of every OS package and language dependency the
    image contains. Useful for supply-chain compliance, license audits, and
    tracking exposure when a new CVE is disclosed (search the SBOM instead of
    re-scanning). Requires the `trivy` CLI installed and on PATH
    (https://trivy.dev).

    Args:
        image: image to generate an SBOM for, e.g. "nginx:latest" or "my-app:v1"
        format: SBOM format, "cyclonedx" (default) or "spdx-json"
    """
    if format not in ("cyclonedx", "spdx-json"):
        return f"Unsupported format '{format}' — use 'cyclonedx' or 'spdx-json'"
    return run_trivy("image", "--format", format, image)

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

@mcp.tool()
def lint_dockerfile(dockerfile_path: str) -> str:
    """
    Lints a Dockerfile with Hadolint for best-practice and style issues —
    unpinned package/base image versions, missing --no-install-recommends,
    use of ADD instead of COPY, sudo usage, missing WORKDIR before relative
    paths, and similar. Complements `scan_dockerfile` (Trivy), which focuses
    on security misconfigurations rather than style/best-practice rules.
    Requires the `hadolint` CLI installed and on PATH
    (https://github.com/hadolint/hadolint).

    Args:
        dockerfile_path: full path to an existing Dockerfile on this machine.
                          Accepts either a Windows path ("C:\\path\\Dockerfile")
                          or a Git Bash style path ("/c/path/Dockerfile").
    """
    path = _normalize_path(dockerfile_path)
    return run_hadolint("--no-color", path)

@mcp.tool()
def audit_dockerfile(dockerfile_path: str, severity: str = "CRITICAL,HIGH") -> str:
    """
    Runs a full pre-build Dockerfile audit: Trivy's security misconfiguration
    scan plus Hadolint's best-practice/style lint, combined into one report,
    plus the raw Dockerfile content. Use this for a general "check/review/audit
    my Dockerfile" request when the user hasn't specified security vs. style
    specifically. For a narrower, single-tool check, use `scan_dockerfile`
    (security only) or `lint_dockerfile` (style only) instead — those return
    findings only, not the raw content, so they're cheaper when a rewrite
    isn't needed.
    Requires both `trivy` (https://trivy.dev) and `hadolint`
    (https://github.com/hadolint/hadolint) installed and on PATH.

    Args:
        dockerfile_path: full path to an existing Dockerfile on this machine.
                          Accepts either a Windows path ("C:\\path\\Dockerfile")
                          or a Git Bash style path ("/c/path/Dockerfile").
        severity: comma-separated Trivy severities to include (default "CRITICAL,HIGH")
    """
    path = _normalize_path(dockerfile_path)
    trivy_report = run_trivy("config", "--severity", severity, "--format", "table", path)
    hadolint_report = run_hadolint("--no-color", path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        content = f"(failed to read file for content: {e})"
    return (
        f"=== Security misconfigurations (Trivy) ===\n{trivy_report}\n\n"
        f"=== Best practices (Hadolint) ===\n{hadolint_report}\n\n"
        f"--- Original Dockerfile content ---\n{content}\n--- End content ---\n\n"
        f"Using the findings above, draft a corrected/recommended version of this Dockerfile."
    )