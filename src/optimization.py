import re

from server import mcp
from helper import _normalize_path

_BUILD_SIGNALS = {
    "Node.js": r"npm (install|ci|run build)|yarn (install|build)",
    "Java (Maven)": r"mvn (package|install|clean)",
    "Java (Gradle)": r"gradle(w)?\s+(build|assemble)",
    "Go": r"go build",
    "Rust": r"cargo build",
    "Python (compiled deps)": r"pip install.*(-r requirements|gcc|build-essential)",
    ".NET": r"dotnet (build|publish|restore)",
    "C/C++": r"\b(make|cmake|gcc|g\+\+)\b",
}

@mcp.tool()
def analyze_multistage(dockerfile_path: str) -> str:
    """
    Analyzes a Dockerfile and reports whether it would benefit from a
    multi-stage build. Detects build-tool commands (npm install/build, mvn,
    gradle, go build, cargo build, pip install with compilers, dotnet
    build/publish, make/cmake/gcc) combined with a single-stage FROM, which
    usually means build tools and dev dependencies end up shipped in the
    final image unnecessarily — increasing image size and attack surface.

    This tool only analyzes and returns reasoning plus the raw Dockerfile
    content — it does NOT generate the rewritten Dockerfile itself. If it
    reports multi-stage as recommended, use the returned content and
    detected build system to draft a multi-stage version yourself: a
    "builder" stage that runs the build commands, and a slim runtime stage
    that only COPYs the compiled artifact from the builder stage.

    Args:
        dockerfile_path: full path to an existing Dockerfile on this machine.
                          Accepts either a Windows path ("C:\\path\\Dockerfile")
                          or a Git Bash style path ("/c/path/Dockerfile").
    """
    path = _normalize_path(dockerfile_path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return f"Failed to read Dockerfile at {path}: {e}"

    from_lines = re.findall(r"^\s*FROM\s+.+", content, re.MULTILINE | re.IGNORECASE)
    if len(from_lines) > 1:
        return f"This Dockerfile already uses multi-stage builds ({len(from_lines)} FROM stages) — no action needed."

    detected = [name for name, pattern in _BUILD_SIGNALS.items() if re.search(pattern, content, re.IGNORECASE)]
    if not detected:
        return (
            "No build-tool commands detected (npm/mvn/gradle/go/cargo/pip/dotnet/make) — "
            "this looks like a single-purpose or already-minimal Dockerfile. "
            "Multi-stage is likely not needed."
        )

    return (
        f"Single-stage Dockerfile detected with build commands for: {', '.join(detected)}.\n"
        f"Multi-stage build is RECOMMENDED — build tools/dependencies from this stage would "
        f"otherwise ship in the final image, increasing size and attack surface.\n\n"
        f"--- Current Dockerfile content ---\n{content}\n--- End content ---\n\n"
        f"Draft a multi-stage version: a 'builder' stage using the current base image to run "
        f"the build commands, and a slim runtime stage (e.g. distroless, alpine, or a "
        f"'-slim' variant) that only COPYs the final build artifact from the builder stage."
    )
