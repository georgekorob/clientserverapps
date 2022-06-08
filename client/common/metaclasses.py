import dis


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
