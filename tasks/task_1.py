from ipaddress import ip_address
from subprocess import Popen, PIPE
import socket


def host_ping(list_address):
    """
    В функции с помощью утилиты ping будет проверяться доступность сетевых узлов.
    Аргументом функции является список, в котором каждый сетевой узел должен быть представлен
    именем хоста или ip-адресом.
    В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
    («Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью
    функции ip_address().
    """
    results = {'Доступные узлы': [], 'Недоступные узлы': []}
    for address in list_address:
        try:
            _ip_address = ip_address(address)
        except ValueError:
            _ip_address = ip_address(socket.gethostbyname(address))
        process = Popen(f"ping {_ip_address} -w 500 -n 1", shell=False, stdout=PIPE)
        process.wait()
        if process.returncode == 0:
            results['Доступные узлы'] += [str(address)]
            res_string = f'{address} доступен'
        else:
            results['Недоступные узлы'] += [str(address)]
            res_string = f'{address} недоступен'
        print(res_string)


if __name__ == '__main__':
    ip_addresses = ['yandex.ru', '2.2.2.2', '192.168.0.100', '192.168.0.101']
    host_ping(ip_addresses)

"""
yandex.ru доступен
2.2.2.2 недоступен
192.168.0.100 недоступен
192.168.0.101 недоступен
"""