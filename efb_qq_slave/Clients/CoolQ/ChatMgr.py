# coding: utf-8

import logging

from ehforwarderbot import EFBChat
from ehforwarderbot.constants import ChatType

from efb_qq_slave import QQMessengerChannel


class ChatManager:

    def __init__(self, channel: 'QQMessengerChannel'):
        self.channel: 'QQMessengerChannel' = channel
        self.logger: logging.Logger = logging.getLogger(__name__)

        self.MISSING_GROUP: EFBChat = EFBChat(self.channel)
        self.MISSING_GROUP.chat_uid = "__error__"
        self.MISSING_GROUP.chat_type = ChatType.Group
        self.MISSING_GROUP.chat_name = self.MISSING_GROUP.chat_alias = "Chat Missing"

        self.MISSING_USER: EFBChat = EFBChat(self.channel)
        self.MISSING_USER.chat_uid = "__error__"
        self.MISSING_USER.chat_type = ChatType.User
        self.MISSING_USER.chat_name = self.MISSING_USER.chat_alias = "Chat Missing"

    """
    def build_efb_chat_as_user(self, uid, is_chat, in_group=None, is_discuss=False):
        efb_chat = EFBChat(self.channel)
        efb_chat.chat_uid = 'user' + str(uid)
        i: dict = self.channel.QQClient.get_stranger_info(uid)
        efb_chat.chat_name = i['nickname']
        efb_chat.chat_alias = None
        efb_chat.chat_type = ChatType.User
        efb_chat.is_chat = is_chat
        efb_chat.vendor_specific = {'is_anonymous': False}
        if in_group is not None:
            efb_chat.group = self.build_efb_chat_as_group(in_group, is_discuss)
        return efb_chat

    def build_efb_chat_as_group(self, uid, discuss=False):
        efb_chat = EFBChat(self.channel)
        if not discuss:
            efb_chat.chat_uid = 'group' + str(uid)
            i = self.channel.QQClient.get_group_info(uid)
            efb_chat.chat_name = i['group_name']
            efb_chat.chat_type = ChatType.Group
            efb_chat.vendor_specific = {'is_discuss': False}
            # todo Add user to efb_chat.member
        else:
            efb_chat.chat_uid = 'discuss' + str(uid)
            efb_chat.chat_name = 'Discuss Group'  # todo Find a way to distinguish from different discuss group
            efb_chat.chat_type = ChatType.Group
            efb_chat.vendor_specific = {'is_discuss': True}
        return efb_chat

    def build_efb_chat_as_anonymous_user(self, nickname, flag, anonymous_id, group_id, is_discuss):
        efb_chat = EFBChat(self.channel)
        efb_chat.chat_uid = flag
        efb_chat.chat_name = nickname
        efb_chat.chat_type = ChatType.User
        efb_chat.is_chat = False
        efb_chat.vendor_specific = {'is_anonymous': True,
                                    'anonymous_id': anonymous_id}
        efb_chat.group = self.build_efb_chat_as_group(group_id, is_discuss)
        return efb_chat

    """

    def build_efb_chat_as_user(self, context, is_chat):
        efb_chat = EFBChat(self.channel)
        uid = context['user_id']
        efb_chat.chat_uid = 'private' + '_' + str(uid)
        chat_name = ''
        if 'nickname' not in context:
            i: dict = self.channel.QQClient.get_stranger_info(uid)
            chat_name = i['nickname']
        else:
            chat_name = context['nickname']
        efb_chat.chat_name = chat_name
        efb_chat.chat_alias = None if 'alias' not in context else context['alias']
        efb_chat.chat_type = ChatType.User
        efb_chat.is_chat = is_chat
        efb_chat.vendor_specific = {'is_anonymous': False}
        if not is_chat and context['message_type'] != 'private':
            efb_chat.group = self.build_efb_chat_as_group(context)
        return efb_chat

    def build_efb_chat_as_group(self, context):
        efb_chat = EFBChat(self.channel)
        efb_chat.chat_type = ChatType.Group
        is_discuss = False if context['message_type'] == 'group' else True
        chat_uid = context['discuss_id'] if is_discuss else context['group_id']
        if not is_discuss:
            efb_chat.chat_uid = 'group' + '_' + str(chat_uid)
            i = self.channel.QQClient.get_group_info(chat_uid)
            if i is not None:
                efb_chat.chat_name = i['group_name'] if 'group_name' not in context else context['group_name']
            else:
                efb_chat.chat_name = chat_uid
            efb_chat.vendor_specific = {'is_discuss': False}
            # todo Add user to efb_chat.member
        else:
            efb_chat.chat_uid = 'discuss' + '_' + str(chat_uid)
            efb_chat.chat_name = 'Discuss Group' + '_' + str(chat_uid)
            # todo Find a way to distinguish from different discuss group
            efb_chat.vendor_specific = {'is_discuss': True}
        return efb_chat

    def build_efb_chat_as_anonymous_user(self, context):
        efb_chat = EFBChat(self.channel)
        anonymous_data = context['anonymous']
        efb_chat.chat_uid = 'anonymous' + '_' + anonymous_data['flag']
        efb_chat.chat_name = '[Anonymous] ' + anonymous_data['name']
        efb_chat.chat_type = ChatType.User
        efb_chat.is_chat = False
        efb_chat.vendor_specific = {'is_anonymous': True,
                                    'anonymous_id': anonymous_data['id']}
        efb_chat.group = self.build_efb_chat_as_group(context)
        return efb_chat

    def build_efb_chat_as_system_user(self, context):  # System user only!
        efb_chat = EFBChat(self.channel).system()
        efb_chat.chat_type = ChatType.System
        efb_chat.chat_name = context['event_description']
        return efb_chat
