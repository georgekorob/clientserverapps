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


# def pyqt_graph(config, database):
#     """Графическое окуружение для сервера"""
#     server_app = QApplication(sys.argv)
#     main_window = MainWindow()
#
#     # Инициализируем параметры в окна
#     main_window.statusBar().showMessage('Server Working')
#     main_window.active_clients_table.setModel(gui_create_model(database))
#     main_window.active_clients_table.resizeColumnsToContents()
#     main_window.active_clients_table.resizeRowsToContents()
#
#     def list_update():
#         """Обновление списка подключенных"""
#         global new_connection
#         if new_connection:
#             main_window.active_clients_table.setModel(gui_create_model(database))
#             main_window.active_clients_table.resizeColumnsToContents()
#             main_window.active_clients_table.resizeRowsToContents()
#             with conflag_lock:
#                 new_connection = False
#
#     def show_statistics():
#         """Окно со статистикой клиентов"""
#         global stat_window
#         stat_window = HistoryWindow()
#         stat_window.history_table.setModel(create_stat_model(database))
#         stat_window.history_table.resizeColumnsToContents()
#         stat_window.history_table.resizeRowsToContents()
#         stat_window.show()
#
#     def server_config():
#         """Окно с настройками сервера"""
#         global config_window
#         # Создаём окно и заносим в него текущие параметры
#         config_window = ConfigWindow()
#         config_window.db_path.insert(config['SETTINGS']['Database_path'])
#         config_window.db_file.insert(config['SETTINGS']['Database_file'])
#         config_window.port.insert(config['SETTINGS']['Default_port'])
#         config_window.ip.insert(config['SETTINGS']['Listen_Address'])
#         config_window.save_btn.clicked.connect(save_server_config)
#
#     def save_server_config():
#         """Сохранение настроек"""
#         global config_window
#         message = QMessageBox()
#         config['SETTINGS']['Database_path'] = config_window.db_path.text()
#         config['SETTINGS']['Database_file'] = config_window.db_file.text()
#         try:
#             port = int(config_window.port.text())
#         except ValueError:
#             message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
#         else:
#             config['SETTINGS']['Listen_Address'] = config_window.ip.text()
#             if 1023 < port < 65536:
#                 config['SETTINGS']['Default_port'] = str(port)
#                 dir_path = os.path.dirname(os.path.realpath(__file__))
#                 with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
#                     config.write(conf)
#                     message.information(config_window, 'OK', 'Настройки успешно сохранены!')
#             else:
#                 message.warning(config_window, 'Ошибка', 'Порт должен быть от 1024 до 65536')
#
#     # Таймер, обновляющий список клиентов 1 раз в секунду
#     timer = QTimer()
#     timer.timeout.connect(list_update)
#     timer.start(1000)
#
#     # Связываем кнопки с процедурами
#     main_window.refresh_button.triggered.connect(list_update)
#     main_window.show_history_button.triggered.connect(show_statistics)
#     main_window.config_btn.triggered.connect(server_config)
#
#     # Запускаем GUI
#     server_app.exec_()
