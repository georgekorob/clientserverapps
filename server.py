# Сервер
import argparse
import configparser
import os
import select
import socket
import sys
import threading
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from common.descriptors import Port, Host
from common.metaclasses import ServerVerifier
import logging
import log.server_log_config
from common.variables import *
from common.utils import *
from common.decorators import Log
from server_database import ServerStorage
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow

new_connection = False
conflag_lock = threading.Lock()
logger = logging.getLogger('server_logger')


@Log()
def arg_parser(def_port, def_address):
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default=def_address, nargs='?')
    parser.add_argument('-p', default=def_port, type=int, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    return namespace.a, namespace.p


# Основной класс сервера
class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()
    address = Host()

    def __init__(self, listen_address, listen_port, database):
        # Параментры подключения
        logger.debug(f'Настройка сервера.')
        self.address, self.port = listen_address, listen_port
        logger.info(f'Порт для подключений: {self.port}, '
                    f'адрес с которого принимаются подключения: {self.address}. '
                    f'Если адрес не указан, принимаются соединения с любых адресов.')
        # База данных сервера
        self.database = database
        # список клиентов и очередь сообщений
        self.clients = []
        self.messages = []
        # Словарь, содержащий имена пользователей и соответствующие им сокеты
        self.names = dict()
        super().__init__()

    @Log()
    def process_client_message(self, message, client):
        """
        Валидация ответа от клиента.
        :param message: Словарь-сообщение от клинта
        :param client:
        :return: Словарь-ответ для клиента
        """
        global new_connection
        logger.debug(f'Разбор сообщения от клиента : {message}')

        if all([w in message for w in [ACTION, TIME, USER]]):
            user = message[USER]
            # Если это сообщение о присутствии, принимаем и отвечаем
            if message[ACTION] == PRESENCE:
                # Пользователь ещё не зарегистрирован
                if user not in self.names.keys():
                    self.names[user] = client
                    client_ip, client_port = client.getpeername()
                    self.database.user_login(user, client_ip, client_port)
                    send_message(client, RESPONSE_200)
                    with conflag_lock:
                        new_connection = True
                else:
                    # Клиент с таким именем уже зарегистрирован
                    response = RESPONSE_400
                    response[ERROR] = 'Имя пользователя уже занято.'
                    send_message(client, response)
                    self.clients.remove(client)
                    client.close()

            # Запрос контакт-листа
            elif message[ACTION] == GET_CONTACTS and \
                    self.names[user] == client:
                response = RESPONSE_202
                response[LIST_INFO] = self.database.get_contacts(user)
                send_message(client, response)

            # Добавление контакта
            elif message[ACTION] == ADD_CONTACT and \
                    ACCOUNT_NAME in message and \
                    self.names[user] == client:
                self.database.add_contact(user, message[ACCOUNT_NAME])
                send_message(client, RESPONSE_200)

            # Удаление контакта
            elif message[ACTION] == REMOVE_CONTACT and \
                    ACCOUNT_NAME in message and \
                    self.names[user] == client:
                self.database.remove_contact(user, message[ACCOUNT_NAME])
                send_message(client, RESPONSE_200)

            # Logout
            elif message[ACTION] == EXIT and \
                    self.names[user] == client:
                self.database.user_logout(user)
                logger.info(f'Клиент {user} корректно отключился от сервера.')
                self.clients.remove(self.names[user])
                self.names[user].close()
                del self.names[user]
                with conflag_lock:
                    new_connection = True

            # Запрос известных пользователей
            elif message[ACTION] == USERS_REQUEST and \
                    self.names[user] == client:
                response = RESPONSE_202
                response[LIST_INFO] = [user[0] for user in self.database.users_list()]
                send_message(client, response)

            # Сообщение
            elif message[ACTION] == MESSAGE and \
                    all([w in message for w in [DESTINATION, MESSAGE_TEXT]]) and \
                    self.names[user] == client:
                if message[DESTINATION] in self.names:
                    self.messages.append(message)
                    self.database.process_message(user, message[DESTINATION])
                    send_message(client, RESPONSE_200)
                else:
                    response = RESPONSE_400
                    response[ERROR] = 'Пользователь не зарегистрирован на сервере.'
                    send_message(client, response)

            return

        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен.'
        send_message(client, response)

    @Log()
    def process_message(self, message, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту.
        :param message: Словарь - сообщение
        :param names: Словарь клиентов
        :param listen_socks:
        """
        # отправляем сообщения, ожидающим клиентам
        if message[DESTINATION] in self.names:
            if self.names[message[DESTINATION]] in listen_socks:
                send_message(self.names[message[DESTINATION]], message)
                logger.info(f'Отправлено сообщение '
                            f'пользователю {message[DESTINATION]} '
                            f'от пользователя {message[USER]}.')
                return
            else:
                raise ConnectionError
        logger.error(f'Пользователь {message[DESTINATION]} '
                         f'не зарегистрирован на сервере, '
                         f'отправка сообщения невозможна.')

    def run(self):
        """Запуск сервера."""
        global new_connection
        logger.debug(f'Запуск сервера.')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.address, self.port))
        self.sock.settimeout(0.5)
        # Слушаем порт
        self.sock.listen()
        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst, send_data_lst, err_lst = [], [], []

            # наличие ожидающих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = \
                        select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения, кладём в словарь
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message),
                                                    client_with_message)
                    except Exception:
                        logger.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
                        with conflag_lock:
                            new_connection = True

            # Обрабатываем каждое сообщение
            for mes in self.messages:
                try:
                    self.process_message(mes, send_data_lst)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {mes[DESTINATION]} '
                                f'была потеряна')
                    self.clients.remove(self.names[mes[DESTINATION]])
                    self.database.user_logout(mes[DESTINATION])
                    del self.names[mes[DESTINATION]]
                    with conflag_lock:
                        new_connection = True
            self.messages.clear()


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


def pyqt_graph(config, database):
    """Графическое окуружение для сервера"""
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        """Обновление списка подключенных"""
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        """Окно со статистикой клиентов"""
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        """Окно с настройками сервера"""
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        """Сохранение настроек"""
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


def main():
    config = config_load()

    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_Address'])
    database = ServerStorage(os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    pyqt_graph(config, database)


if __name__ == '__main__':
    main()
