from src.api.routing.router import APIRouter
from src.factory import CLIENT_FACTORY

API_ROUTER: APIRouter = APIRouter(client_factory=CLIENT_FACTORY)
"""(APIRouter): The API router used to route API Gateway requests to the API function and appropriate execution method."""
