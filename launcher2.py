# Лаунчер

import subprocess
import os
import time


venv = 'C:/Python/Python37/'
build = 'build/exe.win-amd64-3.7/'
path_python = f'{venv}python.exe'
for prog_name in ['server', 'client']:
    command = f'cd {prog_name}' \
              f' && {venv}python.exe setup_exe.py build' \
              f' && rd /s /q "{build}lib/sqlalchemy"' \
              f' && xcopy /e /y /r /i "{venv}Lib/site-packages/sqlalchemy" "{build}lib/sqlalchemy"' \
              f' && move /y "{build}lib/PyQt5/Qt/plugins/platforms" "{build}"'
    rc = subprocess.call(command, shell=True)
