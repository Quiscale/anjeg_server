from anjeg.parser import Parser
from anjeg.server import Client, DataError
from anjeg.logger import Logger, ERROR
import auth_data as db
from typing import Tuple, Dict

LOGGER = Logger("path")
PARSER = Parser()


@PARSER.LOG("/log")
def log(client: Client, token: str, pseudo: str, password: str, seed: str) -> Tuple[str, Dict]:
    """
    Handle the connection of a client

    :param client: The client which connects
    :param token: The client connection token
    :param pseudo: The mail which is used to connect the client
    :param password: The password which is used to connect the client
    :param seed: Connection seed
    :return: A json with the client uuid
    """
    try:

        if len(_res := db.verify_account(pseudo, password)) == 1:
            _uuid, _token = _res[0]

            client.set_account(token, seed)
            db.set_token(_uuid, seed)
            return "JSON", {"uuid": seed}

        raise Exception()
    except Exception as e:
        LOGGER.log(e, ERROR)
        raise DataError(401, "wrong mail or password")


@PARSER.LOG("/sign")
def sign(pseudo: str, password: str) -> Tuple[str, Dict]:
    """
    Create a new account with the given pseudo & password

    :param pseudo: User's pseudo
    :param password: User's password
    :return:
    """
    db.create_account(pseudo, password)
    return "JSON", {}
