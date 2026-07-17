import re


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