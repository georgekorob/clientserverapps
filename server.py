# Сервер

import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT
from common.utils import get_message, send_message


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

    def __init__(self, address='', port=DEFAULT_PORT):
        # Инициализация сокета
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind((address, port))

    @staticmethod
    def process_client_message(message):
        """
        Валидация ответа от клиента.
        :param message: Словарь-сообщение от клинта
        :return: Словарь-ответ для клиента
        """
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
        # Слушаем порт
        self.transport.listen(MAX_CONNECTIONS)
        while True:
            with self.ClientAccept(self.transport) as (client, client_address):
                try:
                    message_from_client = get_message(client)
                    print(message_from_client)
                    response = self.process_client_message(message_from_client)
                    send_message(client, response)
                except (ValueError, json.JSONDecodeError):
                    print('Принято некорретное сообщение от клиента.')


if __name__ == '__main__':
    # Валидация порта
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if 1024 > listen_port > 65535:
            raise ValueError
    except IndexError:
        print('После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        print('В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    # Валидация адреса
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        print('После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)

    server = Server(listen_address, listen_port)
    server.start()
