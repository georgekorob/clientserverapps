import unittest
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import Client


class TestClient(unittest.TestCase):
    client = Client()

    def test_create_presence(self):
        test = self.client.create_presence()
        test[TIME] = 1.1
        self.assertEqual(test,
                         {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_in_presence(self):
        test = self.client.create_presence()
        self.assertIn(ACTION, test)
        self.assertIn(TIME, test)
        self.assertIn(USER, test)
        self.assertIn(ACCOUNT_NAME, test[USER])

    def test_presence_user(self):
        test = self.client.create_presence()
        self.assertEqual(test[USER][ACCOUNT_NAME], 'Guest')

    def test_process_ans_200(self):
        self.assertEqual(self.client.process_ans({RESPONSE: 200}),
                         '200 : OK')

    def test_process_ans_400(self):
        self.assertEqual(self.client.process_ans({RESPONSE: 400,
                                                  ERROR: 'Bad Request'}),
                         '400 : Bad Request')

    def test_no_response(self):
        self.assertRaises(ValueError,
                          self.client.process_ans,
                          {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
