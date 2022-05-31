# Лаунчер

import subprocess
import os
import time

# env = os.environ.copy()
address = '127.0.0.1'
port = '7777'
# path_python = '../clientserverappsvenv/Scripts/python.exe'
path_python = '../venvs/clientserverapps/Scripts/python.exe'
PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen([path_python, 'server.py', '-a', address, '-p', port],
                                        creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(2):
            PROCESS.append(subprocess.Popen([path_python, 'client/client.py', address, port, '-n', f'client{i+1}'],
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
