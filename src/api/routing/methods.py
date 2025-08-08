from enum import Enum


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

    @classmethod
    def from_string(cls, method: str):
        for method_enum in cls:
            if method_enum.value.lower() == method.lower():
                return method_enum
        raise ValueError(f"{method} is not a valid HTTP method!")
