import httpx


def build_async_client(base_url: str, timeout: float = 30.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=timeout)

