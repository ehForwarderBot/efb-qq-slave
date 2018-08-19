import importlib
from typing import Dict

from ehforwarderbot import EFBChannel

from .Clients.BaseClient import BaseClient


class ClientMgr:
    client: BaseClient

    def __init__(self, name: str, config: Dict, channel):
        """
        This class initializes the QQ Client specified in config.yaml
        :param name:
        :param config:
        :param channel:
        """
        actual_path = __name__.rsplit('.', 1)[0]
        c = importlib.import_module('.' + name, actual_path + '.Clients.' + name)
        cls = getattr(c, name)
        self.client = cls(name, config, channel)

    def get_client(self) -> BaseClient:
        return self.client
