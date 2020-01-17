# coding: utf-8
import contextlib
import logging

from ehforwarderbot import Chat
from ehforwarderbot.chat import GroupChat, PrivateChat, SystemChat
from ehforwarderbot.types import ChatID

from efb_qq_slave import QQMessengerChannel


class ChatManager:

    def __init__(self, channel: 'QQMessengerChannel'):
        self.channel: 'QQMessengerChannel' = channel
        self.logger: logging.Logger = logging.getLogger(__name__)

        self.MISSING_GROUP: GroupChat = GroupChat(
            channel=self.channel,
            uid=ChatID("__error_group__"),
            name="Group Missing"
        )

        self.MISSING_CHAT: PrivateChat = PrivateChat(
            channel=self.channel,
            uid=ChatID("__error_chat__"),
            name="Chat Missing"
        )

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

    def build_efb_chat_as_private(self, context):
        uid = context['user_id']
        if 'nickname' not in context:
            i: dict = self.channel.QQClient.get_stranger_info(uid)
            chat_name = ""
            if i:
                chat_name = i['nickname']
        else:
            chat_name = context['nickname']
        efb_chat = PrivateChat(channel=self.channel,
                               uid='private' + '_' + str(uid),
                               name=chat_name,
                               alias=None if 'alias' not in context else context['alias'])
        return efb_chat

    def build_or_get_efb_member(self, chat: Chat, context):
        member_uid = context['user_id']
        with contextlib.suppress(KeyError):
            return chat.get_member(member_uid)
        chat_name = ''
        if 'nickname' not in context:
            i: dict = self.channel.QQClient.get_stranger_info(member_uid)
            chat_name = ""
            if i:
                chat_name = i['nickname']
        else:
            chat_name = context['nickname']
        return chat.add_member(name=chat_name,
                               alias=None if 'alias' not in context else context['alias'],
                               uid=str(member_uid))

    def build_efb_chat_as_group(self, context):  # Should be cached
        is_discuss = False if context['message_type'] == 'group' else True
        chat_uid = context['discuss_id'] if is_discuss else context['group_id']
        efb_chat = GroupChat(
            channel=self.channel,
            uid=str(chat_uid)
        )
        if not is_discuss:
            efb_chat.chat_uid = 'group' + '_' + str(chat_uid)
            i = self.channel.QQClient.get_group_info(chat_uid)
            if i is not None:
                efb_chat.chat_name = i['group_name'] if 'group_name' not in context else context['group_name']
            else:
                efb_chat.chat_name = chat_uid
            efb_chat.vendor_specific = {'is_discuss': False}
            members = self.channel.QQClient.get_group_member_list(chat_uid, False)
            if members:
                for member in members:
                    efb_chat.add_member(name=member['card'], alias=member['nickname'], uid=member['user_id'])
        else:
            efb_chat.chat_uid = 'discuss' + '_' + str(chat_uid)
            efb_chat.chat_name = 'Discuss Group' + '_' + str(chat_uid)
            # todo Find a way to distinguish from different discuss group
            efb_chat.vendor_specific = {'is_discuss': True}
        return efb_chat

    def build_efb_chat_as_anonymous_user(self, chat: Chat, context):
        anonymous_data = context['anonymous']
        member_uid = 'anonymous' + '_' + anonymous_data['flag']
        with contextlib.suppress(KeyError):
            return chat.get_member(member_uid)
        chat_name = '[Anonymous] ' + anonymous_data['name']
        return chat.add_member(name=chat_name,
                               alias=None if 'alias' not in context else context['alias'],
                               uid=str(member_uid),
                               vendor_specific={'is_anonymous': True,
                                                'anonymous_id': anonymous_data['id']})

    def build_efb_chat_as_system_user(self, context):  # System user only!
        return SystemChat(channel=self.channel,
                          name=context['event_description'],
                          uid=ChatID("__{context[uid_prefix]}__".format(context=context)))
