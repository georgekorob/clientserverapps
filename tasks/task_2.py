from ipaddress import ip_address
from task_1 import host_ping


def host_range_ping(start_ip='192.168.1.0', count=10):
    """
    Функция для перебора ip-адресов из заданного диапазона.
    Меняться должен только последний октет каждого адреса.
    По результатам проверки должно выводиться соответствующее сообщение.
    """
    last_oct = int(start_ip.split('.')[3])
    if (last_oct+count) > 254:
        raise OverflowError

    host_list = [str(ip_address(start_ip)+x) for x in range(count)]
    return host_ping(host_list)


if __name__ == "__main__":
    host_range_ping()


"""
192.168.1.0 недоступен
192.168.1.1 недоступен
192.168.1.2 недоступен
192.168.1.3 недоступен
192.168.1.4 доступен
192.168.1.5 недоступен
192.168.1.6 недоступен
192.168.1.7 недоступен
192.168.1.8 недоступен
192.168.1.9 недоступен
"""