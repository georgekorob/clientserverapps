# Сервер
import argparse
import select
import socket
import sys
import json
import time

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, \
    RESPONSE_200, RESPONSE_400, MESSAGE, MESSAGE_TEXT, SENDER
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
        self.clients = []
        self.messages = []

    @staticmethod
    @Log()
    def process_client_message(message, messages_list, client):
        """
        Валидация ответа от клиента.
        :param message: Словарь-сообщение от клинта
        :param messages_list:
        :param client:
        :return: Словарь-ответ для клиента
        """
        SERVER_LOGGER.debug(f'Сообщение от клиента : {message}')
        if ACTION in message and \
                message[ACTION] == PRESENCE and \
                TIME in message and \
                USER in message and \
                message[USER][ACCOUNT_NAME] == 'Guest':
            send_message(client, RESPONSE_200)  # сообщение о присутствии
        elif ACTION in message and \
                message[ACTION] == MESSAGE and \
                TIME in message and \
                MESSAGE_TEXT in message:
            # добавляем его в очередь сообщений
            messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        else:
            send_message(client, RESPONSE_400)  # отдаём Bad request

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
                                                    self.messages,
                                                    client_with_message)
                    except Exception:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                           f'отключился от сервера.')
                        self.clients.remove(client_with_message)

            # отправляем сообщения, ожидающим клиентам
            if self.messages and send_data_lst:
                message = {
                    ACTION: MESSAGE,
                    SENDER: self.messages[0][0],
                    TIME: time.time(),
                    MESSAGE_TEXT: self.messages[0][1]
                }
                del self.messages[0]
                for waiting_client in send_data_lst:
                    try:
                        send_message(waiting_client, message)
                    except Exception:
                        SERVER_LOGGER.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                        self.clients.remove(waiting_client)

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


if __name__ == '__main__':
    server = Server()
    server.start()
