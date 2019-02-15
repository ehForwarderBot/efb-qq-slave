# coding: utf-8

import logging
import threading
import uuid
import base64

import magic
from typing import Callable
from urllib.parse import quote
from ehforwarderbot import EFBMsg, MsgType, EFBChat, coordinator
from ehforwarderbot.message import EFBMsgLocationAttribute, EFBMsgCommands, EFBMsgCommand, EFBMsgSubstitutions, \
    EFBMsgLinkAttribute

from .Utils import cq_get_image, coolq_para_encode
from . import CoolQ


class MsgDecorator:  # Deprecated
    @classmethod
    def qq_msg_meta(cls, func: Callable):
        def wrap_func(self, data, *args, **kwargs):
            logger = logging.getLogger(__name__)
            logger.debug("Raw message: %s", repr(data))

            efb_msg: EFBMsg = func(data, *args, **kwargs)

            if efb_msg is None:
                return
            # todo

            efb_msg.uid = str(uuid.uuid4())

            logger.debug("[%s] Chat: %s, Author: %s", efb_msg.uid, efb_msg.chat, efb_msg.author)

            efb_msg.deliver_to = coordinator.master

        def thread_wrapper(*args, **kwargs):
            """Run message requests in separate threads to prevent blocking"""
            threading.Thread(target=wrap_func, args=args, kwargs=kwargs).run()

        return thread_wrapper


class QQMsgProcessor:
    inst: CoolQ

    def __init__(self, instance: CoolQ):
        self.inst = instance
        self._ = instance._
        pass

    def qq_image_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        if 'url' not in data:
            efb_msg.type = MsgType.Text
            efb_msg.text = self._('[Image Source missing]')
            return efb_msg

        efb_msg.file = cq_get_image(data['url'])
        if efb_msg.file is None:
            efb_msg.type = MsgType.Text
            efb_msg.text = self._('[Download image failed, please check on your QQ client]')
            return efb_msg

        efb_msg.type = MsgType.Image
        mime = magic.from_file(efb_msg.file.name, mime=True)
        if isinstance(mime, bytes):
            mime = mime.decode()
        efb_msg.path = efb_msg.file.name
        efb_msg.mime = mime
        return efb_msg

    def qq_record_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Unsupported
        efb_msg.text = self._('[Voice Message] Please check it on your QQ')
        return efb_msg

    def qq_share_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Link
        efb_msg.text = ''
        efb_msg.attributes = EFBMsgLinkAttribute(
            title='' if 'title' not in data else data['title'],
            description='' if 'content' not in data else data['content'],
            image='' if 'image' not in data else data['image'],
            url=data['url']
        )
        return efb_msg

    def qq_location_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.text = data['content']
        efb_msg.attributes = EFBMsgLocationAttribute(longitude=float(data['lon']),
                                                     latitude=float(data['lat']))
        efb_msg.type = MsgType.Location
        return efb_msg

    def qq_shake_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Text
        efb_msg.text += self._('[Your friend shakes you!]')
        return efb_msg

    def qq_contact_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Text
        uid = data['id']
        contact_type = data['type']
        txt = self._("Chat Recommendation Received\nID: {}\nType: {}")

        txt = txt.format(uid, contact_type)
        efb_msg.text = txt
        efb_msg.type = MsgType.Text
        return efb_msg

    def qq_bface_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Unsupported
        efb_msg.text += self._('[Here comes the BigFace Emoji, please check it on your phone]')
        return efb_msg

    def qq_small_face_wrapper(self, data, merged_msg_id) -> EFBMsg:
        # todo this function's maybe not necessary?
        pass

    def qq_sign_wrapper(self, data) -> EFBMsg:
        location = self._('at {}').format(data['location']) if 'location' in data else self._('at Unknown Place')
        title = '' if 'title' not in data else (self._('with title {}').format(data['title']))
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Text
        efb_msg.text = self._('signed in {location} {title}').format(title=title,
                                                                     location=location)
        return efb_msg

    def qq_rich_wrapper(self, data: dict) -> EFBMsg:  # Buggy, Help needed
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Unsupported
        efb_msg.text = self._('[Here comes the Rich Text, dumping...] \n')
        for key, value in data.items():
            efb_msg.text += key + ':' + value + '\n'
        return efb_msg

    def qq_music_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        if data['type'] == '163':  # Netease Cloud Music
            efb_msg.type = MsgType.Text
            efb_msg.text = 'https://music.163.com/#/song?id=' + data['id']
        else:
            efb_msg.type = MsgType.Text
            efb_msg.text = data['text']
        return efb_msg  # todo Port for other music platform
        pass

    def qq_text_simple_wrapper(self, text: str, ats: dict):  # This cute function only accepts string!
        efb_msg = EFBMsg()
        efb_msg.type = MsgType.Text
        efb_msg.text = text
        if ats:  # This is used to replace specific text with @blahblah
            # And Milkice really requires a brain check
            efb_msg.substitutions = EFBMsgSubstitutions(ats)
        return efb_msg

    def coolq_code_at_wrapper(self, uid):
        return '[CQ:at,qq={}]'.format(uid)

    def coolq_code_image_wrapper(self, file, file_path):
        if file.closed:
            file = open(file.name)
        encoded_string = base64.b64encode(file.read())
        # Since base64 doesn't contain characters which isn't allowed in CQ Code,
        # there's no need to escape the special characters
        return '[CQ:image,file=base64://{}]'.format(encoded_string.decode())

    def qq_file_after_wrapper(self, data) -> EFBMsg:
        efb_msg = EFBMsg()
        efb_msg.file = data['file']
        efb_msg.type = MsgType.File
        mime = magic.from_file(efb_msg.file.name, mime=True)
        if isinstance(mime, bytes):
            mime = mime.decode()
        efb_msg.path = efb_msg.file.name
        efb_msg.mime = mime
        efb_msg.filename = quote(data['filename'])
        return efb_msg
