import unittest

from client.common.variables import RESPONSE, ERROR, TIME, USER, ACCOUNT_NAME, ACTION, PRESENCE
from server import Server


class TestServer(unittest.TestCase):
    return_error = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }
    return_ok = {RESPONSE: 200}
    server = Server()

    def test_no_action(self):
        self.assertEqual(self.server.process_client_message({TIME: '1.1',
                                                             USER: {ACCOUNT_NAME: ''}}),
                         self.return_error)

    def test_wrong_action(self):
        self.assertEqual(self.server.process_client_message({ACTION: 'not presence',
                                                             TIME: '1.1',
                                                             USER: {ACCOUNT_NAME: ''}}),
                         self.return_error)

    def test_no_time(self):
        self.assertEqual(self.server.process_client_message({ACTION: PRESENCE,
                                                             USER: {ACCOUNT_NAME: ''}}),
                         self.return_error)

    def test_no_user(self):
        self.assertEqual(self.server.process_client_message({ACTION: PRESENCE,
                                                             TIME: '1.1'}),
                         self.return_error)

    def test_unknown_user(self):
        self.assertEqual(self.server.process_client_message({ACTION: PRESENCE,
                                                             TIME: '1.1',
                                                             USER: {ACCOUNT_NAME: 'Unknown'}}),
                         self.return_error)

    def test_ok_check(self):
        self.assertEqual(self.server.process_client_message({ACTION: PRESENCE,
                                                             TIME: '1.1',
                                                             USER: {ACCOUNT_NAME: ''}}),
                         self.return_ok)


if __name__ == '__main__':
    unittest.main()
