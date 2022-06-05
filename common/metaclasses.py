import dis


class ServerVerifier(type):
    """Метакласс для проверки соответствия сервера"""

    def __init__(self, clsname, bases, clsdict):
        methods = []
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
                # ret - generator object
            except TypeError:
                # Если не функция
                pass
            else:
                # Если функция разбираем код, получая используемые
                # методы и атрибуты.
                for i in ret:
                    # print(i)
                    # opname - имя для операции
                    # argval - название функции
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися
                            # в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися
                            # в функциях класса
                            attrs.append(i.argval)
        # print(methods)
        # Если обнаружено использование недопустимого метода connect,
        # бросаем исключение:
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо '
                            'в серверном классе')
        # Если сокет не инициализировался константами SOCK_STREAM(TCP)
        # AF_INET(IPv4), тоже исключение.
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        # Обязательно вызываем конструктор предка:
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    """Метакласс для проверки корректности клиентов"""

    def __init__(self, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                # Если не функция
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        # Если обнаружено использование недопустимого метода accept, listen,
        # socket бросаем исключение:
        for command in ('accept', 'listen'):  # , 'socket'
            if command in methods:
                raise TypeError(f'В классе обнаружено использование '
                                f'запрещённого метода {command}')
        # Вызов get_message или send_message из utils считаем корректным
        # использованием сокетов
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих '
                            'с сокетами.')
        super().__init__(clsname, bases, clsdict)
