from fastapi import FastAPI
from pydantic import BaseModel
from src.api.auth_user import AuthUser
from src.clients import walter_authenticator, walter_cw, walter_db, walter_sm
from tst.api.utils import get_auth_user_event

app = FastAPI()


class UserSignInRequest(BaseModel):
    email: str
    password: str


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/auth")
def authenticate_user(request: UserSignInRequest):
    event = get_auth_user_event(email=request.email, password=request.password)
    return (
        AuthUser(
            walter_authenticator=walter_authenticator,
            walter_cw=walter_cw,
            walter_db=walter_db,
            walter_sm=walter_sm,
        )
        .invoke(event)
        .to_json()
    )
