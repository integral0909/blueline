"""A client for talking to the application without a socket.

The tests were written against a framework's test client, and taking the
framework out takes that with it. wsgiref has one already in everything but
name: a wsgi application is a function, so calling it is the whole of what a
test client does. This puts a readable face on it.

Only what the tests actually use is here: the four verbs, a json body, query
parameters, and a response that can be asked for its status, its headers and
its decoded body.
"""

from __future__ import annotations

import io
import json
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode


class Reply:
    """What came back."""

    def __init__(self, status: str, headers: List[Tuple[str, str]], body: bytes) -> None:
        self.status = status
        self.status_code = int(status.split(" ")[0])
        self.headers = {name.lower(): value for name, value in headers}
        self.content = body

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")

    def json(self) -> Any:
        return json.loads(self.text) if self.content else None

    def __repr__(self) -> str:
        return f"<Reply {self.status_code}>"


class Client:
    """Calls a wsgi application the way a caller over http would."""

    def __init__(self, application: Any) -> None:
        self.application = application
        #: What the application is underneath, for a test that wants to look.
        self.app = application

    def request(
        self,
        method: str,
        path: str,
        json_body: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Reply:
        body = b"" if json_body is None else json.dumps(json_body).encode("utf-8")
        # Not quoted. A wsgi server decodes the path before it puts it in
        # PATH_INFO, so a title with a space in it arrives here as a space.
        environ: Dict[str, Any] = {
            "REQUEST_METHOD": method.upper(),
            "PATH_INFO": path,
            "QUERY_STRING": urlencode(
                {key: value for key, value in (params or {}).items() if value is not None},
                doseq=True,
            ),
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "REMOTE_ADDR": "127.0.0.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(body),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "CONTENT_LENGTH": str(len(body)),
            "CONTENT_TYPE": "application/json",
        }
        for name, value in (headers or {}).items():
            environ["HTTP_" + name.upper().replace("-", "_")] = value

        caught: Dict[str, Any] = {}

        def start_response(status: str, response_headers: List[Tuple[str, str]], *rest: Any) -> Any:
            caught["status"] = status
            caught["headers"] = response_headers
            return lambda chunk: None

        chunks = self.application(environ, start_response)
        return Reply(caught["status"], caught["headers"], b"".join(chunks))

    def get(self, path: str, **kwargs: Any) -> Reply:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json: Any = None, **kwargs: Any) -> Reply:
        return self.request("POST", path, json_body=json, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Reply:
        return self.request("DELETE", path, **kwargs)

    def put(self, path: str, json: Any = None, **kwargs: Any) -> Reply:
        return self.request("PUT", path, json_body=json, **kwargs)
