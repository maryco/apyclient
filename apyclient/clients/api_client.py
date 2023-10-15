import json
import logging

import requests

from .auth_client import AuthClient

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(
        self,
        endpoint: str,
        account: dict,
        *,
        should_autorize=False,
        auth: AuthClient,
        **kwds,
    ) -> None:
        self.endpoint = endpoint
        self.actor = account
        if should_autorize:
            auth_key = auth(id=account["id"], password=account["password"])
            self.headers = {"Authorization": "Bearer {}".format(auth_key)}
        else:
            self.headers = None

    def execute(self, method: str, path: str, in_path: dict, body: dict):
        path = self._embedded_path(path, in_path)

        try:
            getattr(self, f"_request_{method}")(
                path=f"{self.endpoint}{path}", body=body
            )
        except Exception as e:
            logger.error("Error")
            raise e

    def _request_get(self, path: str, **kwds):
        r = requests.get(path, headers=self.headers)
        if r.status_code != requests.codes.ok:
            print(f"Error url:{r.url} code:{r.status_code}")

    def _request_post(self, path: str, **kwds):
        r = requests.post(
            path,
            headers=self.headers,
            json=kwds.get("body"),
        )
        return r.json()

    def _request_put(self, path: str, **kwds):
        r = requests.put(
            path,
            headers=self.headers,
            json=kwds.get("body"),
        )
        return r.json()

    def _request_delete(self, path: str, **kwds):
        r = requests.delete(path, headers=self.headers)
        if r.status_code != requests.codes.ok:
            print(f"Error url:{r.url} code:{r.status_code}")

    def _embedded_path(self, path: str, in_path: dict) -> str:
        if in_path is None:
            return path

        for key, value in in_path.items():
            path = path.replace(f"{{{key}}}", value)

        return path


if __name__ == "__main__":
    pass
