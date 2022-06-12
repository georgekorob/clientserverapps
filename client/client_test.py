import argparse
import os
import sys
import threading

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from client.start_dialog import UserNameDialog
from common.errors import ServerError
from common.variables import *
from common.decorators import Log
import logging
import log.client_log_config
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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    return namespace.addr, namespace.port, namespace.name, namespace.password


if __name__ == '__main__':
    address, port, client_name, client_password = arg_parser()
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его
    start_dialog = UserNameDialog()
    if not client_name or not client_password:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
        # удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_password = start_dialog.client_password.text()
            logger.debug(
                f'Using USERNAME = {client_name}, PASSWD = {client_password}.')
        else:
            sys.exit(0)

    logger.info(f'Запущен клиент с парамертами: адрес сервера: {address},'
                f'порт: {port},'
                f'имя пользователя: {client_name}')

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.getcwd()
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())
    logger.debug("Ключи загружены.")

    # База данных
    database = ClientDatabase(f'db_{client_name}.db3')

    # Транспорт
    try:
        transport = ClientTransport(
            address,
            port,
            database,
            client_name,
            client_password,
            keys)
        logger.debug("Клиент подготовлен.")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        sys.exit(1)
    transport.setDaemon(True)
    transport.start()

    # Удалим объект диалога за ненадобностью
    del start_dialog

    # GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат программа - {client_name}')
    client_app.exec_()

    # Закрываем транспорт
    transport.transport_shutdown()
    transport.join()
