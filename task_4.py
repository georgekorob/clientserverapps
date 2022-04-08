"""
Задание 4.

Преобразовать слова «разработка», «администрирование», «protocol»,
«standard» из строкового представления в байтовое и выполнить
обратное преобразование (используя методы encode и decode).

Подсказки:
--- используйте списки и циклы, не дублируйте функции
"""

for word in ['разработка', 'администрирование', 'protocol', 'standard']:
    print(type(word), word)
    word = word.encode('utf-8')
    print(type(word), word)
    word = word.decode('utf-8')
    print(type(word), word)
    print()
