import importlib
import logging
from typing import Dict

import pkg_resources
from ehforwarderbot import Channel

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
        '''
        actual_path = __name__.rsplit('.', 1)[0]
        c = importlib.import_module('.' + name, actual_path + '.Clients.' + name)
        cls = getattr(c, name)
        self.client = cls(name, config, channel)
        '''
        try:
            for entry_point in pkg_resources.iter_entry_points('ehforwarderbot.qq.plugin'):
                if entry_point.name == name:
                    c = entry_point.load()
                    cls = getattr(c, name)
                    self.client = cls(name, config, channel)
                    return
        except:
            raise Exception("Specified client not found!")
        raise Exception("Specified client not found!")

    def get_client(self) -> BaseClient:
        return self.client
