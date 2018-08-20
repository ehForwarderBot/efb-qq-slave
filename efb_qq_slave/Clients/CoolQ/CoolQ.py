# coding: utf-8
import json
import logging
import tempfile
import threading
import uuid

from typing import Any, Dict

from PIL import Image
from ehforwarderbot import EFBMsg, MsgType, EFBChat, EFBChannel, coordinator

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

        @self.coolq_bot.on_message()
        def handle_msg(context):
            self.logger.debug(repr(context))
            msg_element = context['message']
            main_text: str = ''
            messages = []
            m = QQMsgProcessor(instance=self)
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
                    my_uid = self.get_qq_uid()
                    self.logger.debug('My QQ uid: %s\n'
                                      'QQ who is mentioned: %s\n', my_uid, msg_data['qq'])
                    # todo Recheck if bug exists
                    if str(my_uid) == str(msg_data['qq']) or str(msg_data['qq']) == 'all':
                        self_nickname = self.get_login_info()['data']['nickname']
                        substituion_begin = len(main_text) + 1
                        substituion_end = len(main_text) + len(self_nickname) + 2
                        main_text += ' @{} '.format(self_nickname)
                        at_list[(substituion_begin, substituion_end)] = EFBChat(self.channel).self()
                elif msg_type == 'location':
                    messages.append(m.qq_location_wrapper(msg_data))
                elif msg_type == 'shake':
                    messages.append(m.qq_shake_wrapper(msg_data))
                elif msg_type == 'contact':
                    messages.append(m.qq_contact_wrapper(msg_data))
                elif msg_type == 'music':
                    messages.append(m.qq_music_wrapper(msg_data))
                elif msg_type == 'image':
                    messages.append(m.qq_image_wrapper(msg_data))
                elif msg_type == 'record':
                    messages.append(m.qq_audio_wrapper(msg_data))
                elif msg_type == 'share':
                    messages.append(m.qq_share_wrapper(msg_data))
            if main_text != "":
                messages.append(m.qq_text_simple_wrapper(main_text, at_list))
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
                        context['alias'] = self.coolq_bot.get_group_member_info(group_id=g_id, user_id=u_id)['card']
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
                    threading.Thread(target=async_send_messages_to_master, args=args, kwargs=kwargs).run()

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

    def run_instance(self, *args, **kwargs):
        threading.Thread(target=self.coolq_bot.run, args=args, kwargs=kwargs, daemon=True).start()

    def relogin(self):
        self.coolq_bot.set_restart()

    def logout(self):
        raise NotImplementedError

    def login(self):
        raise NotImplementedError

    def get_stranger_info(self, user_id):
        return self.coolq_bot.get_stranger_info(user_id=user_id, no_cache=False)

    def get_login_info(self) -> Dict[Any, Any]:
        res = self.coolq_bot.get_status()
        if 'good' in res or 'online' in res:
            data = self.coolq_bot.get_login_info()
            return {'status': 0, 'data': {'uid': data['user_id'], 'nickname': data['nickname']}}
        else:
            return {'status': 1}

    def get_groups(self):
        # todo Add support for discuss group iteration
        res = self.coolq_bot.get_group_list()
        groups = []
        for i in range(len(res)):
            context = {'message_type': 'group',
                       'group_id': res[i]['group_id']}
            efb_chat = self.chat_manager.build_efb_chat_as_group(context)
            groups.append(efb_chat)
        return groups

    def get_friends(self):
        # Warning: Experimental API
        res = self.coolq_bot._get_friend_list()
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

    def get_qq_uid(self):
        res = self.get_login_info()
        if res['status'] == 0:
            return res['data']['uid']
        else:
            return None

    def get_group_member_info(self, group_id, user_id) -> tuple:
        res = self.coolq_bot.get_group_member_info(group_id=group_id, user_id=user_id, no_cache=True)
        return res
        pass

    def get_group_info(self, group_id):
        res = self.coolq_bot.get_group_list()
        for i in range(len(res)):
            if res[i]['group_id'] == group_id:
                return res[i]
        return None

    def coolq_send_message(self, msg_type, uid, message):
        keyword = msg_type if msg_type != 'private' else 'user'
        res = self.coolq_bot.send_msg(message_type=msg_type, **{keyword + '_id': uid}, message=message)
        return str(uuid.uuid4()) + '_' + str(res['message_id'])
