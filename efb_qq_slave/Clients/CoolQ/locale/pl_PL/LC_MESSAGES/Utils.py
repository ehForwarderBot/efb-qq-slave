# coding: utf-8
import json
import logging
import os
import shutil
import tempfile
import urllib.request
from gettext import translation
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.parse import quote

import requests
from ehforwarderbot import EFBMsg, coordinator
from pkg_resources import resource_filename

from .Exceptions import CoolQUnknownException

qq_emoji_list = {  # created by JogleLew, optimizations are welcome
    0: u'\U0001F62E',
    1: u'\U0001F623',
    2: u'\U0001F60D',
    3: u'\U0001F633',
    4: u'\U0001F60E',
    5: u'\U0001F62D',
    6: u'\U0000263A',
    7: u'\U0001F637',
    8: u'\U0001F634',
    9: u'\U0001F62D',
    10: u'\U0001F630',
    11: u'\U0001F621',
    12: u'\U0001F61D',
    13: u'\U0001F603',
    14: u'\U0001F642',
    15: u'\U0001F641',
    16: u'\U0001F913',
    18: u'\U0001F624',
    19: u'\U0001F628',
    20: u'\U0001F60F',
    21: u'\U0001F60A',
    22: u'\U0001F644',
    23: u'\U0001F615',
    24: u'\U0001F924',
    25: u'\U0001F62A',
    26: u'\U0001F628',
    27: u'\U0001F613',
    28: u'\U0001F62C',
    29: u'\U0001F911',
    30: u'\U0001F44A',
    31: u'\U0001F624',
    32: u'\U0001F914',
    33: u'\U0001F910',
    34: u'\U0001F635',
    35: u'\U0001F629',
    36: u'\U0001F47F',
    37: u'\U0001F480',
    38: u'\U0001F915',
    39: u'\U0001F44B',
    50: u'\U0001F641',
    51: u'\U0001F913',
    53: u'\U0001F624',
    54: u'\U0001F92E',
    55: u'\U0001F628',
    56: u'\U0001F613',
    57: u'\U0001F62C',
    58: u'\U0001F911',
    73: u'\U0001F60F',
    74: u'\U0001F60A',
    75: u'\U0001F644',
    76: u'\U0001F615',
    77: u'\U0001F924',
    78: u'\U0001F62A',
    79: u'\U0001F44A',
    80: u'\U0001F624',
    81: u'\U0001F914',
    82: u'\U0001F910',
    83: u'\U0001F635',
    84: u'\U0001F629',
    85: u'\U0001F47F',
    86: u'\U0001F480',
    87: u'\U0001F915',
    88: u'\U0001F44B',
    96: u'\U0001F630',
    97: u'\U0001F605',
    98: u'\U0001F925',
    99: u'\U0001F44F',
    100: u'\U0001F922',
    101: u'\U0001F62C',
    102: u'\U0001F610',
    103: u'\U0001F610',
    104: u'\U0001F629',
    105: u'\U0001F620',
    106: u'\U0001F61E',
    107: u'\U0001F61F',
    108: u'\U0001F60F',
    109: u'\U0001F619',
    110: u'\U0001F627',
    111: u'\U0001F920',
    172: u'\U0001F61C',
    173: u'\U0001F62D',
    174: u'\U0001F636',
    175: u'\U0001F609',
    176: u'\U0001F913',
    177: u'\U0001F635',
    178: u'\U0001F61C',
    179: u'\U0001F4A9',
    180: u'\U0001F633',
    181: u'\U0001F913',
    182: u'\U0001F602',
    183: u'\U0001F913',
    212: u'\U0001F633',
}

qq_sface_list = {
    1: '[拜拜]',
    2: '[鄙视]',
    3: '[菜刀]',
    4: '[沧桑]',
    5: '[馋了]',
    6: '[吃惊]',
    7: '[微笑]',
    8: '[得意]',
    9: '[嘚瑟]',
    10: '[瞪眼]',
    11: '[震惊]',
    12: '[鼓掌]',
    13: '[害羞]',
    14: '[好的]',
    15: '[惊呆了]',
    16: '[静静看]',
    17: '[可爱]',
    18: '[困]',
    19: '[脸红]',
    20: '[你懂的]',
    21: '[期待]',
    22: '[亲亲]',
    23: '[伤心]',
    24: '[生气]',
    25: '[摇摆]',
    26: '[帅]',
    27: '[思考]',
    28: '[震惊哭]',
    29: '[痛心]',
    30: '[偷笑]',
    31: '[挖鼻孔]',
    32: '[抓狂]',
    33: '[笑着哭]',
    34: '[无语]',
    35: '[捂脸]',
    36: '[喜欢]',
    37: '[笑哭]',
    38: '[疑惑]',
    39: '[赞]',
    40: '[眨眼]'
}

translator = translation("efb_qq_slave",
                         resource_filename('efb_qq_slave', 'Clients/CoolQ/locale'),
                         fallback=True)
_ = translator.gettext
ngettext = translator.ngettext


def cq_get_image(image_link: str) -> tempfile:  # Download image from QQ
    file = tempfile.NamedTemporaryFile()
    try:
        urllib.request.urlretrieve(image_link, file.name)
    except (URLError, HTTPError, ContentTooShortError) as e:
        logging.getLogger(__name__).warning('Image download failed.')
        logging.getLogger(__name__).warning(str(e))
        return None
    else:
        if file.seek(0, 2) <= 0:
            raise EOFError('File downloaded is Empty')
        file.seek(0)
        return file


def async_send_messages_to_master(msg: EFBMsg):
    coordinator.send_message(msg)
    if msg.file:
        msg.file.close()


def process_quote_text(text, max_length):  # Simple wrapper for processing quoted text
    qt_txt = "%s" % text
    if max_length > 0:
        tgt_text = qt_txt[:max_length]
        if len(qt_txt) >= max_length:
            tgt_text += "…"
        tgt_text = "「%s」" % tgt_text
    elif max_length < 0:
        tgt_text = "「%s」" % qt_txt
    else:
        tgt_text = ""
    return tgt_text


def coolq_text_encode(text: str):  # Escape special characters for CQ Code text
    expr = (('&', '&amp;'), ('[', '&#91;'), (']', '&#93;'))
    for r in expr:
        text = text.replace(*r)
    return text


def coolq_para_encode(text: str):  # Escape special characters for CQ Code parameters
    expr = (('&', '&amp;'), ('[', '&#91;'), (']', '&#93;'), (',', '&#44;'))
    for r in expr:
        text = text.replace(*r)
    return text


def upload_image_smms(file, path):  # Upload image to sm.ms and return the link
    UPLOAD_URL = 'https://sm.ms/api/upload'
    UPLOAD_PARAMS = {'format': 'json', 'ssl': True}
    with open(path, 'rb') as f:
        files = {'smfile': f.read()}
        resp = requests.post(UPLOAD_URL, files=files, params=UPLOAD_PARAMS)
        status = json.loads(resp.text)
        if status['code'] == 'success':
            logging.getLogger(__name__).debug('INFO: upload success! url at {}'.format(status['data']['url']))
            return status['data']
        else:
            logging.getLogger(__name__).warning('WARNING: {}'.format(status['msg']))
            raise CoolQUnknownException(status['msg'])


def param_spliter(str_param):
    params = str_param.split(";")
    param = {}
    for _k in params:
        key, value = _k.strip().split("=")
        param[key] = value
    return param


def download_file_from_qzone(cookie: str, csrf_token: str, uin, group_id, file_id, filename, file_size):
    cookie_arr = param_spliter(cookie)
    url = "http://qun.qzone.qq.com/cgi-bin/group_share_get_downurl?uin=" + str(uin) + "&pa=/104/" + \
          str(file_id) + "&groupid=" + str(group_id) + "&bussinessid=0&charset=utf-8&g_tk=" + str(csrf_token) + "&r=888"
    ret = requests.get(url, cookies=cookie_arr)
    data = json.loads(ret.text.split("(")[1].split(")")[0])['data']
    cookie += "; FTN5K=" + str(data['cookie'])
    download_url = data['url']
    download_url += "/" + quote(filename)
    if file_size >= 50*1024*1024:  # File size is bigger than 50MiB
        return _("File is too big to be downloaded")
    file = tempfile.NamedTemporaryFile()
    try:
        opener = urllib.request.build_opener()
        opener.addheaders.append(('Cookie', cookie))
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(download_url, file.name)
    except (URLError, HTTPError, ContentTooShortError) as e:
        logging.getLogger(__name__).warning("Error occurs when downloading files: " + str(e))
        return _("Error occurs when downloading files: ") + str(e)
    else:
        if file.seek(0, 2) <= 0:
            raise EOFError('File downloaded is Empty')
        file.seek(0)
        return file
    '''
    try:
        opener = urllib.request.build_opener()
        opener.addheaders.append(('Cookie', cookie))
        with opener.open(download_url) as response, tempfile.NamedTemporaryFile() as f:
            shutil.copyfileobj(response, f)
            if f.seek(0, 2) <= 0:
                raise EOFError('File downloaded is Empty')
            f.seek(0)
            return f
    except Exception as e:
        logging.getLogger(__name__).warning("Error occurs when downloading files" + str(e))
        return url
    '''