import sqlite3 as sql
from .logger import Logger, ERROR
from typing import Dict


class Connector (Logger):

    def __init__(self, _name: str, _model: Dict):

        Logger.__init__(self, _name)

        self.__database = _name + ".db"
        self.__model = _model

    def execute(self, _request: str):

        self.log(_request)
        _conn = sql.connect(self.__database)
        _cursor = _conn.cursor()

        _answer = None
        try:
            _cursor.execute(_request)
            _answer = _cursor.fetchall()
            if not _request.startswith("select"):
                _conn.commit()
        except sql.OperationalError as _e:
            self.log(f"{type(_e)}: {_e}\n{_request}", ERROR)

        _cursor.close()
        _conn.close()

        return _answer

    def init(self):
        for _k_db, _v_db in self.__model.items():
            self.log(str(self.execute(f"DROP TABLE IF EXISTS {_k_db};")))
            _creator = f"CREATE TABLE {_k_db}("
            for _k_t, _v_t in _v_db.items():
                if _k_t == "references":
                    for _k_r, _v_r in _v_t.items():
                        _creator += f"FOREIGN KEY ({_k_r}) REFERENCES {_v_r} (id),"
                else:
                    _creator += f"{_k_t} {_v_t},"
            _creator = _creator[:-1] + ");"

            self.log(str(self.execute(_creator)))

    def prompt(self):
        _run = True
        while _run:

            _cmd = input("> ")

            if _cmd.startswith("exit"):
                _run = False
            elif _cmd.startswith("init"):
                self.init()
            else:
                print(self.execute(_cmd))

        print("loop exited")
