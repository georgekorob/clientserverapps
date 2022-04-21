# Лаунчер

import subprocess
import os
import time

env = os.environ.copy()
env['PATH'] = '../venvs/clientservervenv/Scripts'
address = '127.0.0.1'
port = '8888'

PROCESS = []

# while True:
#     ACTION = input('Выберите действие: q - выход, '
#                    's - запустить сервер и клиенты, x - закрыть все окна: ')
#
#     if ACTION == 'q':
#         break
#     elif ACTION == 's':
PROCESS.append(subprocess.Popen(['python', 'server.py', '-a', address, '-p', port],
                                creationflags=subprocess.CREATE_NEW_CONSOLE,
                                env=env))
for i in range(3):
    PROCESS.append(subprocess.Popen(['python', 'client.py', address, port],
                                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                                    env=env))
#         elif ACTION == 'x':
time.sleep(10)
while PROCESS:
    VICTIM = PROCESS.pop()
    VICTIM.kill()
