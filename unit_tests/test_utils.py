import json
import unittest
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from common.utils import get_message, send_message


class SocketEmulation:
    def __init__(self, dict_message):
        self.dict_message = dict_message
        self.encoded_message = None
        self.received_message = None

    def send(self, message):
        json_test_message = json.dumps(self.dict_message)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message

    def recv(self, length):
        json_test_message = json.dumps(self.dict_message)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    dict_send = {
        ACTION: PRESENCE,
        TIME: 1.1,
        USER: {
            ACCOUNT_NAME: 'Guest'
        }
    }
    dict_recv_ok = {RESPONSE: 200}
    dict_recv_err = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_message(self):
        socket = SocketEmulation(self.dict_send)
        send_message(socket, self.dict_send)
        self.assertEqual(socket.encoded_message, socket.received_message)

    def test_get_message_ok(self):
        socket_ok = SocketEmulation(self.dict_recv_ok)
        self.assertEqual(get_message(socket_ok), self.dict_recv_ok)

    def test_get_message_err(self):
        socket_err = SocketEmulation(self.dict_recv_err)
        self.assertEqual(get_message(socket_err), self.dict_recv_err)


if __name__ == '__main__':
    unittest.main()
