import logging
from ipaddress import ip_address

logger = logging.getLogger('server')


class Port:
    """Дескриптор для описания порта"""

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        try:
            if 1023 < value < 65536:
                instance.__dict__[self.name] = value
            else:
                raise ValueError
        except Exception as e:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}.'
                f'Допустимые адреса с 1024 до 65535.')
            exit(1)


class Address:
    """Дескриптор для описания адреса"""

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        try:
            instance.__dict__[self.name] = ip_address(value)
        except Exception as e:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего адреса {value}.')
            exit(1)
