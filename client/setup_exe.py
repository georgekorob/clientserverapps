import sys
from cx_Freeze import setup, Executable

setup(
    name="message_client_korobanov",
    version="0.0.1",
    description="message_client_korobanov_project",
    packages=["common", "log", "client"],
    executables=[Executable('client_test.py',
                            # base='Win32GUI',
                            targetName='client.exe',
                            )]
)
