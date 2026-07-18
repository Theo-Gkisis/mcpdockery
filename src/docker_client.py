import docker
_client: docker.DockerClient | None = None

def get_client():
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client
