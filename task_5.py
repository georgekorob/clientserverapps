"""
Задание 5.

Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
преобразовать результаты из байтовового в строковый тип на кириллице.

Подсказки:
--- используйте модуль chardet, иначе задание не засчитается!!!
"""
import subprocess
import chardet

for resource in ['yandex.ru', 'youtube.com']:
    ping_res = subprocess.Popen(['ping', resource], stdout=subprocess.PIPE)
    for line in ping_res.stdout:
        result = chardet.detect(line)
        line = line.decode(result['encoding'])
        line = line.encode('utf-8').decode('utf-8')
        print(line)
