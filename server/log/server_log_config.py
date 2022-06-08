import logging.handlers
import os
import sys
from common.variables import LOGGING_FILE_LEVEL, LOGGING_STREAM_LEVEL

FORMATTER = logging.Formatter(
    '%(asctime)s %(levelname)s %(filename)s %(message)s')

sys.path.append('../../')
PATH = os.getcwd()
PATH = os.path.join(PATH, 'log/server.log')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(LOGGING_STREAM_LEVEL)

FILE_HANDLER = logging.handlers.TimedRotatingFileHandler(
    PATH, encoding='utf8', interval=1, when='D')
FILE_HANDLER.setFormatter(FORMATTER)
FILE_HANDLER.setLevel(LOGGING_FILE_LEVEL)

LOGGER = logging.getLogger('server_logger')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(FILE_HANDLER)
LOGGER.setLevel(logging.DEBUG)

if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
