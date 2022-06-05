Client
=================================================

Клиентское приложение для обмена сообщениями, сообщения шифруются
с помощью алгоритма RSA с длинной ключа 2048 bit.

Поддерживает аргументы коммандной строки:

``python client.py {имя сервера} {порт} -n {имя пользователя} -p {пароль}``

1. {имя сервера} - адрес сервера сообщений.
2. {порт} - порт по которому принимаются подключения
3. -n или --name - имя пользователя с которым произойдёт вход в систему.
4. -p или --password - пароль пользователя.

Все опции командной строки являются необязательными,
но имя пользователя и пароль необходимо использовать в паре.

client.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и
функционал инициализации приложения.

client. **arg_parser** ()
    Парсер аргументов командной строки

database.py
~~~~~~~~~~~~~~

.. autoclass:: client.database.ClientDatabase
   :members:

transport.py
~~~~~~~~~~~~~~

.. autoclass:: client.transport.ClientTransport
   :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: client.main_window.ClientMainWindow
   :members:

start_dialog.py
~~~~~~~~~~~~~~~

.. autoclass:: client.start_dialog.UserNameDialog
   :members:


add_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.add_contact.AddContactDialog
   :members:


del_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.del_contact.DelContactDialog
   :members: