#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json

import client_cmdmanager
import tstutils


# Test-user account details
USR, PW = 'mail@hotmail.com', 'Hard_Password_Since_1985'


class CmdParserMock(client_cmdmanager.CommandParser):
    """
    Mock method _send_to_daemon with fixed return value, set by passing it to the constructor.
    """
    def __init__(self, daemon_return_value=None):
        client_cmdmanager.CommandParser.__init__(self)  # old style class
        self.daemon_return_value = daemon_return_value

    def _send_to_daemon(self, message=None):
        return self.daemon_return_value


def _fake_send_to_daemon(message):
    """
    This function emulate the send_to_daemon method of commandparser
    :return: the message received from client_daemon
    """
    if 'register' in message:
        # User creation validated
        if 'Str0ng_Password' in message['register'][1]:
            return {'content': 'Message relative successful user creation', 'successful': True}
        # User creation failed for weak password
        elif 'password' in message['register'][1]:
            return {'improvements': {'type_improvement': 'Relative info about this improvement'}, 'successful': False}
        # user creation of existent user
        elif 'existent_user' in message['register'][0]:
            return {'content': 'Message relative already existent user creation', 'successful': False}
        else:
            return {'Error': 'You must never came here!'}

    elif 'activate' in message:
        if 'valid_token' in message['activate'][1]:
            return {'content': 'Message relative successful activation of user', 'successful': True}
        if 'bad_token' in message['activate'][1]:
            return {'content': 'Message relative failed activation', 'successful': False}
        else:
            return {'Error': 'You must never came here!'}

    elif 'login' in message:
        if 'valid_user' in message['login'][0] and 'valid_pass' in message['login'][1]:
            return {'content': 'Message relative successful login of user', 'successful': True}
        elif 'valid_user' in message['login'][0] and 'bad_pass' in message['login'][1]:
            return {'content': 'Message relative failed login', 'successful': False}
        elif 'bad_user' in message['login'][0] and 'valid_pass' in message['login'][1]:
            return {'content': 'Message relative failed login', 'successful': False}
        elif 'bad_user' in message['login'][0] and 'bad_pass' in message['login'][1]:
            return {'content': 'Message relative failed login', 'successful': False}
        else:
            return {'Error': 'You must never came here!'}


class TestCmdManagerDaemonConnection(unittest.TestCase):
    """
    Test the connection between Cmd Manager and Daemon
    """
    def setUp(self):
        self.commandparser = client_cmdmanager.CommandParser()
        self.commandparser.sock = tstutils.FakeSocket()

    def test_sent_to_daemon_input(self):
        """
        Tests the string passed in input:
        test a long string
        """
        response = 'ciao sono test'
        self.commandparser.sock.set_response(json.dumps({'message': response}))
        input_str = 'input'

        self.assertEquals(self.commandparser._send_to_daemon(input_str), response)
        self.assertEquals(self.commandparser._send_to_daemon(input_str * 100000), response)

    def test_send_to_daemon_output(self):
        """
        Tests the string received:
        test a long string
        """
        input_str = 'input'
        response = 'ciao sono test'
        self.commandparser.sock.set_response(json.dumps({'message': response}))

        self.assertEquals(self.commandparser._send_to_daemon(input_str), response)

        self.commandparser.sock.set_response(json.dumps({'message': response * 100000}))

        self.assertEquals(self.commandparser._send_to_daemon(input_str), response * 100000)

    def test_do_register(self):
        """
        Test the successful creation of user
        :return: the response received from daemon
        """
        self.line = '{} {}'.format(USR, 'Str0ng_Password')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_register(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertNotIn('improvements', response)
        self.assertTrue(response['successful'])

    def test_do_register_with_weak_password(self):
        """
ò        Test a user registration with weak password.
        The server refuse registration and send a dictionary with inside the possible improvements for the password.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format(USR, 'password')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_register(self.line)
        self.assertNotIn('content', response)
        self.assertIsInstance(response['improvements'], dict)
        self.assertFalse(response['successful'])

    def test_do_register_with_user_already_existent(self):
        """
        Test a user registration with already existent user.
        The server refuse registration with error message and the client_daemon translate
        the error into message for client.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format('existent_user', PW)
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_register(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertNotIn('improvements', response)
        self.assertFalse(response['successful'])

    def test_do_register_with_bad_arguments(self):
        """
        Test the registration of user with bad arguments,
        :return: the response received from daemon
        """
        self.line = '{0} {0} {1}'.format(USR, PW)
        response = self.commandparser.do_register(self.line)
        self.assertFalse(response)
        self.line = '{0}'.format(USR, PW)
        response = self.commandparser.do_register(self.line)
        self.assertFalse(response)

    def test_do_activate(self):
        """
        Test the successful activation of user.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format(USR, 'valid_token')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_activate(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertTrue(response['successful'])

    def test_do_activate_with_bad_token(self):
        """
        Test do_activate with a bad token.
        The server refuse to create user and we received a False from client_daemon.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format(USR, 'bad_token')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_activate(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertFalse(response['successful'])

    def test_do_activate_with_bad_arguments(self):
        """
        Test the activation of user with bad arguments,
        :return: the response received from daemon

        """
        self.line = '{0} {0} {1}'.format(USR, PW)
        response = self.commandparser.do_activate(self.line)
        self.assertFalse(response)
        self.line = '{0}'.format(USR, PW)
        response = self.commandparser.do_activate(self.line)
        self.assertFalse(response)

    def test_do_login_with_valid_userdata(self):
        """
        Test the successful login of user.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format('valid_user', 'valid_pass')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_login(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertTrue(response['successful'])

    def test_do_login_with_bad_user(self):
        """
        Test do_login with a bad user but valid_pass.
        The server refuse to authenticate the user and we received a False from client_daemon.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format('bad_user', 'valid_pass')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_login(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertFalse(response['successful'])

    def test_do_login_with_bad_password(self):
        """
        Test do_login with a valid user but bad password.
        The server refuse to authenticate the user and we received a False from client_daemon.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format('valid_user', 'bad_pass')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_login(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertFalse(response['successful'])

    def test_do_login_with_bad_userdata(self):
        """
        Test do_login with a alla user data wrong.
        The server refuse to authenticate the user and we received a False from client_daemon.
        :return: the response received from daemon
        """
        self.line = '{} {}'.format('bad_user', 'bad_pass')
        self.commandparser._send_to_daemon = _fake_send_to_daemon
        response = self.commandparser.do_login(self.line)
        self.assertIsInstance(response['content'], str)
        self.assertFalse(response['successful'])

    def test_do_login_with_bad_arguments(self):
        """
        Test the activation of user with bad arguments,
        :return: the response received from daemon

        """
        self.line = '{0} {0} {1}'.format(USR, PW)
        response = self.commandparser.do_login(self.line)
        self.assertFalse(response)
        self.line = '{0}'.format(USR, PW)
        response = self.commandparser.do_login(self.line)
        self.assertFalse(response)

class TestDoQuitDoEOF(unittest.TestCase):
    """
    Test do_quit and EOF method
    """
    def setUp(self):
        self.commandparser = client_cmdmanager.CommandParser()
        self.line = 'linelinelineline'

    def test_do_quit(self):
        """
        Verify do_quit
        """
        self.assertTrue(self.commandparser.do_quit(self.line))

    def test_do_EOF(self):
        """
        Verify do_EOF
        """
        self.assertTrue(self.commandparser.do_EOF(self.line))


class TestRecoverpassEmail(unittest.TestCase):
    """
    Test 'recoverpass' command.
    """
    def setUp(self):
        self.commandparser = CmdParserMock()

    def test_recoverpass_empty_email(self):
        self.assertFalse(self.commandparser.do_recoverpass(''))

    def test_recoverpass_no_at_email(self):
        self.assertFalse(self.commandparser.do_recoverpass('invalid.mail'))

    def test_recoverpass_valid_mail(self):
        self.commandparser.daemon_return_value = 'Ok'
        self.assertTrue(self.commandparser.do_recoverpass('myemail@gmail.com'))


class TestRecoverpassEmailAndToken(unittest.TestCase):
    """
    Test 'changepass' command.
    """
    def setUp(self):
        self.valid_line = 'pippo.topolinia@gmail.com my_recoverpass_code'
        self.commandparser = CmdParserMock()

    def test_bad_args(self):
        self.assertFalse(self.commandparser.do_recoverpass('myemail@gmail.com activationcode extra-arg'))

    def test_password_unconfirmed(self):
        """
        If the new password is not confirmed, the command must fail.
        """
        client_cmdmanager._getpass = lambda: False
        self.assertFalse(self.commandparser.do_recoverpass(self.valid_line))  # because _getpass fail (return False)

    def test_invalid_code(self):
        client_cmdmanager._getpass = lambda: 'mynewpassword'
        # Assuming that a empty daemon return value means that the token is invalid.
        self.commandparser.daemon_return_value = ''
        self.assertFalse(self.commandparser.do_recoverpass(self.valid_line))

    def test_ok(self):
        # mock client_cmdmanager._getpass function
        client_cmdmanager._getpass = lambda: 'mynewpassword'
        self.commandparser.daemon_return_value = 'Password changed succesfully'
        self.assertTrue(self.commandparser.do_recoverpass(self.valid_line))


class TestValidateEmail(unittest.TestCase):
    def test_no_local_part(self):
        self.assertFalse(client_cmdmanager.validate_email('@gmail.com'))

    def test_no_domain(self):
        self.assertFalse(client_cmdmanager.validate_email('address@'))

    def test_too_many_at(self):
        self.assertFalse(client_cmdmanager.validate_email('address@@gmail.com'))

    def test_dot_at_begin_or_end(self):
        self.assertFalse(client_cmdmanager.validate_email('.address@gmail.com'))
        self.assertFalse(client_cmdmanager.validate_email('address.@gmail.com'))

    def test_no_dots_in_domain(self):
        self.assertFalse(client_cmdmanager.validate_email('address@gmailcom'))

    def test_consecutive_dots_in_domain_part(self):
        self.assertFalse(client_cmdmanager.validate_email('address@gmail..com'))

    def test_invalid_characters(self):
        for invalid in '^$/:?#[]':
            self.assertFalse(client_cmdmanager.validate_email('my{}address@gmail.com'.format(invalid)))


if __name__ == '__main__':
    unittest.main()
