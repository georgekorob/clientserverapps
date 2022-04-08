"""
Задание 1.

Каждое из слов «разработка», «сокет», «декоратор» представить
в буквенном формате и проверить тип и содержание соответствующих переменных.
Затем с помощью онлайн-конвертера преобразовать
в набор кодовых точек Unicode (НО НЕ В БАЙТЫ!!!)
и также проверить тип и содержимое переменных.

Подсказки:
--- 'разработка' - буквенный формат
--- '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430' - набор кодовых точек
--- используйте списки и циклы, не дублируйте функции
"""

for word in ['разработка', 'сокет', 'декоратор']:
    print(type(word), word)
    # .encode("unicode_escape").decode('utf-8') - Аналогичен онлайн конвертеру
    word_code = word.encode("unicode_escape").decode('utf-8')
    print(type(word_code), word_code)
    print()
