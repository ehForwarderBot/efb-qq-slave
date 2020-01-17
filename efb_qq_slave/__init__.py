# coding: utf-8
import json
import logging
import os
from typing import Optional, Dict, Any, BinaryIO, Collection

import requests
import yaml
from ehforwarderbot import Message, Status, Chat, MsgType
from ehforwarderbot import utils as efb_utils
from ehforwarderbot.channel import SlaveChannel
from ehforwarderbot.exceptions import EFBOperationNotSupported
from ehforwarderbot.types import MessageID, InstanceID, ChatID
from pkg_resources import parse_version

from . import __version__ as version
from .ClientMgr import ClientMgr
from .Clients.BaseClient import BaseClient


class QQMessengerChannel(SlaveChannel):
    def get_message_by_id(self, chat: 'Chat', msg_id: MessageID) -> Optional['Message']:
        raise EFBOperationNotSupported

    channel_name: str = "QQ Slave"
    channel_emoji: str = "🐧"
    channel_id = "milkice.qq"

    __version__ = version.__version__

    supported_message_types = {MsgType.Text, MsgType.Sticker, MsgType.Image,
                               MsgType.Link, MsgType.Voice, MsgType.Animation}

    # todo supported_message can be dynamically defined by Client

    config = dict()
    QQClientMgr: ClientMgr
    QQClient: BaseClient
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, instance_id: InstanceID = None):
        super().__init__(instance_id)
        self.load_config()
        self.init_client_manager()

    def check_updates(self):
        try:
            data = requests.get("https://pypi.org/pypi/efb-qq-slave/json")
            data_json = json.loads(data.text)
            latest_version = data_json['info']['version']
            self.logger.debug("The latest version is {version}".format(version=latest_version))
            if parse_version(self.__version__) < parse_version(latest_version):
                return latest_version
            else:
                return None
        except Exception:
            self.logger.warning("Failed to check updates")
            return None

    def load_config(self):
        """
        Load configuration from path specified by the framework.

        Configuration file is in YAML format.
        """
        config_path = efb_utils.get_config_path(self.channel_id)
        if not config_path.exists():
            return
        with config_path.open() as f:
            self.config: Dict[str, Any] = yaml.load(f)

    def init_client_manager(self):
        self.QQClientMgr = ClientMgr(self.config['Client'], self.config, self)
        self.QQClient = self.QQClientMgr.get_client()

    def poll(self):
        """
        Init ClientMgr
        """
        # not sure how it works
        # todo Help Needed
        pass

    def send_message(self, msg: 'Message') -> 'Message':
        return self.QQClient.send_message(msg)

    def send_status(self, status: 'Status'):
        return self.QQClient.send_status(status)

    def get_chat_picture(self, chat: 'Chat') -> BinaryIO:
        return self.QQClient.get_chat_picture(chat)

    def get_chats(self) -> Collection['Chat']:
        return self.QQClient.get_chats()

    def get_chat(self, chat_uid: ChatID) -> 'Chat':
        return self.QQClient.get_chat(chat_uid)

    def stop_polling(self):
        # not sure how it works
        # todo Help Needed
        pass

    def get_extra_functions(self):
        methods = {}
        for mName in dir(self.QQClient):
            if hasattr(self.QQClient, mName):
                m = getattr(self.QQClient, mName)
                if callable(m) and getattr(m, "extra_fn", False):
                    methods[mName] = m
        return methods

    def __getattr__(self, name):
        def method(*args, **kwargs):
            func = getattr(self.QQClient, name)
            if kwargs:
                return func(**kwargs)
            else:
                return func()
        return method
