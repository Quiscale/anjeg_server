
import ast
import json
import socket
import traceback
from typing import Tuple
from multiprocessing import Process, Queue

from .logger import Logger, ERROR, WARNING
from .parser import ParserError, HeaderError, Parser


VERSION = "Ozad/0.0.402021"


# #############################################################################
# Class exception
# #############################################################################

class DataError(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self)
        self.code = code
        self.msg = msg


# #############################################################################
# Class client
# #############################################################################

class Client(Process, Logger):
    """
    Cette classe client permet de traiter chaque client indépendamment des autres dans un thread dédié
    Il reçoit les données via un socket et se sert de la classe Parser pour analyser les données reçu
    """

    def __init__(self, sock: socket.socket, addr: Tuple, server):
        Process.__init__(self)
        Logger.__init__(self, f"client_{sock.fileno()}")

        self.__id = sock.fileno()
        self.__socket = sock
        self.__server = server
        self.__buffer = bytearray()

        self.__account_id = None
        self.__account_uuid = None

        self.log(f"from {addr[0]}")

    def run(self):

        run = True
        while run:
            # Reçoit les données
            req = self.__socket.recv(256)
            resh, resb = "", ""  # Response head & body
            self.__buffer += req
            # Extrait l'entête
            header_len = self.__buffer.find(b'\n')
            header = self.__buffer[:header_len]
            del self.__buffer[:header_len + 1]
            self.log(str(header))
            # Analyse l'entête
            try:
                data = {}
                func, data_type, data_len, id, token = self.__server.parse(header)
                if data_len is not None:
                    # Extrait les données liées à l'entête
                    bdata = self.__buffer[:data_len + 1]  # for bytes data
                    del self.__buffer[:data_len + 1]

                    sdata = bdata.decode('utf-8')  # for str data
                    if data_type == "TEXT":
                        data["text"] = sdata
                    elif data_type == "JSON":
                        data = ast.literal_eval(sdata)
                        print(data)
                    elif data_type == "IMAGE":
                        data["image"] = bdata

                args = {
                    key: {**data, "client": self, "token": token}[key]
                    for key in func.__code__.co_varnames[:func.__code__.co_argcount]
                }
                try:
                    res_type, res = func(**args)
                    # Prepare response head & body
                    resb = json.dumps(res, separators=(', ', ':'))
                    resh = f"{200} {id} {res_type} {len(resb)}\n"
                except DataError as e:
                    # Prepare response head & body
                    resb = e.msg
                    resh = f"{e.code} {id} TEXT {len(resb)}\n"

            except ParserError as e:
                self.log(f"#{e.code} : {e.msg}", WARNING)
                if e.code == 0:
                    run = False
                else:
                    # Prepare response head & body
                    resb = e.msg
                    resh = f"{e.code} . TEXT {len(resb)}\n"
            except HeaderError as e:
                # Prepare response head & body
                resb = e.msg
                resh = f"{e.code} {e.request_id} TEXT {len(resb)}\n"
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                self.log(f"{type(e)} {e}", ERROR)
                # Prepare response head & body
                resb = f"{type(e)} {e}"
                resh = f"500 . TEXT {len(resb)}\n"

            self.__socket.send(resh.encode('utf-8') + resb.encode('utf-8'))

            # end while

        self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()
        self.__server.put_in_queue(("CLOSE", self.id))

    def fileno(self):
        return self.__socket.fileno()

    @property
    def id(self):
        return self.__id

    def set_account(self, id, uuid):
        self.__account_id = id
        self.__account_uuid = uuid

    def verify_account(self, uuid):
        return self.__account_id if uuid == self.__account_uuid else None


# #############################################################################
# Class server
# #############################################################################

class Server(Process, Logger):
    """
    Serveur du jeu
    Il sert d'API entre le pc client et la base de données
    Il créé un nouveau thread client lors de la connexion de celui-ci
    Il possède une queue afin de traiter les données qui lui sont envoyées
    """

    def __init__(self, host: str, port: int, parser: Parser):
        Process.__init__(self)
        Logger.__init__(self, "server")

        self.__parser = parser
        self.__queue = Queue()
        self.__clients = {}

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind((host, port))
        self.__socket.listen(5)
        self.__socket.settimeout(1)
        self.log("Ready")

    def put_in_queue(self, data):
        self.__queue.put(data)

    def parse(self, data):
        return self.__parser.parse(data)

    def run(self):

        self.log("Start")
        try:
            run = True
            while run:

                # Accept new socket
                try:
                    client_socket, client_address = self.__socket.accept()
                    client = Client(client_socket, client_address, self)
                    self.__clients[client.id] = client
                    client.start()
                except socket.timeout as e:
                    None

                # Empty the queue
                while not self.__queue.empty():
                    item = self.__queue.get()

                    if item[0] == "CLOSE":
                        if (id := item[1]) is not None:
                            self.__clients.pop(id)
                            self.log(f"client_{id} disconnected")
                        else:
                            run = False

        # Exception in 'while' that should stop the server
        except KeyboardInterrupt as e:
            self.log("Ctrl-C interrupt", ERROR)
        except Exception as e:
            trace = ""
            for tb in traceback.format_tb(e.__traceback__):
                trace += tb
            self.log(f"Exception occured : {e}\n{trace}", ERROR)

        # Close the thread properly
        self.__socket.close()
        for client in self.__clients.values():
            client.kill()
        self.log("Stop")
