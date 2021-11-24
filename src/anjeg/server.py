
import ast
import json
import socket
import traceback
from multiprocessing import Process, Queue
from typing import Tuple

from .logger import Logger, ERROR, WARNING


VERSION = "Ozad/0.0.402021"


# #############################################################################
# Class Exception
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

    def __init__(self, sock: socket.socket, addr: Tuple, server_queue: Queue):
        Process.__init__(self)
        Logger.__init__(self, f"client_{sock.fileno()}")

        self.__id = sock.fileno()
        self.__socket = sock
        self.__queue = server_queue
        self.__buffer = bytearray()

        self.__account_id = None
        self.__account_uuid = None

        self.log(f"from {addr[0]}")

    def run(self):

        run = True
        while run:
            # Reçoit les données
            req = self.__socket.recv(256)
            res = None
            self.__buffer += req
            # Extrait l'entête
            header_len = self.__buffer.find(b'\n')
            header = self.__buffer[:header_len]
            del self.__buffer[:header_len + 1]
            self.log(header)
            # Analyse l'entête
            try:
                data = b"{}"
                func, data_len, uuid, req_id = PARSER.parse(header)
                if data_len is not None:
                    # Extrait les données liées à l'entête
                    data = self.__buffer[:data_len + 1]
                    del self.__buffer[:data_len + 1]

                args = {
                    key: {**ast.literal_eval(data.decode('utf-8')), "client": self, "uuid": uuid}[key]
                    for key in func.__code__.co_varnames[:func.__code__.co_argcount]
                }
                try:
                    res = func(**args)

                    resb = json.dumps(res, separators=(', ', ':')).encode('utf-8')
                    res_head = f"{200} {VERSION} {req_id} JSON {len(resb)}\n".encode('utf-8')
                    self.__socket.send(res_head + resb)
                except DataError as e:
                    resb = e.msg.encode('utf-8')
                    res_head = f"{e.code} {VERSION} {req_id} TEXT {len(resb)}\n".encode('utf-8')
                    self.__socket.send(res_head + resb)

            except ParserError as e:
                self.log(f"#{e.code} : {e.msg}", WARNING)
                if e.code == 0:
                    run = False
                else:
                    resb = e.msg.encode('utf-8')
                    res_head = f"{e.code} {VERSION} . TEXT {len(resb)}\n".encode('utf-8')
                    self.__socket.send(res_head + resb)
            except HeaderError as e:
                resb = e.msg.encode('utf-8')
                res_head = f"{e.code} {VERSION} {e.request_id} TEXT {len(resb)}\n".encode('utf-8')
                self.__socket.send(res_head + resb)
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                self.log(f"{type(e)} {e}", ERROR)
                resb = f"{type(e)} {e}".encode('utf-8')
                res_head = f"500 {VERSION} . TEXT {len(resb)}\n".encode('utf-8')
                self.__socket.send(res_head + resb)

            # end while

        self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()
        self.__queue.put(("CLOSE", self.id))

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

    def __init__(self, host: str, port: int):
        Process.__init__(self)
        Logger.__init__(self, "server")

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

    def run(self):

        self.log("Start")
        try:
            run = True
            while run:

                # Accept new socket
                try:
                    client_socket, client_address = self.__socket.accept()
                    client = Client(client_socket, client_address, self.__queue)
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