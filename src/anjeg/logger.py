from colorama import Fore

INFO = 0
WARNING = 1
ERROR = 2
TEST = 3

COLORS = [Fore.LIGHTWHITE_EX, Fore.YELLOW, Fore.RED, Fore.BLUE]


class Logger(object):
    """
    Logger class to make log simplier
    """

    def __init__(self, name: str):
        """
        :param name: The name of the logger
        """
        self.__name = name

    def log(self, message: str, status: int = INFO):
        """
        :param message: The message to log
        :param status: The message's status, it defines the color
        """
        print(f"{COLORS[status]}[{self.__name}] {message}{Fore.RESET}")
