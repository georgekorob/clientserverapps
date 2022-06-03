import argparse
import sys
import threading
from PyQt5.QtWidgets import QApplication
from common.variables import *
from common.decorators import Log
import logging
from client.database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow

logger = logging.getLogger('client_logger')
sock_lock = threading.Lock()
database_lock = threading.Lock()


@Log()
def arg_parser():
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default='test', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    return namespace.addr, namespace.port, namespace.name


if __name__ == '__main__':
    address, port, client_name = arg_parser()
    client_app = QApplication(sys.argv)

    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {address},'
        f'порт: {port},'
        f'имя пользователя: {client_name}')

    # База данных
    database = ClientDatabase(f'databases/db_{client_name}.db3')

    # Транспорт
    try:
        transport = ClientTransport(address, port, database, client_name)
    except Exception as e:
        print(e)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат программа - {client_name}')
    client_app.exec_()

    # Закрываем транспорт
    transport.transport_shutdown()
    transport.join()
