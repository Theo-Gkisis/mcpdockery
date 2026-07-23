from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "mcpdockery",
    instructions=(
        "This server runs locally on the user's own machine, as a separate "
        "process from your own sandboxed code-execution environment. It has "
        "real access to the user's local Docker daemon and to filesystem "
        "paths passed as tool arguments (including Windows paths like "
        "\"C:\\Users\\...\"). Do not refuse a request or claim you lack "
        "filesystem access just because a path looks local — call the "
        "relevant tool instead; it runs on the user's machine, not in your "
        "sandbox.\n\n"
        "For Dockerfile review requests: use `audit_dockerfile` by default "
        "(security misconfigurations + best-practice findings + raw file "
        "content, so you can also draft a corrected version). Only use the "
        "narrower `scan_dockerfile` (security only) or `lint_dockerfile` "
        "(style only) when the user explicitly asks for one specifically."
    ),
)
