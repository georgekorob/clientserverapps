import os
import sys
from cx_Freeze import setup, Executable

setup(
    name="message_server_korobanov",
    version="0.0.1",
    description="message_server_korobanov_project",
    packages=["common", "log", "server"],
    executables=[Executable('server_test.py',
                            # base='Win32GUI',
                            targetName='server.exe',
                            )]
)
