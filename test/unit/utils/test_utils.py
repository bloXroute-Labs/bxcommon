import sys
import unittest

from mock import patch

from bxcommon.utils import ip_resolver


class UtilsTests(unittest.TestCase):

    def setUp(self) -> None:
        sys.argv = [sys.argv[0]]

    def mock_env_config(self, key: str):
        if key == "external_port":
            return 9001

    def mocked_requests_get(*args):
        class MockResponse:
            body = ""

            def __init__(self, data):
                self.data = data

        if args[2] == "VALID_URL":
            return MockResponse(b'Current IP Address: 135.84.167.43')
        elif args[2] == "INVALID_URL":
            raise ConnectionError(b'Connection aborted - connection reset by peer')
        elif args[2] == "INVALID_IP":
            return MockResponse(b'No ip returned')

    @patch("bxcommon.utils.config.get_env_default")
    @patch("bxcommon.utils.config.append_manifest_args")
    @patch("bxcommon.utils.ip_resolver.get_node_public_ip")
    @patch("bxcommon.utils.ip_resolver.blocking_resolve_ip")
    def test_use_default_external_ip_command_line_arg(self, mock_blocking_resolve_ip, mock_get_node_public_ip,
                                                      mock_append_manifest_args, mock_get_env_default):
        from bxcommon.utils import cli
        cli._args = None

        default_external_ip = "99.99.99.99"
        mock_get_env_default.side_effect = self.mock_env_config
        mock_get_node_public_ip.return_value = default_external_ip
        mock_blocking_resolve_ip.return_value = default_external_ip
        mock_append_manifest_args.side_effect = lambda opts: opts
        sys.argv.append("--sdn-url=0.0.0.0")
        parse_args = cli.parse_arguments(cli.get_argument_parser())

        self.assertEqual(default_external_ip, parse_args.__dict__["external_ip"])
        mock_get_node_public_ip.assert_called_once()
        mock_blocking_resolve_ip.assert_called_once()

    @patch("bxcommon.utils.config.get_env_default")
    @patch("bxcommon.utils.config.append_manifest_args")
    @patch("bxcommon.utils.ip_resolver.get_node_public_ip")
    @patch("bxcommon.utils.ip_resolver.blocking_resolve_ip")
    def test_set_external_ip_via_command_line_arg(self, mock_blocking_resolve_ip, mock_get_node_public_ip,
                                                  mock_append_manifest_args, mock_get_env_default):
        from bxcommon.utils import cli
        cli._args = None

        custom_external_ip = "1.1.1.1"
        mock_get_env_default.side_effect = self.mock_env_config
        mock_blocking_resolve_ip.return_value = custom_external_ip
        mock_append_manifest_args.side_effect = lambda opts: opts

        sys.argv.append("--external-ip={}".format(custom_external_ip))
        sys.argv.append("--sdn-url=0.0.0.0")
        parse_args = cli.parse_arguments(cli.get_argument_parser())

        self.assertEqual(custom_external_ip, parse_args.__dict__["external_ip"])
        mock_get_node_public_ip.assert_not_called()
        mock_get_node_public_ip.assert_not_called()
        mock_blocking_resolve_ip.called_once_with(custom_external_ip)

    @patch("urllib3.PoolManager.request")
    @patch("bxcommon.constants.PUBLIC_IP_ADDR_RESOLVER", "VALID_URL")
    def test_get_node_public_ip_with_valid_url(self, mock_get):
        mock_get.side_effect = self.mocked_requests_get

        public_ip = ip_resolver.get_node_public_ip()

        self.assertEqual("135.84.167.43", public_ip)
        mock_get.assert_called_once_with("GET", "VALID_URL")

    @patch("urllib3.PoolManager.request")
    @patch("bxcommon.constants.PUBLIC_IP_ADDR_RESOLVER", "INVALID_URL")
    def test_get_node_public_ip_raising_connection_exception(self, mock_get):
        mock_get.side_effect = self.mocked_requests_get

        with self.assertRaises(SystemExit) as system_exit:
            public_ip = ip_resolver.get_node_public_ip()

        self.assertTrue(system_exit.exception.code, 1)

    @patch("urllib3.PoolManager.request")
    @patch("bxcommon.constants.PUBLIC_IP_ADDR_RESOLVER", "INVALID_IP")
    def test_get_node_public_ip_with_no_ip_in_response(self, mock_get):
        mock_get.side_effect = self.mocked_requests_get

        with self.assertRaises(SystemExit) as system_exit:
            public_ip = ip_resolver.get_node_public_ip()

        self.assertTrue(system_exit.exception.code, 1)
