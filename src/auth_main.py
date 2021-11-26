from anjeg import server
import auth_path
import test

if __name__ == "__main__":

    serv_auth = server.Server("127.0.0.1", 8000, path_auth.PARSER)
    serv_auth.start()

    # test.start(serv_auth)

    input()
