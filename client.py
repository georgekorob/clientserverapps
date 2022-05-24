# Клиент
import argparse
import sys
import json
import socket
import threading
import time
from common.descriptors import Port, Host
from common.metaclasses import ClientVerifier
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, SENDER, MESSAGE_TEXT, MESSAGE, EXIT, DESTINATION
from common.utils import get_message, send_message
import logging
import log.client_log_config
from decorators import Log
from os import system

logger = logging.getLogger('client_logger')


class Client(metaclass=ClientVerifier):
    port = Port()
    address = Host()

    def __init__(self):
        # Инициализация сокета
        logger.debug(f'Настройка клиента.')
        self.address, self.port, self.client_name = self.arg_parser()
        logger.info(f'Настроен клиент с парамертами: адрес сервера {self.address}, '
                           f'порт {self.port}, имя пользователя: {self.client_name}')
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        system("title " + self.client_name)

    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    @staticmethod
    def arg_parser():
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default='test', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        address = namespace.addr
        port = namespace.port
        client_name = namespace.name
        return address, port, client_name

    @Log()
    def create_sys_message(self, request):
        """
        Функция генерирует запрос о состоянии клиента.
        :return: Словарь запрос.
        """
        logger.debug(f'Сформировано {request} сообщение для пользователя {self.client_name}')
        return {
            ACTION: request,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
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
        logger.debug(f'Сообщение от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        raise ValueError

    @Log()
    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        :param sock:
        :param account_name:
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.transport, message_dict)
            logger.info(f'Отправлено сообщение для пользователя {to_user}')
        except Exception as e:
            logger.critical(f'Потеряно соединение с сервером. {e}')
            sys.exit(1)

    @Log()
    def message_from_server(self):
        """Функция для обработки сообщений, поступающих с сервера"""
        while True:
            try:
                message = get_message(self.transport)
                if all([w in message for w in [ACTION, SENDER, DESTINATION, MESSAGE_TEXT]]) and \
                        message[ACTION] == MESSAGE and \
                        message[DESTINATION] == self.client_name:
                    mes = f'\nПолучено сообщение от пользователя {message[SENDER]}:' \
                          f'\n{message[MESSAGE_TEXT]}'
                    print(mes)
                    logger.info(mes)
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except Exception as e:
                logger.critical(f'Потеряно соединение с сервером. {e}')
                break

    @Log()
    def message_to_server(self):
        """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                send_message(self.transport, self.create_sys_message(EXIT))
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def start(self):
        """Инициализация обмена с сервером."""
        try:
            self.transport.connect((self.address, self.port))
            send_message(self.transport, self.create_sys_message(PRESENCE))
            answer = self.process_ans(get_message(self.transport))
            logger.info(f'Принят ответ от сервера: {answer}')
            print(f'Установлено соединение с сервером.')
        except (ValueError, ConnectionRefusedError, json.JSONDecodeError):
            logger.error('Не удалось декодировать сообщение сервера.')
            sys.exit(1)
        else:
            # Если соединение с сервером установлено
            # запускаем клиенский процесс приёма сообщний
            receiver = threading.Thread(target=self.message_from_server)
            receiver.daemon = True
            receiver.start()
            # запускаем отправку сообщений
            user_send_message = threading.Thread(target=self.message_to_server)
            user_send_message.daemon = True
            user_send_message.start()
            logger.debug('Запущены процессы')

            # завершаем работу, если один из потоков завершен
            while True:
                time.sleep(1)
                if receiver.is_alive() and user_send_message.is_alive():
                    continue
                break


def main():
    client = Client()
    client.start()


if __name__ == '__main__':
    main()
