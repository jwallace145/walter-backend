def test_get_users(users_table) -> None:
    users = users_table.get_users()
    assert len(users) == 1
    assert users[0].email == "walteraifinancialadvisor@gmail.com"
    assert users[0].username == "walter"
