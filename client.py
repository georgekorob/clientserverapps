# Клиент
import argparse
import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, SENDER, MESSAGE_TEXT, MESSAGE
from common.utils import get_message, send_message
import logging
import log.client_log_config
from decorators import Log

CLIENT_LOGGER = logging.getLogger('client_logger')


class Client:
    def __init__(self):
        # Инициализация сокета
        CLIENT_LOGGER.debug(f'Настройка клиента.')
        self.address, self.port, self.client_mode = self.arg_parser()
        CLIENT_LOGGER.info(f'Настроен клиент с парамертами: адрес сервера {self.address}, '
                           f'порт {self.port}, режим работы: {self.client_mode}')
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    @Log()
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
    @Log()
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

    @staticmethod
    @Log()
    def create_message(sock, account_name='Guest'):
        """Текст сообщения для отправки или завершает работу"""
        message = input('Введите сообщение для отправки или \'q\' для завершения работы: ')
        if message == 'q':
            sock.close()
            CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
            print('Спасибо за использование нашего сервиса!')
            sys.exit(0)
        message_dict = {
            ACTION: MESSAGE,
            TIME: time.time(),
            ACCOUNT_NAME: account_name,
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        return message_dict

    @staticmethod
    @Log()
    def message_from_server(message):
        """Функция для обработки сообщений, поступающих с сервера"""
        if ACTION in message and \
                message[ACTION] == MESSAGE and \
                SENDER in message and \
                MESSAGE_TEXT in message:
            print(f'Получено сообщение от пользователя '
                  f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                               f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        else:
            CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')

    def start(self):
        """Инициализация обмена с сервером."""
        try:
            self.transport.connect((self.address, self.port))
            message_to_server = self.create_presence()
            send_message(self.transport, message_to_server)
            answer = self.process_ans(get_message(self.transport))
            CLIENT_LOGGER.info(f'Принят ответ от сервера: {answer}')
            print(f'Установлено соединение с сервером.')
        except (ValueError, ConnectionRefusedError, json.JSONDecodeError):
            CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')
            sys.exit(1)
        else:
            # Если соединение с сервером установлено
            while True:
                try:
                    if self.client_mode == 'send':
                        print('Режим работы - отправка сообщений.')
                        send_message(self.transport, self.create_message(self.transport))
                    elif self.client_mode == 'listen':
                        print('Режим работы - приём сообщений.')
                        self.message_from_server(get_message(self.transport))
                    else:
                        print('Неизвестный режим работы.')
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    CLIENT_LOGGER.error(f'Соединение с сервером {self.address} было потеряно.')
                    sys.exit(1)

    @staticmethod
    def arg_parser():
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-m', '--mode', default='listen', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        address = namespace.addr
        port = namespace.port
        client_mode = namespace.mode

        if not 1023 < port < 65536:
            CLIENT_LOGGER.critical(f'Указан неподходящий порт: {port}. '
                                   f'Допустимые адреса с 1024 до 65535.')
            sys.exit(1)

        if client_mode not in ('listen', 'send'):
            CLIENT_LOGGER.critical(f'Указан недопустимый режим работы {client_mode}, '
                                   f'допустимые режимы: listen , send')
            sys.exit(1)

        return address, port, client_mode


if __name__ == '__main__':
    client = Client()
    client.start()
