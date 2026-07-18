from server import mcp
from docker_client import get_client
from helper import _split_tag , _normalize_path
import os

@mcp.tool()
def list_images() -> str:
    """
    Lists all local Docker images, including untagged/intermediate ones.
    Each line shows: short ID, tags, and size in MB.
    """

    client = get_client()
    try:
        images = client.images.list(all=True)
        if not images:
            return f"No Images found"
        lines = []
        for img in images:
            size_mb = img.attrs["Size"] / (1024 * 1024)
            lines.append(f"{img.short_id} {img.tags} {size_mb:.1f}MB")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list Docker images: {e}"


@mcp.tool()
def pull_image(image: str, tag: str = "alpine", platform: str | None = None) -> str:
    """
    Pulls a Docker image from a registry (Docker Hub, ECR, GCR, etc.) without
    running it. Requires prior `docker login` if the registry needs auth —
    this tool does not accept credentials.

    Defaults to the "alpine" tag (smaller, faster to pull) when no tag is
    specified. Only pass a different tag (e.g. "latest" or a specific
    version) if the user explicitly asks for the full/standard image —
    not every image publishes an "alpine" variant, in which case the pull
    will fail and you should retry with "latest".

    Args:
        image: repository name, e.g. "nginx" or "myregistry.com:5000/my-app".
               Can include a tag directly (e.g. "nginx:1.27"), in which case
               the `tag` argument is ignored.
        tag: tag to pull if not already included in `image` (default "alpine")
        platform: optional, e.g. "linux/amd64" or "linux/arm64" — force a
                  specific architecture on multi-arch images
    """
    repository, image_tag = _split_tag(image, tag)
    client = get_client()
    try:
        errors = []
        for chunk in client.api.pull(repository, tag=image_tag, platform=platform, stream=True, decode=True):
            if "error" in chunk:
                errors.append(chunk["error"])
        if errors:
            return f"Failed to pull {repository}:{image_tag}: {'; '.join(errors)}"

        img = client.images.get(f"{repository}:{image_tag}")
        size_mb = img.attrs["Size"] / (1024 * 1024)
        return f"Pulled {repository}:{image_tag} ({img.short_id}, {size_mb:.1f}MB)"
    except Exception as e:
        return f"Failed to pull {repository}:{image_tag}: {e}"

@mcp.tool()
def delete_image(image_name:str) -> str:
    """
    Delete a Docker image by tag or ID. Removed even if still referenced by a stopped container (force).
    Args:
        image_name: image name to be deleted
    """
    client = get_client()
    try:
        client.images.remove(image_name, force=True)
        return f"Removed image {image_name}"
    except Exception as e:
        return f"Failed to delete Docker images: {e}"
    
@mcp.tool()
def build_image(image_tag: str, dockerfile_path: str) -> str:
    """
    Builds a Docker image from a Dockerfile already saved on disk. The build
    context is the folder containing the Dockerfile, so COPY/ADD of other files
    in that same folder works normally. Accepts either a Windows path
    ("C:\\path\\Dockerfile") or a Git Bash style path ("/c/path/Dockerfile").
    Args:
        image_tag: tag to give the built image, e.g. "my-app:latest"
        dockerfile_path: full path to an existing Dockerfile on this machine
    """
    client = get_client()
    try:
        dockerfile_path = _normalize_path(dockerfile_path)
        build_dir = os.path.dirname(dockerfile_path)
        image, _logs = client.images.build(
            path=build_dir,
            dockerfile=os.path.basename(dockerfile_path),
            tag=image_tag,
        )
        return f"Built image {image.tags} ({image.short_id})"
    except Exception as e:
        return f"Failed to build image {image_tag}: {e}"

@mcp.tool()
def push_image(local_image: str, repository:str,  image_tag: str = "latest") -> str:
    """
    Tags a local Docker image with a registry repository name and pushes it
    (e.g. Docker Hub, AWS ECR). Requires that you have already run `docker login`
    locally — this tool does not accept credentials.
    Args:
        local_image: the image currently on your machine, e.g. "my-app:latest"
        repository: full destination repository name, e.g. "myusername/my-app"
                    or "123456789012.dkr.ecr.eu-west-1.amazonaws.com/my-app"
        image_tag: tag to push, e.g. "latest" or "v1.0"
    """
    client = get_client()
    try:
        image = client.images.get(local_image)
        image.tag(repository, image_tag)

        errors = []
        for chunk in client.images.push(repository, tag=image_tag, stream=True, decode=True):
            if "error" in chunk:
                errors.append(chunk["error"])
        if errors:
            return f"Failed to push {repository}:{image_tag}: {'; '.join(errors)}"
        return f"Pushed {repository}:{image_tag}"
    except Exception as e:
        return f"Failed to push {repository}:{image_tag}: {e}"
