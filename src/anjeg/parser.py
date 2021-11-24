
from typing import Tuple

from .logger import Logger


# #############################################################################
# Class Exception
# #############################################################################

class ParserError(Exception):

    def __init__(self, code, msg):
        Exception.__init__(self)
        self.code = code
        self.msg = msg


class HeaderError(Exception):
    def __init__(self, code, msg, request_id):
        Exception.__init__(self)
        self.code = code
        self.msg = msg
        self.request_id = request_id


# #############################################################################
# Class parser
# #############################################################################

class Parser(Logger):

    def __init__(self):
        Logger.__init__(self, "parser")
        self.__log = {}
        self.__get = {}
        self.__post = {}

    def GET(self, path):
        def register(func):
            self.__get[path] = func

        return register

    def POST(self, path):
        def register(func):
            self.__post[path] = func

        return register

    def LOG(self, path):
        def register(func):
            self.__log[path] = func

        return register

    def parse(self, header: bytearray) -> Tuple:
        length = len(params := header.split(b' '))

        if length == 1:
            raise ParserError(0, "Client need to be closed")
        if length != 4 and length != 6:
            raise ParserError(400, "Wrong number of parameter")
        command = params[0]
        url = params[1].decode('utf-8')
        id = params[2].decode('utf-8')
        token = params[3].decode('utf-8')
        data_type = params[4].decode('utf-8') if length == 6 else None
        data_length = int(params[5]) if length == 6 else None

        if command == b'GET' or command == b'POST':
            funcs = self.__get if command == b'GET' else self.__post
            if len(token) != 16:
                raise HeaderError(401, "ID is mandatory", id)
            if url not in funcs:
                raise HeaderError(404, "Url not found", id)
            return funcs[url], data_type, data_length, id, token

        elif command == b'LOG':
            if token != ".":
                raise HeaderError(401, "ID should be a dot", id)
            if url not in self.__log:
                raise HeaderError(404, "Url not found", id)
            return self.__log[url], data_type, data_length, id, token

        raise HeaderError(400, "Command not found", id)
