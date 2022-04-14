# Утилиты

import json
from .variables import MAX_PACKAGE_LENGTH, ENCODING


def get_message(client):
    """
    Утилита приёма и декодирования сообщения. Получает словарь в виде строки в байтах, если принято что-то другое,
    то выдаёт ошибку значения.
    :param client: Клиент.
    :return: Декодирует байты и возвращает словарь.
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock, message):
    """
    Утилита кодирования и отправки сообщения. Принимает словарь и отправляет его.
    :param sock: Сокет.
    :param message: Словарь.
    """
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
