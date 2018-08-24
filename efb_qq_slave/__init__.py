# coding: utf-8
import logging
import os
from typing import Optional, Dict, Any
import yaml
from gettext import translation
from ehforwarderbot import EFBChannel, ChannelType, EFBMsg, EFBStatus, EFBChat, MsgType
from ehforwarderbot import utils as efb_utils
from pkg_resources import resource_filename

from .Clients.BaseClient import BaseClient
from .ClientMgr import ClientMgr


class QQMessengerChannel(EFBChannel):
    channel_name: str = "QQ Slave"
    channel_emoji: str = "🐧"
    channel_id = "milkice.qq"
    channel_type: ChannelType = ChannelType.Slave

    supported_message_types = {MsgType.Text, MsgType.Sticker, MsgType.Image,
                               MsgType.Link, MsgType.Audio}

    # todo supported_message can be dynamically defined by Client

    config = dict()
    QQClientMgr: ClientMgr
    QQClient: BaseClient
    logger: logging.Logger = logging.getLogger(__name__)

    translator = translation("efb_qq_slave",
                             resource_filename('efb_qq_slave', 'locale'),
                             fallback=True)

    t = translator.gettext
    ngettext = translator.ngettext

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)
        """
        Load Config
        """
        self.load_config()

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
        pass

    def get_chat_picture(self, chat: 'EFBChat'):
        # todo, availability depends on client
        pass

    def get_chats(self):
        qq_chats = self.QQClient.get_friends()
        group_chats = self.QQClient.get_groups()
        return qq_chats+group_chats
        pass

    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None):
        # todo
        pass

    def stop_polling(self):
        # not sure how it works
        # todo Help Needed
        pass
