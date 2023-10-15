import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class AuthClient:
    def __init__(self, auth_endpoint: str, authorized_key: str, **kwds: Any) -> None:
        self.auth_endpoint = auth_endpoint
        self.base_endpoint = kwds.get("base_endpoint", None)
        if self.base_endpoint is not None:
            self.auth_endpoint = f"{kwds.get('base_endpoint')}{auth_endpoint}"

        self.authorized_key = authorized_key
        self.state = None

    def __call__(self, id: Any, password: str, **kwds: Any) -> Any:
        self._get_auth_url()
        if self.state is None:
            raise ValueError("")

        r = requests.get(
            f"{self.auth_endpoint}?code=dummycode&state={self.state}&user_id={id}"
        )
        r.raise_for_status()

        try:
            key = r.json()[self.authorized_key]
        except Exception as e:
            logger.error(f"Not found key of {self.authorized_key}")
            raise e
        else:
            return key

    def _get_auth_url(self):
        r = requests.get(f"{self.base_endpoint}/auth/url")
        r.raise_for_status()
        self.state = r.json().get("state", None)


if __name__ == "__main__":
    pass
