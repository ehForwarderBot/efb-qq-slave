# coding: utf-8
import html
import json
import logging
import tempfile
import threading
import time
import uuid

from typing import Any, Dict, Callable

import cqhttp
from PIL import Image
from ehforwarderbot import EFBMsg, MsgType, EFBChat, EFBChannel, coordinator, ChatType
from ehforwarderbot.exceptions import EFBException, EFBMessageError, EFBChatNotFound, EFBOperationNotSupported
from requests import RequestException

from ... import QQMessengerChannel
from .ChatMgr import ChatManager
from .utils import qq_emoji_list, async_send_messages_to_master, process_quote_text, coolq_text_encode, \
    upload_image_smms
from ..BaseClient import BaseClient
from cqhttp import CQHttp
from .MsgDecorator import QQMsgProcessor


class CoolQ(BaseClient):
    client_name: str = "CoolQ Client"
    client_id: str = "CoolQ"
    client_config: Dict[str, Any]

    coolq_bot: CQHttp = None
    logger: logging.Logger = logging.getLogger(__name__)
    channel: QQMessengerChannel

    def __init__(self, client_id: str, config: Dict[str, Any], channel):
        super().__init__(client_id, config)
        self.client_config = config[self.client_id]
        self.coolq_bot = CQHttp(api_root=self.client_config['api_root'],
                                access_token=self.client_config['access_token']
                                )
        self.channel = channel
        self.chat_manager = ChatManager(channel)

        self.is_connected = False
        self.is_logged_in = False
        self.msg_decorator = QQMsgProcessor(instance=self)

        @self.coolq_bot.on_message()
        def handle_msg(context):
            self.logger.debug(repr(context))
            msg_element = context['message']
            main_text: str = ''
            messages = []
            qq_uid = context['user_id']
            at_list = {}
            for i in range(len(msg_element)):
                msg_type = msg_element[i]['type']
                msg_data = msg_element[i]['data']
                if msg_type == 'text':
                    main_text += msg_data['text']
                elif msg_type == 'face':
                    qq_face = int(msg_data['id'])
                    if qq_face in qq_emoji_list:
                        main_text += qq_emoji_list[qq_face]
                    else:
                        main_text += '\u2753'  # ❓
                elif msg_type == 'sface':
                    main_text += '\u2753'  # ❓
                elif msg_type == 'at':
                    # todo Recheck if bug exists
                    g_id = context['group_id']
                    my_uid = self.get_qq_uid()
                    self.logger.debug('My QQ uid: %s\n'
                                      'QQ who is mentioned: %s\n', my_uid, msg_data['qq'])
                    group_card = ''
                    if str(msg_data['qq']) == 'all':
                        group_card = 'all'
                    else:
                        member_info = self.coolq_api_query('get_group_member_info', group_id=g_id, user_id=msg_data['qq'])
                        group_card = member_info['card'] if member_info['card'] != '' else member_info['nickname']
                    self.logger.debug('Group card: {}'.format(group_card))
                    substitution_begin = len(main_text) + 1
                    substitution_end = len(main_text) + len(group_card) + 2
                    main_text += ' @{} '.format(group_card)
                    if str(my_uid) == str(msg_data['qq']) or str(msg_data['qq']) == 'all':
                        at_list[(substitution_begin, substitution_end)] = EFBChat(self.channel).self()
                else:
                    messages.append(self.call_msg_decorator(msg_type, msg_data))
            if main_text != "":
                messages.append(self.msg_decorator.qq_text_simple_wrapper(main_text, at_list))
            uid: str = str(uuid.uuid4())
            for i in range(len(messages)):
                if not isinstance(messages[i], EFBMsg):
                    continue
                efb_msg = messages[i]
                efb_msg.uid = uid + '_' + str(i)
                if qq_uid != '80000000':
                    if context['message_type'] == 'group':
                        g_id = context['group_id']
                        u_id = context['user_id']
                        context['alias'] = self.coolq_api_query('get_group_member_info', group_id=g_id, user_id=u_id)[
                            'card']
                        # context['alias'] = self.coolq_bot.get_group_member_info(group_id=g_id, user_id=u_id)['card']
                    if context['message_type'] == 'private':
                        pass  # todo
                    efb_msg.author: EFBChat = self.chat_manager.build_efb_chat_as_user(context, False)
                else:  # anonymous user in group
                    efb_msg.author: EFBChat = self.chat_manager.build_efb_chat_as_anonymous_user(context)

                if context['message_type'] == 'private':
                    efb_msg.chat: EFBChat = self.chat_manager.build_efb_chat_as_user(context, True)
                else:
                    efb_msg.chat: EFBChat = self.chat_manager.build_efb_chat_as_group(context)

                efb_msg.deliver_to = coordinator.master

                def send_message_wrapper(*args, **kwargs):
                    threading.Thread(target=async_send_messages_to_master, args=args, kwargs=kwargs).start()

                send_message_wrapper(efb_msg)

        @self.coolq_bot.on_notice('group_increase')
        def handle_group_msg(context):
            self.logger.debug(repr(context))
            # todo

        @self.coolq_bot.on_request('group', 'friend')
        def handle_request(context):
            self.logger.debug(repr(context))
            # todo

        self.run_instance(host=self.client_config['host'], port=self.client_config['port'], debug=False)

        # threading.Thread(target=self.check_running_status).start()
        self.check_status_periodically(threading.Event())

    def run_instance(self, *args, **kwargs):
        threading.Thread(target=self.coolq_bot.run, args=args, kwargs=kwargs, daemon=True).start()

    def relogin(self):
        self.coolq_api_query('set_restart')
        # self.coolq_bot.set_restart()

    def logout(self):
        raise NotImplementedError

    def login(self):
        return self.check_status_periodically(None)

    def get_stranger_info(self, user_id):
        return self.coolq_api_query('get_stranger_info', user_id=user_id, no_cache=False)
        # return self.coolq_bot.get_stranger_info(user_id=user_id, no_cache=False)

    def get_login_info(self) -> Dict[Any, Any]:
        res = self.coolq_bot.get_status()
        if 'good' in res or 'online' in res:
            data = self.coolq_bot.get_login_info()
            return {'status': 0, 'data': {'uid': data['user_id'], 'nickname': data['nickname']}}
        else:
            return {'status': 1}

    def get_groups(self):
        # todo Add support for discuss group iteration
        res = self.coolq_api_query('get_group_list')
        # res = self.coolq_bot.get_group_list()
        groups = []
        for i in range(len(res)):
            context = {'message_type': 'group',
                       'group_id': res[i]['group_id']}
            efb_chat = self.chat_manager.build_efb_chat_as_group(context)
            groups.append(efb_chat)
        return groups

    def get_friends(self):
        # Warning: Experimental API
        res = self.coolq_api_query('_get_friend_list')
        # res = self.coolq_bot._get_friend_list()
        users = []
        for i in range(len(res)):  # friend group
            for j in range(len(res[i]['friends'])):
                current_user = res[i]['friends'][j]
                txt = '[{}] {}'
                txt = txt.format(res[i]['friend_group_name'], current_user['remark'])
                if current_user['nickname'] == current_user['remark']:  # no remark name
                    context = {'user_id': str(current_user['user_id']),
                               'nickname': txt,
                               'alias': None}
                else:
                    context = {'user_id': str(current_user['user_id']),
                               'nickname': current_user['nickname'],
                               'alias': txt}
                efb_chat = self.chat_manager.build_efb_chat_as_user(context, True)
                users.append(efb_chat)
        return users
        pass

    def receive_message(self):
        # Replaced by handle_msg()
        pass

    def send_message(self, msg: EFBMsg):
        # todo Add support for edited message
        """
        self.logger.info("[%s] Sending message to WeChat:\n"
                         "uid: %s\n"
                         "Type: %s\n"
                         "Text: %s\n"
                         "Target Chat: %s\n"
                         "Target uid: %s\n",
                         msg.uid,
                         msg.chat.chat_uid, msg.type, msg.text, repr(msg.target.chat), msg.target.uid)
        """
        m = QQMsgProcessor(instance=self)
        chat_type = msg.chat.chat_uid.split('_')
        if msg.type in [MsgType.Text, MsgType.Link]:
            if isinstance(msg.target, EFBMsg):
                max_length = -1  # todo
                tgt_text = coolq_text_encode(process_quote_text(msg.target.text, max_length))
                user_type = msg.target.author.chat_uid.split('_')
                tgt_alias = ""
                if chat_type[0] != 'private' and not msg.target.author.is_self:
                    tgt_alias += m.coolq_code_at_wrapper(user_type[1])
                else:
                    tgt_alias = ""
                msg.text = "%s%s\n\n%s" % (tgt_alias, tgt_text, coolq_text_encode(msg.text))
            msg.uid = self.coolq_send_message(chat_type[0], chat_type[1], msg.text)
            self.logger.debug('[%s] Sent as a text message. %s', msg.uid, msg.text)
        elif msg.type in (MsgType.Image, MsgType.Sticker):  # todo Send text if the picture msg does contain text
            self.logger.info("[%s] Image/Sticker %s", msg.uid, msg.type)
            text = ''
            if not self.client_config['is_pro']:  # CoolQ Air
                if self.client_config['air_option']['upload_to_smms']:
                    text = '[Image] {}'.format(upload_image_smms(msg.file, msg.path)['url'])
                else:
                    text = '[Image]'
            else:
                if msg.type != MsgType.Sticker:
                    text += m.coolq_code_image_wrapper(msg.file, msg.path)
                else:
                    with tempfile.NamedTemporaryFile(suffix=".gif") as f:
                        img = Image.open(msg.file)
                        try:
                            alpha = img.split()[3]
                            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
                        except IndexError:
                            mask = Image.eval(img.split()[0], lambda a: 0)
                        img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
                        img.paste(255, mask)
                        img.save(f, transparency=255)
                        msg.file.close()
                        f.seek(0)
                        text += m.coolq_code_image_wrapper(f, f.name)
            msg.uid = self.coolq_send_message(chat_type[0], chat_type[1], text)
            if msg.text:
                self.coolq_send_message(chat_type[0], chat_type[1], msg.text)
        # todo More MsgType Support
        return msg

    def call_msg_decorator(self, msg_type: str, *args):
        func = getattr(self.msg_decorator, 'qq_{}_wrapper'.format(msg_type))
        return func(*args)

    def get_qq_uid(self):
        res = self.get_login_info()
        if res['status'] == 0:
            return res['data']['uid']
        else:
            return None

    def get_group_member_info(self, group_id, user_id):
        res = self.coolq_api_query('get_group_member_info', group_id=group_id, user_id=user_id, no_cache=True)
        # res = self.coolq_bot.get_group_member_info(group_id=group_id, user_id=user_id, no_cache=True)
        return res
        pass

    def get_group_info(self, group_id):
        res = self.coolq_api_query('get_group_list')
        # res = self.coolq_bot.get_group_list()
        for i in range(len(res)):
            if res[i]['group_id'] == group_id:
                return res[i]
        return None

    def coolq_send_message(self, msg_type, uid, message):
        keyword = msg_type if msg_type != 'private' else 'user'
        res = self.coolq_api_query('send_msg', message_type=msg_type, **{keyword + '_id': uid}, message=message)
        # res = self.coolq_bot.send_msg(message_type=msg_type, **{keyword + '_id': uid}, message=message)
        return str(uuid.uuid4()) + '_' + str(res['message_id'])

    def coolq_api_wrapper(self, func_name, **kwargs):
        try:
            func = getattr(self.coolq_bot, func_name)
            res = func(**kwargs)
        except RequestException as e:
            raise EFBOperationNotSupported('Unable to connect to CoolQ Client! Error Message:\n{}'.format(repr(e)))
        except cqhttp.Error as ex:
            raise EFBOperationNotSupported('CoolQ HTTP API encountered an error!\n'
                                           'Status Code:{} Return Code:{}'.format(ex.status_code, ex.retcode))
        else:
            return res

    def check_running_status(self):
        res = self.coolq_api_wrapper('get_status')
        if res['good'] or res['online']:
            return True
        else:
            raise EFBMessageError("CoolQ Client isn't working correctly!")

    def coolq_api_query(self, func_name, **kwargs):
        """ # Do not call get_status too frequently
        if self.check_running_status():
            return self.coolq_api_wrapper(func_name, **kwargs)
        """
        if self.is_logged_in and self.is_connected:
            return self.coolq_api_wrapper(func_name, **kwargs)
        else:
            self.deliver_alert_to_master('Your status is offline.\n'
                                         'You may try login with /login')

    def check_status_periodically(self, t_event):
        self.logger.debug('Start checking status...')
        flag = True
        interval = 300
        try:
            flag = self.check_running_status()
        except EFBOperationNotSupported as e:
            self.deliver_alert_to_master("We're unable to communicate with CoolQ Client.\n"
                                         "Please check the connection and credentials provided.\n"
                                         "{}".format(repr(e)))
            self.is_connected = False
            self.is_logged_in = False
            interval = 3600
        except EFBMessageError:
            self.deliver_alert_to_master('CoolQ is running in abnormal status.\n'
                                         'You may need to relogin your account or have a check in CoolQ Client.\n')
            self.is_connected = True
            self.is_logged_in = False
            interval = 3600
        else:
            if not flag:
                self.deliver_alert_to_master("We don't know why, but status check failed.\n"
                                             "Please enable debug mode and consult the log for more details.")
                self.is_connected = True
                self.is_logged_in = False
                interval = 3600
            else:
                self.logger.debug('Status: OK')
                self.is_connected = True
                self.is_logged_in = True

        if t_event is not None and not t_event.is_set():
            threading.Timer(interval, self.check_status_periodically, [t_event]).start()

    def deliver_alert_to_master(self, message: str):
        msg = EFBMsg()
        chat = EFBChat(self.channel).system()
        chat.chat_type = ChatType.System
        chat.chat_name = "CoolQ Alert"
        msg.chat = msg.author = chat
        msg.deliver_to = coordinator.master
        msg.type = MsgType.Text
        msg.uid = "__alert__.%s" % int(time.time())
        msg.text = message
        coordinator.send_message(msg)
