# Клиент

import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS,\
    DEFAULT_PORT
from common.utils import get_message, send_message


class Client:
    def __init__(self, address, port):
        # Инициализация сокета
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.connect((address, port))

    @staticmethod
    def create_presence(account_name='Guest'):
        """
        Функция генерирует запрос о присутствии клиента.
        :param account_name: Имя пользователя.
        :return: Словарь запрос.
        """
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
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        raise ValueError

    def start(self):
        """Инициализация обмена с сервером."""
        message_to_server = self.create_presence()
        send_message(self.transport, message_to_server)
        try:
            answer = self.process_ans(get_message(self.transport))
            print(answer)
        except (ValueError, json.JSONDecodeError):
            print('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    # Валидация адреса и порта
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    client = Client(server_address, server_port)
    client.start()
