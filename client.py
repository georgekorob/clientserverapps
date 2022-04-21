# Клиент
import argparse
import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS,\
    DEFAULT_PORT
from common.utils import get_message, send_message
import logging
import log.client_log_config

CLIENT_LOGGER = logging.getLogger('client_logger')


class Client:
    def __init__(self, arguments):
        # Инициализация сокета
        CLIENT_LOGGER.debug(f'Настройка клиента.')
        CLIENT_LOGGER.debug(f'{arguments}')
        parser = self.create_arg_parser()
        namespace = parser.parse_args(arguments)
        address, port = namespace.addr, namespace.port
        # Валидация порта
        if 1024 > port > 65535:
            CLIENT_LOGGER.critical(f'Указан неподходящий порт: {port}. '
                                   f'Допустимые адреса с 1024 до 65535.')
            sys.exit(1)
        CLIENT_LOGGER.info(f'Настроен клиент с парамертами: адрес {address}, порт {port}.')

        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address, self.port = address, port

    @staticmethod
    def create_presence(account_name='Guest'):
        """
        Функция генерирует запрос о присутствии клиента.
        :param account_name: Имя пользователя.
        :return: Словарь запрос.
        """
        CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
        return {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }

    @staticmethod
    def process_ans(message):
        """
        Валидация ответа от сервера.
        :param message: Словарь-сообщение от сервера.
        :return: Информационная строка.
        """
        CLIENT_LOGGER.debug(f'Сообщение от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        raise ValueError

    def start(self):
        """Инициализация обмена с сервером."""
        self.transport.connect((self.address, self.port))
        message_to_server = self.create_presence()
        send_message(self.transport, message_to_server)
        try:
            answer = self.process_ans(get_message(self.transport))
            CLIENT_LOGGER.info(f'Принят ответ от сервера: {answer}')
        except (ValueError, json.JSONDecodeError):
            CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')

    @staticmethod
    def create_arg_parser():
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        return parser


if __name__ == '__main__':
    client = Client(sys.argv[1:])
    client.start()
