from enum import Enum


class Status(Enum):
    """
    The status of the API response.
    """

    SUCCESS = "Success"
    FAILURE = "Failure"

    @staticmethod
    def from_string(status: str):
        for status_enum in Status:
            if status_enum.value.lower() == status.lower():
                return status_enum
        raise ValueError(f"{status} is not a valid status!")


class HTTPStatus(Enum):
    """
    The HTTP status of the API response.

    For more information, see https://developer.mozilla.org/en-US/docs/Web/HTTP/Status.
    """

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500

    def is_success(self) -> bool:
        return str(self.value).startswith("2")
