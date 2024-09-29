from src.database.users.models import User

USERS = [User(email="walteraifinancialadvisor@gmail.com", username="walter")]


def test_get_users(users_table) -> None:
    users = users_table.get_users()
    assert set(users) == set(USERS)
