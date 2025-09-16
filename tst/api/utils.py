import json
from typing import Optional

from src.api.common.methods import HTTPStatus, Status
from src.api.common.models import Response
from src.api.routing.methods import HTTPMethod
from src.environment import Domain

UNIT_TEST_REQUEST_ID = "WALTER_BACKEND_UNIT_TEST_REQUEST_ID"
"""(str): Request ID used for unit testing."""


def get_api_event(
    path: str,
    http_method: HTTPMethod,
    token: Optional[str] = None,
    body: Optional[dict] = None,
    query: Optional[dict] = None,
) -> dict:
    """
    Creates an API Gateway event object to simulate a request for testing.

    This function constructs a dictionary representing an event typically provided
    by API Gateway in a serverless AWS Lambda context. It includes details such as
    the HTTP method, path, query parameters, authorization headers, and the request
    body if applicable.

    Args:
        path (str): The endpoint path of the API request.
        http_method (HTTPMethod): The HTTP method (e.g., GET, POST) for the API
            request.
        token (Optional[str]): Optional Bearer token for authorization. Default is
            None.
        body (Optional[dict]): Optional dictionary representing the request body.
            Default is None.
        query (Optional[dict]): Optional dictionary of query string parameters.
            Default is None.

    Returns:
        dict: A dictionary representation of the API Gateway event.
    """
    # create core event
    event = {
        "path": path,
        "httpMethod": http_method.value,
        "queryStringParameters": query,
    }

    # add auth headers if provided
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # add body if provided
    if body is not None:
        headers["content-type"] = "application/json"
        event["body"] = json.dumps(body)
    else:
        event["body"] = None

    if len(headers) > 0:
        event["headers"] = headers

    return event


def get_expected_response(
    api_name: str,
    status_code: HTTPStatus,
    status: Status,
    message: str,
    data: str = None,
) -> Response:
    """
    Generates a standardized response object for a given API, including relevant metadata
    and optional data content. This function encapsulates the domain, status, and message
    information within a structured `Response` object.

    Args:
        api_name (str): Name of the API invoking the response.
        status_code (HTTPStatus): HTTP status code representing the response's outcome.
        status (Status): Status object reflecting the operation's execution state.
        message (str): Message providing contextual details about the response.
        data (str, optional): Additional data or payload to include in the response
            if applicable. Defaults to None.

    Returns:
        Response: A structured response object containing all provided metadata and
        optional data.
    """
    return Response(
        domain=Domain.TESTING,
        api_name=api_name,
        request_id=UNIT_TEST_REQUEST_ID,
        http_status=status_code,
        status=status,
        message=message,
        data=data,
    )
