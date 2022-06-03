import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
from common.descriptors import Port, Host
from common.variables import *
from common.utils import send_message, get_message
from common.decorators import login_required

# Загрузка логера
logger = logging.getLogger('server_logger')


class MessageProcessor(threading.Thread):
    '''Процессор сервера для обработки. Работает в качестве отдельного потока.'''
    port = Port()
    address = Host()

    def __init__(self, listen_address, listen_port, database):
        # Параментры подключения
        self.address, self.port = listen_address, listen_port
        self.database = database
        self.clients = []

        # Сокеты
        self.sock = None
        self.listen_sockets = None
        self.error_sockets = None

        self.running = True
        self.names = dict()
        super().__init__()

    @login_required
    def process_client_message(self, message, client):
        """
        Валидация ответа от клиента.
        :param message: Словарь-сообщение от клинта
        :param client:
        :return: Словарь-ответ для клиента
        """
        logger.debug(f'Разбор сообщения от клиента : {message}')
        if all([w in message for w in [ACTION, TIME, USER]]):
            user = message[USER]
            # Если это сообщение о присутствии, принимаем и отвечаем
            if message[ACTION] == PRESENCE:
                self.autorize_user(message, client)

            # Запрос контакт-листа
            elif message[ACTION] == GET_CONTACTS and \
                 self.names[user] == client:
                response = RESPONSE_202
                response[LIST_INFO] = self.database.get_contacts(user)
                self.try_send_message(client, response)

            # Добавление контакта
            elif message[ACTION] == ADD_CONTACT and \
                    ACCOUNT_NAME in message and \
                    self.names[user] == client:
                self.database.add_contact(user, message[ACCOUNT_NAME])
                self.try_send_message(client, RESPONSE_200)

            # Удаление контакта
            elif message[ACTION] == REMOVE_CONTACT and \
                    ACCOUNT_NAME in message and \
                    self.names[user] == client:
                self.database.remove_contact(user, message[ACCOUNT_NAME])
                self.try_send_message(client, RESPONSE_200)

            # Logout
            elif message[ACTION] == EXIT and \
                    self.names[user] == client:
                self.remove_client(client)

            # Запрос известных пользователей
            elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                    and self.names[message[ACCOUNT_NAME]] == client:
                response = RESPONSE_202
                response[LIST_INFO] = [user[0] for user in self.database.users_list()]
                self.try_send_message(client, response)

            # Сообщение
            elif message[ACTION] == MESSAGE and \
                    all([w in message for w in [DESTINATION, MESSAGE_TEXT]]) and \
                    self.names[user] == client:
                if message[DESTINATION] in self.names:
                    self.database.process_message(user, message[DESTINATION])
                    self.process_message(message)
                    self.try_send_message(client, RESPONSE_200)
                else:
                    response = RESPONSE_400
                    response[ERROR] = 'Пользователь не зарегистрирован на сервере.'
                    self.try_send_message(client, response)

            # Запрос публичного ключа пользователя
            elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST:
                response = RESPONSE_511
                response[DATA] = self.database.get_pubkey(user)
                if response[DATA]:
                    self.try_send_message(client, response)
                else:
                    response = RESPONSE_400
                    response[ERROR] = 'Нет публичного ключа для данного пользователя'
                    self.try_send_message(client, response)
            return

        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен.'
        self.try_send_message(client, response)

    def process_message(self, message):
        """
        Функция адресной отправки сообщения определённому клиенту.
        :param message: Словарь - сообщение
        :param names: Словарь клиентов
        :param listen_socks:
        """
        # отправляем сообщения, ожидающим клиентам
        if message[DESTINATION] in self.names:
            if self.names[message[DESTINATION]] in self.listen_sockets:
                try:
                    send_message(self.names[message[DESTINATION]], message)
                    logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                                f'от пользователя {message[USER]}.')
                except OSError:
                    self.remove_client(message[DESTINATION])
            else:
                logger.error(f'Связь с клиентом {message[DESTINATION]} была потеряна. '
                             f'Соединение закрыто, доставка невозможна.')
                self.remove_client(self.names[message[DESTINATION]])
            return
        logger.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                     f'отправка сообщения невозможна.')
        raise ConnectionError

    def run(self):
        '''Метод основной цикл потока.'''
        logger.debug(f'Запуск сервера.')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.address, self.port))
        self.sock.settimeout(0.5)
        # Слушаем порт
        self.sock.listen()

        # Основной цикл программы сервера
        while self.running:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst, self.listen_sockets, self.error_sockets = [], [], []

            # наличие ожидающих клиентов
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err.errno}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message),
                                                    client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.debug(f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)

    def try_send_message(self, client, response):
        try:
            send_message(client, response)
        except OSError:
            self.remove_client(client)

    def remove_client(self, client):
        '''Обработчик клиента с которым прервана связь.'''
        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def autorize_user(self, message, sock):
        '''Авторизция пользователей.'''
        logger.debug(f'Start auth process for {message[USER]}')
        if message[USER] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                logger.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                logger.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.database.check_user(message[USER]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован.'
            try:
                logger.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            logger.debug('Correct username, starting passwd check.')
            # Иначе отвечаем 511 и проводим процедуру авторизации
            message_auth = RESPONSE_511
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth[DATA] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем серверную версию ключа
            hash = hmac.new(self.database.get_hash(message[USER]), random_str, 'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            # Если ответ клиента корректный, то сохраняем его в список пользователей.
            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.names[message[USER]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER])
                # добавляем пользователя в список активных и если у него изменился открытый ключ
                self.database.user_login(
                    message[USER],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        '''Отправка сервисного сообщения 205 клиентам.'''
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
