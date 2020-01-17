# coding: utf-8

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, BinaryIO, Collection

from ehforwarderbot import Message, Status, Chat
from ehforwarderbot.types import ChatID


class BaseClient(ABC):
    client_name: str = "Example Client"
    client_id: str = "Client"
    client_config: Dict[str, Any]

    def __init__(self, client_id: str, config: Dict[str, Any]):
        self.client_id = client_id
        self.client_config = config

    @abstractmethod
    def login(self):
        raise NotImplementedError

    @abstractmethod
    def logout(self):
        raise NotImplementedError

    @abstractmethod
    def relogin(self):
        raise NotImplementedError

    @abstractmethod
    def send_message(self, msg: 'Message') -> 'Message':
        raise NotImplementedError

    @abstractmethod
    def send_status(self, status: 'Status'):
        raise NotImplementedError

    @abstractmethod
    def receive_message(self):
        raise NotImplementedError

    @abstractmethod
    def get_friends(self):
        raise NotImplementedError

    @abstractmethod
    def get_groups(self):
        raise NotImplementedError

    @abstractmethod
    def get_login_info(self) -> Dict[Any, Any]:
        """Retrieve Client Info
        :rtype: Dict
        status =>
            0 => Logged In
            1 => Not Logged In
        If status == 0 then
        data =>
            uid => User QQ Id
            nickname => User nickname
        """
        raise NotImplementedError

    """
    @abstractmethod
    def get_stranger_info(self, user_id):
        raise NotImplementedError
    """

    def get_stranger_info(self, user_id):
        raise NotImplementedError

    def get_group_info(self, group_id, no_cache=True):
        raise NotImplementedError

    def get_chat_picture(self, chat: 'Chat') -> BinaryIO:
        raise NotImplementedError

    def get_chat(self, chat_uid: ChatID) -> 'Chat':
        raise NotImplementedError

    def get_chats(self) -> Collection['Chat']:
        raise NotImplementedError

    def get_group_member_list(self, group_id, no_cache=True):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError
