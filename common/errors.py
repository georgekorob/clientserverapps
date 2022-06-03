class ServerError(Exception):
    """Исключение, для обработки ошибок сервера."""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
