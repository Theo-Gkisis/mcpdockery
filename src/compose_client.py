import subprocess

def run_compose(*args:str) -> str:
    results = subprocess.run(
        ["docker", "compose", *args],
        text=True,
        capture_output=True
        )
    if results.returncode != 0 :
         return f"Error: {results.stderr.strip()}"
    return results.stdout.strip() or "Done."