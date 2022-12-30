from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse, unquote
from http.client import responses


SERVER_NAME = "EPOLL"
DEFAULT_CONNECTION_VAL = "close"

    
@dataclass
class HTTPRequest:
    raw_requestline: str
    method: str
    path: str
    query_params: dict
    headers: dict


@dataclass
class HTTPResponse:
    request: HTTPRequest

    def build_response(self, directory_root):
        full_path = Path(f"./{directory_root}{self.request.path}")

        response_code = None
        resp_data = b""

        if full_path.absolute() != full_path.resolve():  # remove escape from the root directory ../../
            response_code = 403

        elif self.request.method not in {"GET", "HEAD"}:
            response_code = 405

        elif full_path.is_file() and self.request.path.endswith("/"):
            response_code = 404

        else:
            if full_path.is_dir():
                full_path = full_path/"index.html"

            if full_path.exists():  # migth be existing file but ending with trail slash
                resp_data = full_path.read_bytes()
                response_code = 200
            else:
                response_code = 404

        headers = self.build_headers(full_path, resp_data)
        message = self.get_message(response_code)
    
        resp_line = f"HTTP/1.1 {response_code} {message}\r\n{headers}\r\n\r\n"
        if self.request.method == "GET":
            return bytes(resp_line, "utf-8") + resp_data
        else:
            return bytes(resp_line, "utf-8")

    def build_headers(self, path: Path, data: bytes) -> dict:
        headers = {}
        if path:
            headers["Content-Type"] = self.build_content_type(path.absolute())
            # print("Contenttype", headers["Content-Type"])
        headers["Content-Length"] = len(data)
        headers["Date"] = self.date_header
        headers["Server"] = self.server_header

        return "\r\n".join(f"{head_name}: {head_val}" for head_name, head_val in headers.items())

    def build_content_type(self, url: str) -> str:
        import mimetypes
        return mimetypes.guess_type(url)[0]

    @property
    def date_header(self):
        return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    @property
    def server_header(self):
        return SERVER_NAME

    def connection_header(self):
        return DEFAULT_CONNECTION_VAL

    def get_message(self, code: int) -> str:
        return responses[code]



def parse_request(req_data: bytearray) -> HTTPRequest:
    splitted_req_data = req_data.decode("utf-8").replace("\r\n\r\n", "").split("\r\n")
    search_result = re.search("(?P<name>[^\s]+)\s*(?P<req_line>[^\s]+)\s*", splitted_req_data[0])

    headers = {}
    for item in splitted_req_data[1:]:
        splitted_header = item.split(":", 1)
        headers[splitted_header[0]] = splitted_header[1]

    parsed_url = urlparse(search_result.group("req_line"))

    return HTTPRequest(
        method=search_result.group("name"),
        raw_requestline=splitted_req_data[0],
        path=unquote(parsed_url.path), # get rid of %20
        query_params=parse_qs(parsed_url.query),
        headers=headers
    )
