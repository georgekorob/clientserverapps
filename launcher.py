# Лаунчер

import subprocess
import os
import time

# env = os.environ.copy()
address = '127.0.0.1'
port = '7777'
path_python = '../clientserverappsvenv/Scripts/python.exe'
# path_python = '../venvs/clientserverapps/Scripts/python.exe'
PROCESS = []


def start_server():
    PROCESS.append(subprocess.Popen([path_python, 'server.py', '-a', address, '-p', port],
                                    creationflags=subprocess.CREATE_NEW_CONSOLE))


def start_clients(count):
    for i in range(count):
        PROCESS.append(subprocess.Popen([path_python, 'client.py', address, port, '-n', f'client{i + 1}'],
                                        creationflags=subprocess.CREATE_NEW_CONSOLE))


start_server()
start_clients(2)

while True:
    ACTION = input('Выберите действие:'
                   'q - выход, '
                   's - запустить сервер, '
                   # 'c - запустить клиенты, '
                   'x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        start_server()
    # elif ACTION == 'c':
        start_clients(2)
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
