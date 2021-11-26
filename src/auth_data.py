from anjeg.database import Connector


MODEL = {
    "account": {
        "uuid": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "pseudo": "TEXT NOT NULL UNIQUE",
        "password": "TEXT NOT NULL",
        "mail": "TEXT",
        "token": "CHAR(16)"
    }

}

CONN = Connector("authentifier", MODEL)


# #############################################################################
# Database simple access
# #############################################################################

def verify_account(pseudo: str, password: str):
    """
    Verify if there is an account with a given password in the database

    :param pseudo: User's pseudo
    :param password: User's password
    :return: User's uuid & token if the verification succeed
    """

    return CONN.execute(f"SELECT uuid,token FROM account WHERE {pseudo=} AND {password=}")


def create_account(pseudo: str, password: str):
    """
    Create a new account in the database

    :param pseudo: User's pseudo
    :param password: User's password
    :return:
    """

    return CONN.execute(f"INSERT INTO account(pseudo,password) VALUES('{pseudo}','{password}')")


def set_token(uuid: int, token: str):
    """
    Set a new token for the user

    :param uuid: User's uuid
    :param token: User's new token
    :return:
    """

    return CONN.execute(f"UPDATE account SET {token=} WHERE {uuid=}")
