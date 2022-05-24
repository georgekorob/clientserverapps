# Сервер
import argparse
import select
import socket
import sys
import threading

from common.descriptors import Port, Host
from common.metaclasses import ServerVerifier
from common.variables import *
from common.utils import *
from decorators import Log
from databases.server_database import ServerStorage

logger = logging.getLogger('server_logger')


@Log()
def arg_parser():
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default='', nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    return namespace.a, namespace.p


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()
    address = Host()

    def __init__(self, listen_address, listen_port, database):
        # Инициализация сокета
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
        logger.debug(f'Сообщение от клиента : {message}')
        if all([w in message for w in [ACTION, TIME]]):
            if USER in message:
                if message[ACTION] == PRESENCE:
                    # Если клиент хочет зарегистрироватся
                    if message[USER] not in self.names.keys():
                        # Если клиента с таким именем ещё не было
                        self.names[message[USER]] = client
                        client_ip, client_port = client.getpeername()
                        self.database.user_login(message[USER], client_ip, client_port)
                        send_message(client, RESPONSE_200)  # сообщение о присутствии
                        return
                    else:
                        # Если клиент с таким именем уже зарегистрирован
                        response = RESPONSE_400
                        response[ERROR] = 'Имя пользователя уже занято.'
                        send_message(client, response)
                        self.clients.remove(client)
                        client.close()
                        return
                elif message[ACTION] == EXIT:
                    # Если клиент хочет выйти
                    client_name = message[USER][ACCOUNT_NAME]
                    self.database.user_logout(client_name)
                    self.clients.remove(self.names[client_name])
                    self.names[client_name].close()
                    del self.names[client_name]
                    return
                elif message[ACTION] == GET_CONTACTS and \
                        self.names[message[USER]] == client:
                    response = RESPONSE_202
                    response[LIST_INFO] = self.database.get_contacts(message[USER])
                    send_message(client, response)
                    return
                elif message[ACTION] == USERS_REQUEST and \
                        self.names[message[USER]] == client:
                    response = RESPONSE_202
                    response[LIST_INFO] = [user[0] for user in self.database.users_list()]
                    send_message(client, response)
                    return
                elif message[ACTION] == ADD_CONTACT and \
                        ACCOUNT_NAME in message and \
                        self.names[message[USER]] == client:
                    self.database.add_contact(message[USER], message[ACCOUNT_NAME])
                    send_message(client, RESPONSE_200)
                    return
                elif message[ACTION] == REMOVE_CONTACT and \
                        ACCOUNT_NAME in message and \
                        self.names[message[USER]] == client:
                    self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
                    send_message(client, RESPONSE_200)
                    return
            elif message[ACTION] == MESSAGE and \
                    all([w in message for w in [DESTINATION, SENDER, MESSAGE_TEXT]]):
                # Если клиент хочет отправить сообщение
                self.messages.append(message)
                self.database.process_message(message[SENDER], message[DESTINATION])
                return
        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен.'
        send_message(client, response)  # отдаём Bad request

    @staticmethod
    @Log()
    def process_message(message, names, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту.
        :param message: Словарь - сообщение
        :param names: Словарь клиентов
        :param listen_socks:
        """
        # отправляем сообщения, ожидающим клиентам
        if message[DESTINATION] in names:
            if names[message[DESTINATION]] in listen_socks:
                send_message(names[message[DESTINATION]], message)
                logger.info(f'Отправлено сообщение '
                            f'пользователю {message[DESTINATION]} '
                            f'от пользователя {message[SENDER]}.')
            else:
                raise ConnectionError
        else:
            logger.error(f'Пользователь {message[DESTINATION]} '
                         f'не зарегистрирован на сервере, '
                         f'отправка сообщения невозможна.')

    def run(self):
        """Запуск сервера."""
        logger.debug(f'Запуск сервера.')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.address, self.port))
        self.sock.settimeout(0.5)
        # Слушаем порт
        self.sock.listen(MAX_CONNECTIONS)
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
                        self.clients.remove(client_with_message)

            # Обрабатываем каждое сообщение
            for mes in self.messages:
                try:
                    self.process_message(mes, self.names, send_data_lst)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {mes[DESTINATION]} '
                                f'была потеряна')
                    self.clients.remove(self.names[mes[DESTINATION]])
                    del self.names[mes[DESTINATION]]
            self.messages.clear()


def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main():
    database = ServerStorage()
    listen_address, listen_port = arg_parser()
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    print_help()

    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'loghist':
            name = input('Введите имя пользователя для просмотра истории.'
                         'Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    main()
