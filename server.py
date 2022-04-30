# Сервер
import argparse
import select
import socket
import sys
import json
import time
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, \
    RESPONSE_200, RESPONSE_400, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from common.utils import get_message, send_message
import logging
import log.server_log_config
from decorators import Log

SERVER_LOGGER = logging.getLogger('server_logger')


class Server:
    def __init__(self):
        # Инициализация сокета
        SERVER_LOGGER.debug(f'Настройка сервера.')
        address, port = self.create_arg_parser()

        SERVER_LOGGER.info(f'Порт для подключений: {port}, '
                           f'адрес с которого принимаются подключения: {address}. '
                           f'Если адрес не указан, принимаются соединения с любых адресов.')

        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind((address, port))
        self.transport.settimeout(0.5)
        # список клиентов и очередь сообщений
        self.clients = []
        self.messages = []
        # Словарь, содержащий имена пользователей и соответствующие им сокеты
        self.names = dict()

    @staticmethod
    def create_arg_parser():
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', default='', nargs='?')
        parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        address, port = namespace.a, namespace.p
        # Валидация порта
        if 1024 > port > 65535:
            SERVER_LOGGER.critical(f'Указан неподходящий порт: {port}. '
                                   f'Допустимые адреса с 1024 до 65535.')
            sys.exit(1)
        return address, port

    @Log()
    def process_client_message(self, message, client):
        """
        Валидация ответа от клиента.
        :param message: Словарь-сообщение от клинта
        :param client:
        :return: Словарь-ответ для клиента
        """
        SERVER_LOGGER.debug(f'Сообщение от клиента : {message}')
        if all([w in message for w in [ACTION, TIME]]):
            if message[ACTION] == PRESENCE and \
                    USER in message:
                # Если клиент хочет зарегистрироватся
                if message[USER][ACCOUNT_NAME] not in self.names.keys():
                    # Если клиента с таким именем ещё не было
                    self.names[message[USER][ACCOUNT_NAME]] = client
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
            elif message[ACTION] == MESSAGE and \
                all([w in message for w in [DESTINATION, SENDER, MESSAGE_TEXT]]):
                # Если клиент хочет отправить сообщение
                self.messages.append(message)
                return
            elif message[ACTION] == EXIT and \
                    USER in message:
                # Если клиент хочет выйти
                client_name = message[USER][ACCOUNT_NAME]
                self.clients.remove(self.names[client_name])
                self.names[client_name].close()
                del self.names[client_name]
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
                SERVER_LOGGER.info(f'Отправлено сообщение '
                                   f'пользователю {message[DESTINATION]} '
                                   f'от пользователя {message[SENDER]}.')
            else:
                raise ConnectionError
        else:
            SERVER_LOGGER.error(f'Пользователь {message[DESTINATION]} '
                                f'не зарегистрирован на сервере, '
                                f'отправка сообщения невозможна.')

    def start(self):
        """Запуск сервера."""
        SERVER_LOGGER.debug(f'Запуск сервера.')
        # Слушаем порт
        self.transport.listen(MAX_CONNECTIONS)
        while True:
            try:
                client, client_address = self.transport.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
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
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                           f'отключился от сервера.')
                        self.clients.remove(client_with_message)

            # Обрабатываем каждое сообщение
            for mes in self.messages:
                try:
                    self.process_message(mes, self.names, send_data_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {mes[DESTINATION]} '
                                       f'была потеряна')
                    self.clients.remove(self.names[mes[DESTINATION]])
                    del self.names[mes[DESTINATION]]
            self.messages.clear()


if __name__ == '__main__':
    server = Server()
    server.start()
