# Клиент
import argparse
import sys
import json
import socket
import threading
import time
from common.descriptors import Port, Host
from common.metaclasses import ClientVerifier
from common.variables import *
from common.utils import get_message, send_message
import logging
import log.client_log_config
from databases.client_database import ClientDatabase
from decorators import Log
from os import system

logger = logging.getLogger('client_logger')
sock_lock = threading.Lock()
database_lock = threading.Lock()


class Client(metaclass=ClientVerifier):
    port = Port()
    address = Host()

    def __init__(self):
        # Инициализация сокета
        logger.debug(f'Настройка клиента.')
        self.address, self.port, self.client_name = self.arg_parser()
        logger.info(f'Настроен клиент с парамертами: адрес сервера {self.address}, '
                    f'порт {self.port}, имя пользователя: {self.client_name}')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        system("title " + self.client_name)

    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
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

    def database_load(self):
        """Инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера."""
        # Инициализация БД
        self.database = ClientDatabase(self.client_name)
        # Загружаем список известных пользователей
        try:
            users_list = self.user_list()
        except Exception:
            logger.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(users_list)

        # Загружаем список контактов
        try:
            contacts_list = self.contacts_list()
        except Exception:
            logger.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts_list:
                self.database.add_contact(contact)

    @Log()
    def contacts_list(self):
        """Запрос контакт листа"""
        logger.debug(f'Запрос контакт листа для пользователся {self.client_name}')
        send_message(self.sock, self.create_sys_message(GET_CONTACTS))
        ans = get_message(self.sock)
        logger.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
        else:
            raise ValueError

    @Log()
    def user_list(self):
        """Запрос списка известных пользователей"""
        logger.debug(f'Запрос списка известных пользователей {self.client_name}')
        send_message(self.sock, self.create_sys_message(USERS_REQUEST))
        ans = get_message(self.sock)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
        else:
            raise ValueError

    # Функция изменеия контактов
    def edit_contacts(self):
        """Изменение контактов"""
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        self.add_contact(edit)
                    except Exception:
                        logger.error('Не удалось отправить информацию на сервер.')

    @Log()
    def add_contact(self, contact):
        """Добавления пользователя в контакт лист"""
        logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        send_message(self.sock, req)
        ans = get_message(self.sock)
        if RESPONSE not in ans or ans[RESPONSE] != 200:
            raise Exception('Ошибка создания контакта')

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
            USER: self.client_name
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
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(to_user):
                logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.client_name, to_user, message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {to_user}')
            except Exception as e:
                logger.critical(f'Потеряно соединение с сервером. {e}')
                sys.exit(1)

    @Log()
    def message_from_server(self):
        """Функция для обработки сообщений, поступающих с сервера"""
        while True:
            time.sleep(1)
            try:
                with sock_lock:
                    message = get_message(self.sock)
            except OSError as e:
                if e.errno:
                    logger.critical(f'Потеряно соединение с сервером. {e}')
                    break
            except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError) as e:
                logger.critical(f'Потеряно соединение с сервером. {e}')
                break
            else:
                if all([w in message for w in [ACTION, SENDER, DESTINATION, MESSAGE_TEXT]]) and \
                        message[ACTION] == MESSAGE and \
                        message[DESTINATION] == self.client_name:
                    mes = f'\nПолучено сообщение от пользователя {message[SENDER]}:' \
                          f'\n{message[MESSAGE_TEXT]}'
                    print(mes)
                    with database_lock:
                        try:
                            self.database.save_message(message[SENDER],
                                                       self.client_name,
                                                       message[MESSAGE_TEXT])
                        except:
                            logger.error('Ошибка взаимодействия с базой данных')
                    logger.info(mes)
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')

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
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_sys_message(EXIT))
                        print('Завершение соединения.')
                        logger.info('Завершение работы по команде пользователя.')
                        # Задержка неоходима, чтобы успело уйти сообщение о выходе
                    except:
                        pass
                    time.sleep(0.5)
                    break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def start(self):
        """Инициализация обмена с сервером."""
        try:
            self.sock.settimeout(1)  # Таймаут 1 секунда, необходим для освобождения сокета.
            self.sock.connect((self.address, self.port))
            send_message(self.sock, self.create_sys_message(PRESENCE))
            answer = self.process_ans(get_message(self.sock))
            logger.info(f'Принят ответ от сервера: {answer}')
            self.database_load()
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
