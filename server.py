# Сервер
import argparse
import configparser
import os
import sys
import threading
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import logging
import log.server_log_config
from common.variables import *
from common.decorators import Log
from server.core import MessageProcessor
from server.database import ServerStorage
from server.main_window import MainWindow

new_connection = False
conflag_lock = threading.Lock()
logger = logging.getLogger('server_logger')


@Log()
def arg_parser(def_port, def_address):
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default=def_address, nargs='?')
    parser.add_argument('-p', default=def_port, type=int, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    return namespace.a, namespace.p, namespace.no_gui


@Log()
def config_load():
    """Загрузка файла конфигурации."""
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    config = config_load()

    listen_address, listen_port, gui_flag = arg_parser(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_Address'])
    database = ServerStorage(os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file']))

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # простенький обработчик консольного ввода
    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завршаем основной цикл сервера.
                server.running = False
                server.join()
                break

    # GUI:
    else:
        # Создаём графическое окуружение для сервера:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)
        # Запускаем GUI
        server_app.exec_()
        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
