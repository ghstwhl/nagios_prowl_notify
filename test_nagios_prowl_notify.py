#!/usr/bin/env python3
"""
Unit tests for nagios_prowl_notify.py
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import urllib.error
from io import StringIO

import nagios_prowl_notify


class TestGetPriority(unittest.TestCase):
    """Test the get_priority function."""

    def test_priority_from_state_critical(self):
        """Priority should be determined by CRITICAL state."""
        priority = nagios_prowl_notify.get_priority('RECOVERY', 'CRITICAL')
        self.assertEqual(priority, 1)

    def test_priority_from_state_down(self):
        """Priority should be determined by DOWN state."""
        priority = nagios_prowl_notify.get_priority('RECOVERY', 'DOWN')
        self.assertEqual(priority, 1)

    def test_priority_from_state_warning(self):
        """Priority should be determined by WARNING state."""
        priority = nagios_prowl_notify.get_priority('PROBLEM', 'WARNING')
        self.assertEqual(priority, 0)

    def test_priority_from_state_ok(self):
        """Priority should be determined by OK state."""
        priority = nagios_prowl_notify.get_priority('PROBLEM', 'OK')
        self.assertEqual(priority, -1)

    def test_priority_from_state_up(self):
        """Priority should be determined by UP state."""
        priority = nagios_prowl_notify.get_priority('PROBLEM', 'UP')
        self.assertEqual(priority, -1)

    def test_priority_from_state_unknown(self):
        """Priority should be determined by UNKNOWN state."""
        priority = nagios_prowl_notify.get_priority('PROBLEM', 'UNKNOWN')
        self.assertEqual(priority, 0)

    def test_priority_from_notification_type_problem(self):
        """When state is unknown, use notification type for priority."""
        priority = nagios_prowl_notify.get_priority('PROBLEM', 'SOMEUNKNOWNSTATE')
        self.assertEqual(priority, 1)

    def test_priority_from_notification_type_recovery(self):
        """Recovery notifications should have low priority."""
        priority = nagios_prowl_notify.get_priority('RECOVERY', 'UNKNOWNSTATE')
        self.assertEqual(priority, -1)

    def test_priority_from_notification_type_acknowledgement(self):
        """Acknowledgement notifications should have normal priority."""
        priority = nagios_prowl_notify.get_priority('ACKNOWLEDGEMENT', 'UNKNOWNSTATE')
        self.assertEqual(priority, 0)

    def test_priority_default_fallback(self):
        """Unknown notification type should default to 0."""
        priority = nagios_prowl_notify.get_priority('UNKNOWNTYPE', 'UNKNOWNSTATE')
        self.assertEqual(priority, 0)

    def test_priority_case_insensitive(self):
        """get_priority should handle lowercase input."""
        priority = nagios_prowl_notify.get_priority('problem', 'critical')
        self.assertEqual(priority, 1)


class TestSendProwl(unittest.TestCase):
    """Test the send_prowl function."""

    @patch('urllib.request.urlopen')
    def test_send_prowl_success(self, mock_urlopen):
        """Successful API call should not raise exception."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Should not raise exception
        nagios_prowl_notify.send_prowl(
            apikey='test_api_key',
            event='Test Event',
            description='Test Description',
            priority=1
        )

        # Verify urlopen was called
        self.assertTrue(mock_urlopen.called)

    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_send_prowl_non_200_response(self, mock_exit, mock_urlopen):
        """Non-200 response should trigger error and exit."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            nagios_prowl_notify.send_prowl(
                apikey='test_api_key',
                event='Test Event',
                description='Test Description'
            )
            
            # Check error message was printed
            self.assertIn('Prowl API error: HTTP 400', mock_stderr.getvalue())
        
        # Verify exit was called with code 1
        mock_exit.assert_called_with(1)

    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_send_prowl_http_error(self, mock_exit, mock_urlopen):
        """HTTP error should be handled and exit."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'url', 403, 'Forbidden', {}, None
        )

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            nagios_prowl_notify.send_prowl(
                apikey='invalid_key',
                event='Test Event',
                description='Test Description'
            )
            
            # Check error message was printed
            self.assertIn('Prowl API error: 403 Forbidden', mock_stderr.getvalue())
        
        # Verify exit was called with code 1
        mock_exit.assert_called_with(1)

    @patch('urllib.request.urlopen')
    @patch('sys.exit')
    def test_send_prowl_url_error(self, mock_exit, mock_urlopen):
        """URL error (connection failure) should be handled and exit."""
        mock_urlopen.side_effect = urllib.error.URLError('Connection refused')

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            nagios_prowl_notify.send_prowl(
                apikey='test_key',
                event='Test Event',
                description='Test Description'
            )
            
            # Check error message was printed
            self.assertIn('Prowl connection error:', mock_stderr.getvalue())
        
        # Verify exit was called with code 1
        mock_exit.assert_called_with(1)

    @patch('urllib.request.Request')
    @patch('urllib.request.urlopen')
    def test_send_prowl_request_parameters(self, mock_urlopen, mock_request):
        """Verify correct parameters are sent in the request."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        nagios_prowl_notify.send_prowl(
            apikey='my_api_key',
            event='My Event',
            description='My Description',
            priority=2
        )

        # Verify Request was created with correct URL
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'https://api.prowlapp.com/publicapi/add')
        
        # Verify request has correct headers
        self.assertIn('headers', call_args[1])
        self.assertEqual(
            call_args[1]['headers']['Content-Type'],
            'application/x-www-form-urlencoded'
        )


class TestMain(unittest.TestCase):
    """Test the main function."""

    @patch('nagios_prowl_notify.send_prowl')
    @patch('sys.argv', ['nagios_prowl_notify.py', 'host',
                        '--apikey', 'test_key',
                        '--notificationtype', 'PROBLEM',
                        '--hostname', 'server01',
                        '--hoststate', 'DOWN',
                        '--hostaddress', '192.168.1.10',
                        '--hostoutput', 'PING CRITICAL - Host unreachable',
                        '--datetime', 'Mon Jun 9 12:34:56 PDT 2026'])
    def test_main_host_notification(self, mock_send_prowl):
        """Test main function with host notification."""
        nagios_prowl_notify.main()

        # Verify send_prowl was called
        self.assertTrue(mock_send_prowl.called)
        
        # Get the call arguments
        call_args = mock_send_prowl.call_args
        event = call_args[0][1]
        description = call_args[0][2]
        priority = call_args[0][3]

        # Verify event message
        self.assertIn('PROBLEM Host Alert', event)
        self.assertIn('server01', event)
        self.assertIn('DOWN', event)

        # Verify description
        self.assertIn('Notification Type: PROBLEM', description)
        self.assertIn('Host: server01', description)
        self.assertIn('State: DOWN', description)
        self.assertIn('Address: 192.168.1.10', description)
        self.assertIn('PING CRITICAL', description)

        # Verify priority (DOWN state = priority 1)
        self.assertEqual(priority, 1)

    @patch('nagios_prowl_notify.send_prowl')
    @patch('sys.argv', ['nagios_prowl_notify.py', 'service',
                        '--apikey', 'test_key',
                        '--notificationtype', 'RECOVERY',
                        '--servicedesc', 'HTTP',
                        '--hostalias', 'webserver',
                        '--hostaddress', '10.0.0.5',
                        '--servicestate', 'OK',
                        '--serviceoutput', 'HTTP OK: HTTP/1.1 200 OK',
                        '--datetime', 'Mon Jun 9 13:45:00 PDT 2026'])
    def test_main_service_notification(self, mock_send_prowl):
        """Test main function with service notification."""
        nagios_prowl_notify.main()

        # Verify send_prowl was called
        self.assertTrue(mock_send_prowl.called)
        
        # Get the call arguments
        call_args = mock_send_prowl.call_args
        event = call_args[0][1]
        description = call_args[0][2]
        priority = call_args[0][3]

        # Verify event message
        self.assertIn('RECOVERY Service Alert', event)
        self.assertIn('webserver/HTTP', event)
        self.assertIn('OK', event)

        # Verify description
        self.assertIn('Notification Type: RECOVERY', description)
        self.assertIn('Service: HTTP', description)
        self.assertIn('Host: webserver', description)
        self.assertIn('Address: 10.0.0.5', description)
        self.assertIn('State: OK', description)
        self.assertIn('HTTP OK: HTTP/1.1 200 OK', description)

        # Verify priority (OK state = priority -1)
        self.assertEqual(priority, -1)

    @patch('nagios_prowl_notify.send_prowl')
    @patch('sys.argv', ['nagios_prowl_notify.py', 'service',
                        '--apikey', 'test_key',
                        '--notificationtype', 'PROBLEM',
                        '--servicedesc', 'MySQL',
                        '--hostalias', 'db-server',
                        '--hostaddress', '10.0.0.20',
                        '--servicestate', 'CRITICAL',
                        '--serviceoutput', 'Connection refused',
                        '--datetime', 'Mon Jun 9 14:00:00 PDT 2026'])
    def test_main_critical_service(self, mock_send_prowl):
        """Test critical service notification has high priority."""
        nagios_prowl_notify.main()

        call_args = mock_send_prowl.call_args
        priority = call_args[0][3]
        
        # CRITICAL state should have priority 1 (high)
        self.assertEqual(priority, 1)

    @patch('sys.argv', ['nagios_prowl_notify.py'])
    def test_main_no_subcommand(self):
        """Test main exits when no subcommand is provided."""
        with patch('sys.stderr', new_callable=StringIO):
            with self.assertRaises(SystemExit) as cm:
                nagios_prowl_notify.main()
            
            # Should exit with code 2
            self.assertEqual(cm.exception.code, 2)

    @patch('sys.argv', ['nagios_prowl_notify.py', 'host', '--apikey', 'test'])
    def test_main_missing_required_args(self):
        """Test main exits when required arguments are missing."""
        with patch('sys.stderr', new_callable=StringIO):
            with self.assertRaises(SystemExit) as cm:
                nagios_prowl_notify.main()
            
            # ArgumentParser exits with code 2 for invalid arguments
            self.assertEqual(cm.exception.code, 2)


class TestBuildCommonArgs(unittest.TestCase):
    """Test the build_common_args function."""

    def test_build_common_args_returns_parser(self):
        """build_common_args should return an ArgumentParser."""
        parser = nagios_prowl_notify.build_common_args()
        self.assertIsNotNone(parser)
        # ArgumentParser instance check
        self.assertTrue(hasattr(parser, 'add_argument'))


if __name__ == '__main__':
    unittest.main()
