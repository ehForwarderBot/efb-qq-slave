# coding: utf-8
import logging
import tempfile
import threading
import time
import uuid
import requests
from typing import IO, Any, Dict, Optional, List, Tuple

import cqhttp
from PIL import Image
from cqhttp import CQHttp
from ehforwarderbot import EFBMsg, MsgType, EFBChat, coordinator, EFBStatus
from ehforwarderbot.exceptions import EFBMessageError, EFBOperationNotSupported, EFBChatNotFound
from ehforwarderbot.message import EFBMsgCommands, EFBMsgCommand
from ehforwarderbot.status import EFBMessageRemoval
from ehforwarderbot.utils import extra
from requests import RequestException
from gettext import translation
from pkg_resources import resource_filename

from .ChatMgr import ChatManager
from .Exceptions import CoolQDisconnectedException, CoolQAPIFailureException, CoolQOfflineException, \
    CoolQUnknownException
from .MsgDecorator import QQMsgProcessor
from .Utils import qq_emoji_list, async_send_messages_to_master, process_quote_text, coolq_text_encode, \
    upload_image_smms, download_file_from_qzone, download_user_avatar, download_group_avatar, \
    get_friend_list_via_qq_show, upload_image_vim_cn, upload_image_mi, upload_image_sogou
from ..BaseClient import BaseClient
from ... import QQMessengerChannel


class CoolQ(BaseClient):
    client_name: str = "CoolQ Client"
    client_id: str = "CoolQ"
    client_config: Dict[str, Any]

    coolq_bot: CQHttp = None
    logger: logging.Logger = logging.getLogger(__name__)
    channel: QQMessengerChannel

    translator = translation("efb_qq_slave",
                             resource_filename('efb_qq_slave', 'Clients/CoolQ/locale'),
                             fallback=True)

    _ = translator.gettext
    ngettext = translator.ngettext

    friend_list = []
    group_list = []
    discuss_list = []
    extra_group_list = []
    repeat_counter = 0
    update_repeat_counter = 0

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
                                      'QQ mentioned: %s\n', my_uid, msg_data['qq'])
                    group_card = ''
                    if str(msg_data['qq']) == 'all':
                        group_card = 'all'
                    else:
                        member_info = self.coolq_api_query('get_group_member_info',
                                                           group_id=g_id,
                                                           user_id=msg_data['qq'])
                        group_card = member_info['card'] if member_info['card'] != '' else member_info['nickname']
                    self.logger.debug('Group card: {}'.format(group_card))
                    substitution_begin = 0
                    substitution_end = 0
                    if main_text == '':
                        substitution_begin = len(main_text)
                        substitution_end = len(main_text) + len(group_card) + 1
                        main_text += '@{} '.format(group_card)
                    else:
                        substitution_begin = len(main_text) + 1
                        substitution_end = len(main_text) + len(group_card) + 2
                        main_text += ' @{} '.format(group_card)
                    if str(my_uid) == str(msg_data['qq']) or str(msg_data['qq']) == 'all':
                        at_list[(substitution_begin, substitution_end)] = EFBChat(self.channel).self()
                else:
                    messages.extend(self.call_msg_decorator(msg_type, msg_data))
            if main_text != "":
                messages.append(self.msg_decorator.qq_text_simple_wrapper(main_text, at_list))
            uid: str = str(uuid.uuid4())
            coolq_msg_id = context['message_id']
            for i in range(len(messages)):
                if not isinstance(messages[i], EFBMsg):
                    continue
                efb_msg = messages[i]
                efb_msg.uid = uid + '_' + str(coolq_msg_id) + '_' + str(i)
                # if qq_uid != '80000000':
                if 'anonymous' not in context or context['anonymous'] is None:
                    remark = self.get_friend_remark(qq_uid)
                    if context['message_type'] == 'group':
                        if context['sub_type'] == 'notice':
                            context['event_description'] = self._("System Notification")
                            efb_msg.author = self.chat_manager.build_efb_chat_as_system_user(context)
                        else:
                            if remark is not None:
                                context['nickname'] = remark
                            g_id = context['group_id']
                            member_info = self.coolq_api_query('get_group_member_info',
                                                               group_id=g_id,
                                                               user_id=qq_uid)
                            if member_info is not None:
                                context['alias'] = member_info['card']
                            efb_msg.author: EFBChat = self.chat_manager.build_efb_chat_as_user(context, False)
                    else:
                        if context['message_type'] == 'private' or context['message_type'] == 'discuss':
                            context['alias'] = remark
                        efb_msg.author: EFBChat = self.chat_manager.build_efb_chat_as_user(context, False)
                else:  # anonymous user in group
                    efb_msg.author: EFBChat = self.chat_manager.build_efb_chat_as_anonymous_user(context)

                if context['message_type'] == 'private':
                    efb_msg.chat: EFBChat = self.chat_manager.build_efb_chat_as_user(context, True)
                else:
                    efb_msg.chat: EFBChat = self.chat_manager.build_efb_chat_as_group(context)

                # Append discuss group into group list
                if context['message_type'] == 'discuss' and efb_msg.chat not in self.discuss_list:
                    self.discuss_list.append(efb_msg.chat)

                efb_msg.deliver_to = coordinator.master

                def send_message_wrapper(*args, **kwargs):
                    threading.Thread(target=async_send_messages_to_master, args=args, kwargs=kwargs).start()

                send_message_wrapper(efb_msg)

        @self.coolq_bot.on_notice('group_increase')
        def handle_group_increase_msg(context):
            context['event_description'] = self._('\u2139 Group Member Increase Event')
            if (context['sub_type']) == 'invite':
                text = self._('{nickname}({context[user_id]}) joined the group({group_name}) via invitation')
            else:
                text = self._('{nickname}({context[user_id]}) joined the group({group_name})')

            original_group = self.get_group_info(context['group_id'], False)
            group_name = context['group_id']
            if original_group is not None and 'group_name' in original_group:
                group_name = original_group['group_name']
            text = text.format(nickname=self.get_stranger_info(context['user_id'])['nickname'],
                               context=context,
                               group_name=group_name)

            context['message'] = text
            self.send_efb_group_notice(context)

        @self.coolq_bot.on_notice('group_decrease')
        def handle_group_decrease_msg(context):
            context['event_description'] = self._("\u2139 Group Member Decrease Event")
            original_group = self.get_group_info(context['group_id'], False)
            group_name = context['group_id']
            if original_group is not None and 'group_name' in original_group:
                group_name = original_group['group_name']
            text = ''
            if context['sub_type'] == 'kick_me':
                text = self._("You've been kicked from the group({})").format(group_name)
            else:
                if context['sub_type'] == 'leave':
                    text = self._('{nickname}({context[user_id]}) quited the group({group_name})')
                else:
                    text = self._('{nickname}({context[user_id]}) was kicked from the group({group_name})')
                text = text.format(nickname=self.get_stranger_info(context['user_id'])['nickname'],
                                   context=context,
                                   group_name=group_name)
            context['message'] = text
            self.send_efb_group_notice(context)

        @self.coolq_bot.on_notice('group_upload')
        def handle_group_file_upload_msg(context):
            context['event_description'] = self._("\u2139 Group File Upload Event")

            original_group = self.get_group_info(context['group_id'], False)
            group_name = context['group_id']
            if original_group is not None and 'group_name' in original_group:
                group_name = original_group['group_name']

            file_info_msg = self._('File ID: {file[id]}\n'
                                   'Filename: {file[name]}\n'
                                   'File size: {file[size]}').format(file=context['file'])
            member_info = self.coolq_api_query('get_group_member_info',
                                               group_id=context['group_id'],
                                               user_id=context['user_id'])
            group_card = member_info['card'] if member_info['card'] != '' else member_info['nickname']
            text = self._('{member_card}({context[user_id]}) uploaded a file to group({group_name})\n')
            text = text.format(member_card=group_card,
                               context=context,
                               group_name=group_name) + file_info_msg
            context['message'] = text
            self.send_efb_group_notice(context)

            cred = self.coolq_api_query('get_credentials')
            cookies = cred['cookies']
            csrf_token = cred['csrf_token']
            param_dict = {
                'context': context,
                'cookie': cookies,
                'csrf_token': csrf_token,
                'uin': self.get_qq_uid(),
                'group_id': context['group_id'],
                'file_id': context['file']['id'],
                'filename': context['file']['name'],
                'file_size': context['file']['size']
            }

            threading.Thread(target=self.async_download_file, args=[], kwargs=param_dict).start()

        @self.coolq_bot.on_notice('friend_add')
        def handle_friend_add_msg(context):
            context['event_description'] = self._('\u2139 New Friend Event')
            context['uid_prefix'] = 'friend_add'
            text = self._('{nickname}({context[user_id]}) has become your friend!')
            text = text.format(nickname=self.get_stranger_info(context['user_id'])['nickname'],
                               context=context)
            context['message'] = text
            self.send_msg_to_master(context)

        @self.coolq_bot.on_request('friend')  # Add friend request
        def handle_add_friend_request(context):
            self.logger.debug(repr(context))
            context['event_description'] = self._('\u2139 New Friend Request')
            context['uid_prefix'] = 'friend_request'
            text = self._('{nickname}({context[user_id]}) wants to be your friend!\n'
                          'Here is the verification comment:\n'
                          '{context[comment]}')
            text = text.format(nickname=self.get_stranger_info(context['user_id'])['nickname'],
                               context=context)
            context['message'] = text
            commands = [EFBMsgCommand(
                name=self._("Accept"),
                callable_name="process_friend_request",
                kwargs={'result': 'accept',
                        'flag': context['flag']}
            ), EFBMsgCommand(
                name=self._("Decline"),
                callable_name="process_friend_request",
                kwargs={'result': 'decline',
                        'flag': context['flag']}
            )]
            context['commands'] = commands
            self.send_msg_to_master(context)

        @self.coolq_bot.on_request('group')
        def handle_group_request(context):
            self.logger.debug(repr(context))
            context['group_name'] = self._('[Request]') + self.get_group_info(context['group_id'])['group_name']
            context['group_id_orig'] = context['group_id']
            context['group_id'] = str(context['group_id']) + "_notification"
            context['message_type'] = 'group'
            context['event_description'] = '\u2139 New Group Join Request'
            original_group = self.get_group_info(context['group_id'], False)
            group_name = context['group_id']
            if original_group is not None and 'group_name' in original_group:
                group_name = original_group['group_name']
            msg = EFBMsg()
            msg.uid = 'group' + '_' + str(context['group_id'])
            msg.author = self.chat_manager.build_efb_chat_as_system_user(context)
            msg.chat = self.chat_manager.build_efb_chat_as_group(context)
            msg.deliver_to = coordinator.master
            msg.type = MsgType.Text
            name = ""
            if not self.get_friend_remark(context['user_id']):
                name = "{}({})[{}] ".format(
                    self.get_stranger_info(context['user_id'])['nickname'], self.get_friend_remark(context['user_id']),
                    context['user_id'])
            else:
                name = "{}[{}] ".format(self.get_stranger_info(context['user_id'])['nickname'], context['user_id'])
            msg.text = "{} wants to join the group {}({}). \nHere is the comment: {}".format(
                name, group_name, context['group_id_orig'], context['comment']
            )
            msg.commands = EFBMsgCommands([EFBMsgCommand(
                name=self._("Accept"),
                callable_name="process_group_request",
                kwargs={'result': 'accept',
                        'flag': context['flag'],
                        'sub_type': context['sub_type']}
            ), EFBMsgCommand(
                name=self._("Decline"),
                callable_name="process_group_request",
                kwargs={'result': 'decline',
                        'flag': context['flag'],
                        'sub_type': context['sub_type']}
            )])
            coordinator.send_message(msg)

        self.run_instance(host=self.client_config['host'], port=self.client_config['port'], debug=False)

        # threading.Thread(target=self.check_running_status).start()
        self.check_status_periodically(threading.Event())
        self.check_self_update(threading.Event())
        threading.Timer(1800, self.update_contacts_periodically, [threading.Event()]).start()

    def run_instance(self, *args, **kwargs):
        threading.Thread(target=self.coolq_bot.run, args=args, kwargs=kwargs, daemon=True).start()

    @extra(name=_("Restart CoolQ Client"),
           desc=_("Force CoolQ to restart\n"
                  "Usage: {function_name} [-l] [-c] [-e]\n"
                  "    -l: Restart and clean log\n"
                  "    -c: Restart and clean cache\n"
                  "    -e: Restart and clean event\n"))
    def relogin(self, param: str = ""):
        param_dict = dict()
        if param:
            params = param.split(' ')
            for each_param in params:
                if each_param == ' ':
                    continue
                if each_param == '-l':
                    param_dict['clean_log'] = 'true'
                elif each_param == '-c':
                    param_dict['clean_cache'] = 'true'
                elif each_param == '-e':
                    param_dict['clean_event'] = 'true'
                else:
                    return self._("Unknown parameter: {}.").format(param)
        self.logger.debug(repr(param_dict))
        self.coolq_api_query('_set_restart', **param_dict)
        return 'Done. Please wait for a while.'

    def logout(self):
        raise NotImplementedError

    @extra(name=_("Check CoolQ Status"),
           desc=_("Force efb-qq-slave to refresh status from CoolQ Client.\n"
                  "Usage: {function_name}"))
    def login(self, param: str = ""):
        self.check_status_periodically(None)
        return 'Done'

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

    def get_groups(self) -> List:
        # todo Add support for discuss group iteration
        self.update_group_list()  # Force update group list
        res = self.group_list
        # res = self.coolq_bot.get_group_list()
        groups = []
        for i in range(len(res)):
            context = {'message_type': 'group',
                       'group_id': res[i]['group_id']}
            efb_chat = self.chat_manager.build_efb_chat_as_group(context)
            groups.append(efb_chat)
        for i in range(len(self.extra_group_list)):
            does_exist = False
            for j in range(len(res)):
                if str(self.extra_group_list[i]['group_id']) == str(res[i]['group_id']):
                    does_exist = True
                    break
            if does_exist:
                continue
            context = {'message_type': 'group',
                       'group_id': self.extra_group_list[i]['group_id']}
            efb_chat = self.chat_manager.build_efb_chat_as_group(context)
            groups.append(efb_chat)
        return groups + self.discuss_list

    def get_friends(self) -> List:
        # Warning: Experimental API
        try:
            self.update_friend_list()  # Force update friend list
        except CoolQAPIFailureException:
            self.deliver_alert_to_master(self._('Failed to retrieve the friend list.\n'
                                                'Only groups are shown.'))
            return []
        res = self.friend_list
        users = []
        for i in range(len(res)):  # friend group
            for j in range(len(res[i]['friend'])):
                current_user = res[i]['friend'][j]
                txt = '[{}] {}'
                txt = txt.format(res[i]['name'], current_user['name'])
                # nickname = self.get_stranger_info(current_user['uin'])['nickname']

                # Disable nickname & remark comparsion for it's too time-consuming
                context = {'user_id': str(current_user['uin']),
                           'nickname': txt,
                           'alias': None}
                efb_chat = self.chat_manager.build_efb_chat_as_user(context, True)
                users.append(efb_chat)
        '''
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
        '''
        return users

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

        self.logger.debug('[%s] Is edited: %s', msg.uid, msg.edit)
        if msg.edit:
            if self.client_config['is_pro']:
                try:
                    uid_type = msg.uid.split('_')
                    self.recall_message(uid_type[1])
                except CoolQAPIFailureException:
                    raise EFBOperationNotSupported(self._("Failed to recall the message!\n"
                                                          "This message may have already expired."))

        if msg.type in [MsgType.Text, MsgType.Link]:
            if isinstance(msg.target, EFBMsg):
                if msg.text == "kick`":
                    group_id = chat_type[1]
                    user_id = msg.target.author.chat_uid.split('_')[1]
                    self.coolq_api_query("set_group_kick",
                                         group_id=group_id,
                                         user_id=user_id)
                else:
                    max_length = 50
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
        elif msg.type in (MsgType.Image, MsgType.Sticker, MsgType.Animation):
            self.logger.info("[%s] Image/Sticker/Animation %s", msg.uid, msg.type)
            text = ''
            if not self.client_config['is_pro']:  # CoolQ Air
                if self.client_config['air_option']['upload_to_smms']:
                    text = '[Image] {}'
                    smms_data = None
                    try:
                        smms_data = upload_image_smms(msg.file, msg.path)
                    except CoolQUnknownException as e:
                        text = '[Image]'
                        self.deliver_alert_to_master(self._('Failed to upload the image to sm.ms! Return Msg: ')
                                                     + getattr(e, 'message', repr(e)))
                    else:
                        if smms_data is not None:
                            text = text.format(smms_data['url'])
                elif 'upload_to_vim_cn' in self.client_config['air_option'] \
                        and self.client_config['air_option']['upload_to_vim_cn']:
                    text = '[Image] {}'
                    vim_cn_data = None
                    try:
                        vim_cn_data = upload_image_vim_cn(msg.file, msg.path)
                    except CoolQUnknownException as e:
                        text = '[Image]'
                        self.deliver_alert_to_master(self._('Failed to upload the image to vim-cn.com! Return Msg: ')
                                                     + getattr(e, 'message', repr(e)))
                    else:
                        if vim_cn_data is not None:
                            text = text.format(vim_cn_data)
                elif 'upload_to_mi' in self.client_config['air_option'] \
                        and self.client_config['air_option']['upload_to_mi']:
                    text = '[Image] {}'
                    mi_data = None
                    try:
                        mi_data = upload_image_mi(msg.file, msg.path)
                    except CoolQUnknownException as e:
                        text = '[Image]'
                        self.deliver_alert_to_master(self._('Failed to upload the image to mi.com! Return Msg: ')
                                                     + getattr(e, 'message', repr(e)))
                    else:
                        if mi_data is not None:
                            text = text.format(mi_data)
                elif 'upload_to_sogou' in self.client_config['air_option'] \
                        and self.client_config['air_option']['upload_to_sogou']:
                    text = '[Image] {}'
                    sogou_data = None
                    try:
                        sogou_data = upload_image_sogou(msg.file, msg.path)
                    except CoolQUnknownException as e:
                        text = '[Image]'
                        self.deliver_alert_to_master(self._('Failed to upload the image to sogou.com! Return Msg: ')
                                                     + getattr(e, 'message', repr(e)))
                    else:
                        if sogou_data is not None:
                            text = text.format(sogou_data)
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

    def get_group_info(self, group_id, no_cache=True):
        if no_cache or not self.group_list:
            self.group_list = self.coolq_api_query('get_group_list')
        res = self.group_list
        # res = self.coolq_bot.get_group_list()
        for i in range(len(res)):
            if res[i]['group_id'] == group_id:
                return res[i]
        try:
            external_group = self.get_external_group_info(group_id)
        except Exception:
            return None
        else:
            new_group = {'group_id': group_id, 'group_name': external_group['group_name']}
            for i in range(len(self.extra_group_list)):
                if str(self.extra_group_list[i]['group_id']) == str(group_id):
                    return new_group
            self.extra_group_list.append(new_group)
            return new_group

    def coolq_send_message(self, msg_type, uid, message):
        keyword = msg_type if msg_type != 'private' else 'user'
        res = self.coolq_api_query('send_msg', message_type=msg_type, **{keyword + '_id': uid}, message=message)
        # res = self.coolq_bot.send_msg(message_type=msg_type, **{keyword + '_id': uid}, message=message)
        return str(uuid.uuid4()) + '_' + str(res['message_id'])

    def _coolq_api_wrapper(self, func_name, **kwargs):
        try:
            func = getattr(self.coolq_bot, func_name)
            res = func(**kwargs)
        except RequestException as e:
            raise CoolQDisconnectedException(self._('Unable to connect to CoolQ Client!'
                                                    'Error Message:\n{}').format(str(e)))
        except cqhttp.Error as ex:
            api_ex = CoolQAPIFailureException(self._('CoolQ HTTP API encountered an error!\n'
                                                     'Status Code:{} '
                                                     'Return Code:{}').format(ex.status_code, ex.retcode))
            # if ex.status_code == 200 and ex.retcode == 104:  # Cookie expired
            setattr(api_ex, 'status_code', ex.status_code)
            setattr(api_ex, 'retcode', ex.retcode)
            raise api_ex
        else:
            return res

    def check_running_status(self):
        res = self._coolq_api_wrapper('get_status')
        if res['good'] or res['online']:
            return True
        else:
            raise CoolQOfflineException(self._("CoolQ Client isn't working correctly!"))

    def coolq_api_query(self, func_name, **kwargs):
        """ # Do not call get_status too frequently
        if self.check_running_status():
            return self._coolq_api_wrapper(func_name, **kwargs)
        """
        if self.is_logged_in and self.is_connected:
            return self._coolq_api_wrapper(func_name, **kwargs)
        elif self.repeat_counter < 3:
            self.deliver_alert_to_master(self._('Your status is offline.\n'
                                                'You may try login with /0_login'))
            self.repeat_counter += 1

    def check_status_periodically(self, t_event):
        self.logger.debug('Start checking status...')
        flag = True
        interval = 300
        try:
            flag = self.check_running_status()
        except CoolQDisconnectedException as e:
            if self.repeat_counter < 3:
                self.deliver_alert_to_master(self._("We're unable to communicate with CoolQ Client.\n"
                                                    "Please check the connection and credentials provided.\n"
                                                    "{}").format(str(e)))
                self.repeat_counter += 1
            self.is_connected = False
            self.is_logged_in = False
            interval = 3600
        except (CoolQOfflineException, CoolQAPIFailureException):
            if self.repeat_counter < 3:
                self.deliver_alert_to_master(self._('CoolQ is running in abnormal status.\n'
                                                    'You may need to relogin your account '
                                                    'or have a check in CoolQ Client.\n'))
                self.repeat_counter += 1
            self.is_connected = True
            self.is_logged_in = False
            interval = 3600
        else:
            if not flag:
                if self.repeat_counter < 3:
                    self.deliver_alert_to_master(self._("We don't know why, but status check failed.\n"
                                                        "Please enable debug mode and consult the log "
                                                        "for more details."))
                    self.repeat_counter += 1
                self.is_connected = True
                self.is_logged_in = False
                interval = 3600
            else:
                self.logger.debug('Status: OK')
                self.is_connected = True
                self.is_logged_in = True
                self.repeat_counter = 0

        if t_event is not None and not t_event.is_set():
            threading.Timer(interval, self.check_status_periodically, [t_event]).start()

    def deliver_alert_to_master(self, message: str):
        context = {'message': message, 'uid_prefix': 'alert', 'event_description': self._('CoolQ Alert')}
        self.send_msg_to_master(context)

    def update_friend_list(self):
        # Warning: Experimental API
        # self.friend_list = self.coolq_api_query('_get_friend_list')
        try:
            cred = self.coolq_api_query('get_credentials')
            cookies = cred['cookies']
            csrf_token = cred['csrf_token']
            self.friend_list = get_friend_list_via_qq_show(cookies, csrf_token)
        except Exception:
            self.logger.warning('Failed to update friend list')
        if self.friend_list:
            self.logger.debug('Update friend list completed. Entries: %s', len(self.friend_list))
        else:
            self.logger.warning('Failed to update friend list')

    def update_group_list(self):
        self.group_list = self.coolq_api_query('get_group_list')
        if self.group_list:
            self.logger.debug('Update group list completed. Entries: %s', len(self.group_list))
        else:
            self.logger.warning('Failed to update group list')

    def update_contacts_periodically(self, t_event):
        self.logger.debug('Start updating friend & group list')
        interval = 1800
        if self.is_connected and self.is_logged_in:
            try:
                self.update_friend_list()
                self.update_group_list()
            except CoolQAPIFailureException as ex:
                if getattr(ex, 'status_code') == 200 and getattr(ex, 'retcode') == 104 \
                        and self.update_repeat_counter < 3:
                    self.send_cookie_expired_alarm()
                if self.update_repeat_counter < 3:
                    self.deliver_alert_to_master(self._('Errors occurred when updating contacts: ')
                                                 + getattr(ex, 'message'))
                    self.update_repeat_counter += 1
            else:
                self.update_repeat_counter = 0
        self.logger.debug('Update completed')
        if t_event is not None and not t_event.is_set():
            threading.Timer(interval, self.update_contacts_periodically, [t_event]).start()

    def get_friend_remark(self, uid):
        if not self.friend_list:
            try:
                self.update_friend_list()
            except CoolQAPIFailureException:
                self.deliver_alert_to_master(self._('Failed to obtain friend remark name'))
                return ''
        for i in range(len(self.friend_list)):  # friend group
            for j in range(len(self.friend_list[i]['friend'])):
                current_user = self.friend_list[i]['friend'][j]
                if current_user['uin'] != str(uid):
                    continue
                return current_user['name']
        return None  # I don't think you've got such a friend
        '''
        for i in range(len(self.friend_list)):  # friend group
            for j in range(len(self.friend_list[i]['friends'])):
                current_user = self.friend_list[i]['friends'][j]
                if current_user['user_id'] != uid:
                    continue
                if current_user['nickname'] == current_user['remark'] or current_user['nickname'] == '':
                    # no remark name
                    return current_user['nickname']
                else:
                    return current_user['remark']
        return None  # I don't think you've got such a friend
        '''

    def send_efb_group_notice(self, context):
        context['message_type'] = 'group'
        self.logger.debug(repr(context))
        msg = EFBMsg()
        msg.author = self.chat_manager.build_efb_chat_as_system_user(context)
        msg.chat = self.chat_manager.build_efb_chat_as_group(context)
        msg.deliver_to = coordinator.master
        msg.type = MsgType.Text
        msg.uid = "__group_notice__.%s" % int(time.time())
        msg.text = context['message']
        coordinator.send_message(msg)

    def send_msg_to_master(self, context):
        self.logger.debug(repr(context))
        msg = EFBMsg()
        msg.chat = msg.author = self.chat_manager.build_efb_chat_as_system_user(context)
        msg.deliver_to = coordinator.master
        msg.type = MsgType.Text
        msg.uid = "__{context[uid_prefix]}__.{uni_id}".format(context=context,
                                                              uni_id=str(int(time.time())))
        if 'message' in context:
            msg.text = context['message']
        if 'commands' in context:
            msg.commands = EFBMsgCommands(context['commands'])
        coordinator.send_message(msg)

    # As the old saying goes
    # A programmer spent 20% of time on coding
    # while the rest 80% on considering a variable/function/class name
    # todo Deprecated
    def get_external_group_info(self, group_id):  # Special thanks to @lwl12 for thinking of this name
        res = self.coolq_api_query('_get_group_info',
                                   group_id=group_id)
        return res

    def send_status(self, status: 'EFBStatus'):
        if isinstance(status, EFBMessageRemoval):
            if not status.message.author.is_self:
                raise EFBMessageError(self._('You can only recall your own messages.'))
            try:
                uid_type = status.message.uid.split('_')
                self.recall_message(uid_type[1])
            except CoolQAPIFailureException:
                raise EFBMessageError(
                    self._('Failed to recall the message. This message may have already expired.'))
        else:
            raise EFBOperationNotSupported()
        # todo

    def recall_message(self, message_id):
        self.coolq_api_query('delete_msg',
                             message_id=message_id)

    def send_cookie_expired_alarm(self):
        self.deliver_alert_to_master(self._('Your cookie of CoolQ Client seems to be expired. '
                                            'Although it will not affect the normal functioning of sending/receiving '
                                            'messages, however, you may encounter issues like failing to retrieve '
                                            'friend list. Please consult '
                                            'https://github.com/milkice233/efb-qq-slave/wiki/Workaround-for-expired'
                                            '-cookies-of-CoolQ for solutions.'))

    def process_friend_request(self, result, flag):
        res = 'true' if result == 'accept' else 'false'
        try:
            self.coolq_api_query('set_friend_add_request',
                                 approve=res,
                                 flag=flag)
        except CoolQAPIFailureException as e:
            return (self._('Failed to process request! Error Message:\n')
                    + getattr(e, 'message', repr(e)))
        return 'Done'

    def process_group_request(self, result, flag, sub_type):
        res = 'true' if result == 'accept' else 'false'
        try:
            self.coolq_api_query('set_group_add_request',
                                 approve=res,
                                 flag=flag,
                                 sub_type=sub_type)
        except CoolQAPIFailureException as e:
            return (self._('Failed to process request! Error Message:\n')
                    + getattr(e, 'message', repr(e)))
        return 'Done'

    def async_download_file(self, context, **kwargs):
        res = download_file_from_qzone(**kwargs)
        if isinstance(res, str):
            context['message'] = self._("[Download] ") + res
            self.send_efb_group_notice(context)
        elif res is None:
            pass
        else:
            data = {'file': res, 'filename': context['file']['name']}
            context['message_type'] = 'group'
            efb_msg = self.msg_decorator.qq_file_after_wrapper(data)
            efb_msg.uid = str(context['user_id']) + '_' + str(uuid.uuid4()) + '_' + str(1)
            efb_msg.text = 'Sent a file'
            efb_msg.author = self.chat_manager.build_efb_chat_as_user(context, False)
            efb_msg.chat = self.chat_manager.build_efb_chat_as_group(context)
            efb_msg.deliver_to = coordinator.master
            async_send_messages_to_master(efb_msg)

    def get_chat_picture(self, chat: EFBChat) -> IO[bytes]:
        chat_type = chat.chat_uid.split('_')
        if chat_type[0] == 'private':
            return download_user_avatar(chat_type[1])
        elif chat_type[0] == 'group':
            return download_group_avatar(chat_type[1])
        else:
            return download_group_avatar("")

    def get_chats(self):
        qq_chats = self.get_friends()
        group_chats = self.get_groups()
        return qq_chats + group_chats

    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None) -> EFBChat:
        # todo what is member_uid used for?
        chat_type = chat_uid.split('_')
        if chat_type[0] == 'private':
            qq_uid = int(chat_type[1])
            remark = self.get_friend_remark(qq_uid)
            context = {"user_id": qq_uid}
            if remark is not None:
                context['alias'] = remark
            return self.chat_manager.build_efb_chat_as_user(context, True)
        elif chat_type[0] == 'group':
            group_id = int(chat_type[1])
            context = {'message_type': 'group', 'group_id': group_id}
            return self.chat_manager.build_efb_chat_as_group(context)
        elif chat_type[0] == 'discuss':
            discuss_id = int(chat_type[1])
            context = {'message_type': 'discuss', 'discuss_id': discuss_id}
            return self.chat_manager.build_efb_chat_as_group(context)
        raise EFBChatNotFound()

    def check_self_update(self, t_event):
        interval = 60 * 60 * 24
        latest_version = self.channel.check_updates()
        if latest_version is not None:
            self.deliver_alert_to_master("New version({version}) of EFB-QQ-Slave has released! "
                                         "Please manually update EQS by stopping ehForwarderbot first and then execute "
                                         "<code>pip3 install --upgrade efb-qq-slave</code>"
                                         .format(version=latest_version))
        else:
            if t_event is not None and not t_event.is_set():
                threading.Timer(interval, self.check_self_update, [t_event]).start()
