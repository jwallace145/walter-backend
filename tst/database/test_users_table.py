from src.database.users.models import User

#########
# USERS #
#########

USERS = [
    User(email="walter@gmail.com", username="walter"),
    User(email="walrus@gmail.com", username="walrus"),
]

#########
# TESTS #
#########


def test_get_users(users_table) -> None:
    users = users_table.get_users()
    assert set(users) == set(USERS)
