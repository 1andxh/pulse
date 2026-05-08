from urllib.parse import urlparse, urlunparse


def normalize_public_url(v: str | None) -> str:
    if not v or not v.strip():
        return ""

    v = v.strip()
    if not v.startswith(("http://", "https://")):
        v = f"https://{v}"

    parsed = urlparse(v)
    if not parsed.netloc:
        return ""

    path = parsed.path if parsed.path not in ["/", ""] else ""

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
