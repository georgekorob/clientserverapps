from sqlalchemy import create_engine, Table, Column, Integer, String, \
    MetaData, ForeignKey, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
import datetime
from sqlalchemy.sql import default_comparator


class ServerStorage:
    """Серверная база данных:"""

    class AllUsers:
        """Отображение таблицы всех пользователей
        Экземпляр этого класса = запись в таблице AllUsers"""

        def __init__(self, username, password_hash):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.password_hash = password_hash
            self.pubkey = None
            self.id = None

    class ActiveUsers:
        """Отображение таблицы активных пользователей:
        Экземпляр этого класса = запись в таблице ActiveUsers"""

        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        """Отображение таблицы истории входов
        Экземпляр этого класса = запись в таблице LoginHistory"""

        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class UsersContacts:
        """Отображение таблицы контактов пользователей"""

        def __init__(self, user, contact):
            self.id = None
            self.user = user  # Владелец
            self.contact = contact  # Клиент

    class UsersHistory:
        """Отображение таблицы истории действий"""

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # Создаём движок базы данных
        self.database_engine = create_engine(
            f'sqlite:///{path}', echo=False,
            pool_recycle=7200,
            connect_args={'check_same_thread': False})

        # Создаём объект MetaData
        self.metadata = MetaData()

        # Создаём таблицу пользователей
        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime),
                            Column('password_hash', String),
                            Column('pubkey', Text))

        # Создаём таблицу активных пользователей
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'),
                                          unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime))

        # Создаём таблицу истории входов
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String))

        # Создаём таблицу контактов пользователей
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id')))

        # Создаём таблицу истории пользователей
        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer))

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Если в таблице активных пользователей есть записи, то их необходимо
        # удалить
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port, key):
        """Вход пользователя, записываем в базу факт входа"""
        print(username, ip_address, port)
        # Запрос в таблицу пользователей на наличие там пользователя с таким
        # именем
        rez = self.session.query(self.AllUsers).filter_by(name=username)

        # Если имя пользователя уже присутствует в таблице, обновляем время
        # последнего входа.
        # Если клиент прислал новый ключ, сохраняем его.
        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        # Теперь можно создать запись в таблицу активных пользователей о
        # факте входа.
        self.session.add(self.ActiveUsers(user.id, ip_address, port,
                                          datetime.datetime.now()))
        # и сохранить в историю входов
        self.session.add(
            self.LoginHistory(user.id, datetime.datetime.now(), ip_address,
                              port))
        # Сохраняем изменения
        self.session.commit()

    def add_user(self, name, password_hash):
        '''Регистрация пользователя.'''
        user_row = self.AllUsers(name, password_hash)
        self.session.add(user_row)
        self.session.commit()
        self.session.add(self.UsersHistory(user_row.id))
        self.session.commit()

    def remove_user(self, name):
        '''Удаление пользователя из базы.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(name=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.AllUsers).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        '''Хэша пароля пользователя.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.password_hash

    def get_pubkey(self, name):
        '''Публичный ключ пользователя.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        '''Существование пользователя.'''
        return bool(
            self.session.query(self.AllUsers).filter_by(name=name).count())

    def user_logout(self, username):
        """Фиксируем отключение пользователя."""
        # Запрашиваем выходящего пользователя
        user = self.session.query(self.AllUsers).filter_by(
            name=username).first()
        # Удаляем его из таблицы активных пользователей.
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        # Применяем изменения
        self.session.commit()

    def process_message(self, sender, recipient):
        """Фиксирует передачу сообщения и делает соответствующие
        отметки в БД"""
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.AllUsers).filter_by(
            name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(
            name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UsersHistory).filter_by(
            user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(
            user=recipient).first()
        recipient_row.accepted += 1
        self.session.commit()

    def add_contact(self, user, contact):
        """Добавление контакта."""
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(
            name=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(
                user=user.id, contact=contact.id).count():
            return
        self.session.add(self.UsersContacts(user.id, contact.id))
        self.session.commit()

    def remove_contact(self, user, contact):
        """Удаление контакта."""
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(
            name=contact).first()

        if not contact:
            return
        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id).delete()
        self.session.commit()

    def users_list(self):
        """Список известных пользователей со временем последнего входа."""
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login)
        # Возвращаем список кортежей
        return query.all()

    def active_users_list(self):
        """Возвращает список активных пользователей"""
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес,
        # порт, время.
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()

    def login_history(self, username=None):
        """Возвращающает историю входов по пользователю или всем
        пользователям"""
        # Запрашиваем историю входа
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    def get_contacts(self, username):
        """Возвращает список контактов пользователя."""
        # Запрашивааем указанного пользователя
        user = self.session.query(self.AllUsers).filter_by(name=username).one()
        # Запрашиваем его список контактов
        query = self.session.query(self.UsersContacts, self.AllUsers.name). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)
        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    def message_history(self):
        """Количество переданных и полученных сообщений"""
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()


if __name__ == '__main__':
    test_db = ServerStorage('../databases/server_base.db3')
    # выполняем 'подключение' пользователя
    test_db.user_login('client_1', '192.168.1.4', 8888, 'fdg')
    test_db.user_login('client_2', '192.168.1.5', 7777, 'fdsg')
    # выводим список кортежей - активных пользователей
    print(test_db.active_users_list())
    # выполянем 'отключение' пользователя
    test_db.user_logout('client_1')
    # выводим список активных пользователей
    print(test_db.active_users_list())
    # запрашиваем историю входов по пользователю
    test_db.login_history('client_1')
    # выводим список известных пользователей
    print(test_db.users_list())
