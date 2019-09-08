# coding: utf-8
import logging
import os
import requests
from typing import Optional, Dict, Any
import yaml
import json
from pkg_resources import parse_version

from gettext import translation
from ehforwarderbot import EFBChannel, ChannelType, EFBMsg, EFBStatus, EFBChat, MsgType
from ehforwarderbot import utils as efb_utils
from pkg_resources import resource_filename
from . import __version__ as version

from .Clients.BaseClient import BaseClient
from .ClientMgr import ClientMgr


class QQMessengerChannel(EFBChannel):
    channel_name: str = "QQ Slave"
    channel_emoji: str = "🐧"
    channel_id = "milkice.qq"
    channel_type: ChannelType = ChannelType.Slave

    __version__ = version.__version__

    supported_message_types = {MsgType.Text, MsgType.Sticker, MsgType.Image,
                               MsgType.Link, MsgType.Audio, MsgType.Animation}

    # todo supported_message can be dynamically defined by Client

    config = dict()
    QQClientMgr: ClientMgr
    QQClient: BaseClient
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)
        """
        Load Config
        """
        self.load_config()

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
        if not os.path.exists(config_path):
            return
        with open(config_path) as f:
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
        self.init_client_manager()
        pass

    def send_message(self, msg: 'EFBMsg'):
        return self.QQClient.send_message(msg)

    def send_status(self, status: 'EFBStatus'):
        return self.QQClient.send_status(status)

    def get_chat_picture(self, chat: 'EFBChat'):
        return self.QQClient.get_chat_picture(chat)

    def get_chats(self):
        return self.QQClient.get_chats()

    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None):
        return self.QQClient.get_chat(chat_uid, member_uid)

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
