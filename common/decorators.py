import inspect
import sys
import logging
import traceback
import datetime
from socket import socket

import log.server_log_config
import log.client_log_config

LOGGER = logging.getLogger('server_logger') if sys.argv[0].find(
    'server') != -1 else logging.getLogger('client_logger')


class Log:
    """Класс-декоратор для логирования вызовов функций."""

    def __call__(self, func_to_log):
        def decorated(*args, **kwargs):
            """Обертка"""
            func = func_to_log(*args, **kwargs)
            LOGGER.debug(
                f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                f'Функция {func_to_log.__name__}() '
                f'c параметрами {args}, {kwargs} '
                f'вызвана из модуля {func_to_log.__module__} '
                f'функцией {inspect.stack()[1][3]}.', stacklevel=2)
            return func

        return decorated


def login_required(func):
    """Проверка авторизации на сервере."""

    def checker(*args, **kwargs):
        # Импортировать необходимо тут, иначе ошибка рекурсивного импорта.
        from server.core import MessageProcessor
        from common.variables import ACTION, PRESENCE
        # проверяем, что первый аргумент - экземпляр MessageProcessor
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
                            break
            if not found:
                # В этом случае надо проверить, что передаваемые аргументы
                # имеют presence сообщение.
                for arg in args:
                    if isinstance(arg, dict):
                        if ACTION in arg and arg[ACTION] == PRESENCE:
                            found = True
                            break
            # Если не авторизован и нет сообщения начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
