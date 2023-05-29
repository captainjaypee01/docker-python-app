"""
    Arguments
    =========

    Contains helpers to parse application arguments

    .. Copyright:
        Copyright 2019 Wirepas Ltd licensed under Apache License, Version 2.0
        See file LICENSE for full license details.
"""

import argparse
import sys
import os
import yaml
from dotenv import load_dotenv
from .serialization_tools import serialize

class Settings:
    """Simple class to handle library settings"""

    def __init__(self, settings: dict):
        super(Settings, self).__init__()
        for k, v in settings.items():
            self.__dict__[k] = v

    def items(self):
        return self.__dict__.items()

    def __str__(self):
        return str(self.__dict__)


class ParserHelper:
    """
    ParserHelper

    Handles the creation and decoding of arguments

    """

    # These options are deprecated but might still be received through the
    # settings file
    _short_options = [
        "s",
        "p",
        "u",
        "pw",
        "t",
        "ua",
        "i",
        "fp",
        "gm",
        "gv",
        "iepf",
        "wepf",
    ]

    def __init__(
        self,
        description="argument parser",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        version=None,
    ):
        super(ParserHelper, self).__init__()
        self._parser = argparse.ArgumentParser(
            description=description, formatter_class=formatter_class
        )

        self._groups = dict()
        self._unknown_arguments = None
        self._arguments = None

        if version is not None:
            self.main.add_argument("--version", action="version", version=version)

    @property
    def parser(self):
        """ Returns the parser object """
        return self._parser

    @property
    def arguments(self):
        """ Returns arguments that it can parse and throwing an error otherwise """
        self._arguments = self.parser.parse_args()
        return self._arguments

    @property
    def known_arguments(self):
        """ returns the unknown arguments it could not parse """
        self._arguments, self._unknown_arguments = self.parser.parse_known_args()
        return self._arguments

    @property
    def unkown_arguments(self):
        """ returns the unknown arguments it could not parse """
        return self._unknown_arguments

    def settings(self, settings_class=None):
        """ Reads an yaml settings file and puts it through argparse """

        # Parse args from cmd line to see if a custom setting file is specified
        self._arguments = self.parser.parse_args()
        
        if self._arguments.settings is not None:
            with open(self._arguments.settings, "r") as f:
                settings = yaml.load(f, Loader=yaml.FullLoader)
                arglist = list()

                # Add the file parameters
                for key, value in settings.items():
                    if key in self._short_options:
                        key = "-{}".format(key)
                    else:
                        key = "--{}".format(key)

                    # We assume that booleans are always handled with
                    # store_true. This logic will fail otherwise.
                    if value is False:
                        continue

                    arglist.append(key)

                    # do not append True as the key is enough
                    if value is True:
                        continue
                    arglist.append(str(value))

                arguments = sys.argv
                argument_index = 1  # wm-gw
                if "python" in arguments[0]:  # pythonX transport (...)
                    if "-m" in arguments[1]:  # pythonX -m transport (...)
                        argument_index += 1
                    argument_index = +1
                # Add the cmd line parameters. They will override
                # parameters from file if set in both places.
                for arg in arguments[argument_index:]:
                    arglist.append(arg)

            # Override self._arguments as there are parameters from file
            self._arguments = self.parser.parse_args(arglist)

        if settings_class is None:
            settings_class = Settings

        settings = settings_class(self._arguments.__dict__)

        return settings

    def __getattr__(self, name):
        if name not in self._groups:
            self._groups[name] = self._parser.add_argument_group(name)

        return self._groups[name]

    @staticmethod
    def str2bool(value):
        """ Ensures string to bool conversion """
        if isinstance(value, bool):
            return value
        if value.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif value.lower() in ("no", "false", "f", "n", "0", ""):
            return False
        else:
            raise argparse.ArgumentTypeError("Boolean value expected.")

    @staticmethod
    def str2int(value):
        """ Ensures string to bool conversion """
        try:
            value = int(value)
        except ValueError:
            if value == "":
                value = 0
            else:
                raise argparse.ArgumentTypeError("Integer value expected.")
        return value

    @staticmethod
    def str2none(value):
        """ Ensures string to bool conversion """
        if value == "":
            return None
        return value

    def add_file_settings(self):
        """ For file setting handling"""
        self.file_settings.add_argument(
            "--settings",
            type=self.str2none,
            required=False,
            default=os.environ.get("WM_GW_FILE_SETTINGS", None),
            help="A yaml file with argument parameters (see help for options).",
        )

    def add_mqtt(self):
        """ Commonly used MQTT arguments """
        self.mqtt.add_argument(
            "--mqtt_hostname",
            default=os.environ.get("WM_SERVICES_MQTT_HOSTNAME", None),
            action="store",
            type=self.str2none,
            help="MQTT broker hostname.",
        )

        self.mqtt.add_argument(
            "--mqtt_username",
            default=os.environ.get("WM_SERVICES_MQTT_USERNAME", None),
            action="store",
            type=self.str2none,
            help="MQTT broker username.",
        )

        self.mqtt.add_argument(
            "--mqtt_password",
            default=os.environ.get("WM_SERVICES_MQTT_PASSWORD", None),
            action="store",
            type=self.str2none,
            help="MQTT broker password.",
        )

        self.mqtt.add_argument(
            "--mqtt_port",
            default=os.environ.get("WM_SERVICES_MQTT_PORT", 8883),
            action="store",
            type=self.str2int,
            help="MQTT broker port.",
        )

        self.mqtt.add_argument(
            "--mqtt_ca_certs",
            default=os.environ.get("WM_SERVICES_MQTT_CA_CERTS", None),
            action="store",
            type=self.str2none,
            help=(
                "Path to the Certificate "
                "Authority certificate files that "
                "are to be treated as trusted by "
                "this client."
            ),
        )

        self.mqtt.add_argument(
            "--mqtt_certfile",
            default=os.environ.get("WM_SERVICES_MQTT_CLIENT_CRT", None),
            action="store",
            type=self.str2none,
            help=("Path to the PEM encoded client certificate."),
        )

        self.mqtt.add_argument(
            "--mqtt_keyfile",
            default=os.environ.get("WM_SERVICES_MQTT_CLIENT_KEY", None),
            action="store",
            type=self.str2none,
            help=(
                "Path to the PEM "
                "encoded client private keys "
                "respectively."
            ),
        )

        self.mqtt.add_argument(
            "--mqtt_cert_reqs",
            default=os.environ.get("WM_SERVICES_MQTT_CERT_REQS", "CERT_REQUIRED"),
            choices=["CERT_REQUIRED", "CERT_OPTIONAL", "CERT_NONE"],
            action="store",
            type=self.str2none,
            help=(
                "Defines the certificate "
                "requirements that the client "
                "imposes on the broker."
            ),
        )

        self.mqtt.add_argument(
            "--mqtt_tls_version",
            default=os.environ.get("WM_SERVICES_MQTT_TLS_VERSION", "PROTOCOL_TLSv1_2"),
            choices=[
                "PROTOCOL_TLS",
                "PROTOCOL_TLS_CLIENT",
                "PROTOCOL_TLS_SERVER",
                "PROTOCOL_TLSv1",
                "PROTOCOL_TLSv1_1",
                "PROTOCOL_TLSv1_2",
            ],
            action="store",
            type=self.str2none,
            help=("Specifies the version of the SSL / TLS protocol to be used."),
        )

        self.mqtt.add_argument(
            "--mqtt_ciphers",
            default=os.environ.get("WM_SERVICES_MQTT_CIPHERS", None),
            action="store",
            type=self.str2none,
            help=(
                "A string specifying which "
                "encryption ciphers are allowable "
                "for this connection."
            ),
        )

        self.mqtt.add_argument(
            "--mqtt_persist_session",
            default=os.environ.get("WM_SERVICES_MQTT_PERSIST_SESSION", False),
            type=self.str2bool,
            nargs="?",
            const=True,
            help=(
                "When True the broker will buffer session packets "
                "between reconnection."
            ),
        )

        self.mqtt.add_argument(
            "--mqtt_force_unsecure",
            default=os.environ.get("WM_SERVICES_MQTT_FORCE_UNSECURE", False),
            type=self.str2bool,
            nargs="?",
            const=True,
            help=("When True the broker will skip the TLS handshake."),
        )

        self.mqtt.add_argument(
            "--mqtt_allow_untrusted",
            default=os.environ.get("WM_SERVICES_MQTT_ALLOW_UNTRUSTED", False),
            type=self.str2bool,
            nargs="?",
            const=True,
            help=("When true the client will skip the certificate name check."),
        )

        self.mqtt.add_argument(
            "--mqtt_reconnect_delay",
            default=os.environ.get("WM_SERVICES_MQTT_RECONNECT_DELAY", 0),
            action="store",
            type=self.str2int,
            help=(
                "Delay in seconds to try to reconnect when connection to"
                "broker is lost (0 to try forever)"
            ),
        )

        self.mqtt.add_argument(
            "--mqtt_max_inflight_messages",
            default=os.environ.get("WM_SERVICES_MQTT_MAX_INFLIGHT_MESSAGES", 20),
            action="store",
            type=self.str2int,
            help=("Max inflight messages for messages with qos > 0"),
        )

        self.mqtt.add_argument(
            "--mqtt_use_websocket",
            default=os.environ.get("WM_SERVICES_MQTT_USE_WEBSOCKET", False),
            type=self.str2bool,
            nargs="?",
            const=True,
            help=(
                "When true the mqtt client will use websocket instead of TCP for transport"
            ),
        )


    def dump(self, path):
        """ dumps the arguments into a file """
        with open(path, "w") as f:
            f.write(serialize(vars(self._arguments)))
