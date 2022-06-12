import inspect
import sys
import logging
import datetime
from socket import socket

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
                f'вызвана из модуля {func_to_log.__module__}')
                # f'функцией {inspect.stack()[1][3]}.', stacklevel=2
            return func

        return decorated
