import httpx

BASE_URL = "https://mint.local/doglog"
_client = httpx.Client(base_url=BASE_URL, timeout=15)


def configure(base_url: str):
    global BASE_URL, _client
    BASE_URL = base_url
    _client = httpx.Client(base_url=BASE_URL, timeout=15)


def get(path: str, **kwargs):
    return _client.get(path, **kwargs).raise_for_status().json()


def post(path: str, **kwargs):
    return _client.post(path, **kwargs).raise_for_status().json()


def patch(path: str, **kwargs):
    return _client.patch(path, **kwargs).raise_for_status().json()


def put(path: str, **kwargs):
    return _client.put(path, **kwargs).raise_for_status().json()


def delete(path: str, **kwargs):
    return _client.delete(path, **kwargs).raise_for_status().json()
