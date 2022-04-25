# Сервер
import argparse
import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT
from common.utils import get_message, send_message
import logging
import log.server_log_config
from decorators import Log

SERVER_LOGGER = logging.getLogger('server_logger')


class Server:
    class ClientAccept(object):
        def __init__(self, transport):
            self.transport = transport

        def __enter__(self):
            try:
                self.client, client_address = self.transport.accept()
            except Exception as e:
                print(e)
                self.client, client_address = None, None
            return self.client, client_address

        def __exit__(self, exp_type, exp_value, exp_tr):
            if exp_type is Exception:
                self.client.close()
                return True
            self.client.close()

    def __init__(self, arguments):
        # Инициализация сокета
        SERVER_LOGGER.debug(f'Настройка сервера.')
        parser = self.create_arg_parser()
        namespace = parser.parse_args(arguments)
        address, port = namespace.a, namespace.p
        # Валидация порта
        if 1024 > port > 65535:
            SERVER_LOGGER.critical(f'Указан неподходящий порт: {port}. '
                                   f'Допустимые адреса с 1024 до 65535.')
            sys.exit(1)
        SERVER_LOGGER.info(f'Порт для подключений: {port}, '
                           f'адрес с которого принимаются подключения: {address}. '
                           f'Если адрес не указан, принимаются соединения с любых адресов.')

        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind((address, port))

    @staticmethod
    @Log()
    def process_client_message(message):
        """
        Валидация ответа от клиента.
        :param message: Словарь-сообщение от клинта
        :return: Словарь-ответ для клиента
        """
        SERVER_LOGGER.debug(f'Сообщение от клиента : {message}')
        if ACTION in message and \
                message[ACTION] == PRESENCE and \
                TIME in message and \
                USER in message and \
                message[USER][ACCOUNT_NAME] == 'Guest':
            return {
                RESPONSE: 200
            }
        return {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        }

    def start(self):
        """Запуск сервера."""
        SERVER_LOGGER.debug(f'Запуск сервера.')
        # Слушаем порт
        self.transport.listen(MAX_CONNECTIONS)
        while True:
            with self.ClientAccept(self.transport) as (client, client_address):
                SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
                try:
                    message_from_client = get_message(client)
                    SERVER_LOGGER.debug(f'Получено сообщение {message_from_client}')
                    response = self.process_client_message(message_from_client)
                    SERVER_LOGGER.info(f'Cформирован ответ клиенту {response}')
                    send_message(client, response)
                except (ValueError, json.JSONDecodeError):
                    SERVER_LOGGER.error(f'Принято некорретное сообщение от клиента {client_address}.')
                SERVER_LOGGER.debug(f'Соединение с клиентом {client_address} закрывается.')

    @staticmethod
    def create_arg_parser():
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', default='', nargs='?')
        parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
        return parser


if __name__ == '__main__':
    server = Server(sys.argv[1:])
    server.start()
