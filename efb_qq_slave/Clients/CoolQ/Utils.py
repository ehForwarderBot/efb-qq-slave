# coding: utf-8
import json
import logging
import os
import shutil
import ntpath
import tempfile
import urllib.request
from gettext import translation
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.parse import quote

import magic
import requests
from ehforwarderbot import EFBMsg, coordinator
from pkg_resources import resource_filename

from .Exceptions import CoolQUnknownException

qq_emoji_list = {  # created by JogleLew, optimizations are welcome
    0: '\U0001F62E',
    1: '\U0001F623',
    2: '\U0001F60D',
    3: '\U0001F633',
    4: '\U0001F60E',
    5: '\U0001F62D',
    6: '\U0000263A',
    7: '\U0001F637',
    8: '\U0001F634',
    9: '\U0001F62D',
    10: '\U0001F630',
    11: '\U0001F621',
    12: '\U0001F61D',
    13: '\U0001F603',
    14: '\U0001F642',
    15: '\U0001F641',
    16: '\U0001F913',
    18: '\U0001F624',
    19: '\U0001F628',
    20: '\U0001F60F',
    21: '\U0001F60A',
    22: '\U0001F644',
    23: '\U0001F615',
    24: '\U0001F924',
    25: '\U0001F62A',
    26: '\U0001F628',
    27: '\U0001F613',
    28: '\U0001F62C',
    29: '\U0001F911',
    30: '\U0001F44A',
    31: '\U0001F624',
    32: '\U0001F914',
    33: '\U0001F910',
    34: '\U0001F635',
    35: '\U0001F629',
    36: '\U0001F47F',
    37: '\U0001F480',
    38: '\U0001F915',
    39: '\U0001F44B',
    50: '\U0001F641',
    51: '\U0001F913',
    53: '\U0001F624',
    54: '\U0001F92E',
    55: '\U0001F628',
    56: '\U0001F613',
    57: '\U0001F62C',
    58: '\U0001F911',
    73: '\U0001F60F',
    74: '\U0001F60A',
    75: '\U0001F644',
    76: '\U0001F615',
    77: '\U0001F924',
    78: '\U0001F62A',
    79: '\U0001F44A',
    80: '\U0001F624',
    81: '\U0001F914',
    82: '\U0001F910',
    83: '\U0001F635',
    84: '\U0001F629',
    85: '\U0001F47F',
    86: '\U0001F480',
    87: '\U0001F915',
    88: '\U0001F44B',
    96: '\U0001F630',
    97: '\U0001F605',
    98: '\U0001F925',
    99: '\U0001F44F',
    100: '\U0001F922',
    101: '\U0001F62C',
    102: '\U0001F610',
    103: '\U0001F610',
    104: '\U0001F629',
    105: '\U0001F620',
    106: '\U0001F61E',
    107: '\U0001F61F',
    108: '\U0001F60F',
    109: '\U0001F619',
    110: '\U0001F627',
    111: '\U0001F920',
    172: '\U0001F61C',
    173: '\U0001F62D',
    174: '\U0001F636',
    175: '\U0001F609',
    176: '\U0001F913',
    177: '\U0001F635',
    178: '\U0001F61C',
    179: '\U0001F4A9',
    180: '\U0001F633',
    181: '\U0001F913',
    182: '\U0001F602',
    183: '\U0001F913',
    212: '\U0001F633',
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


def upload_image_vim_cn(file, path):  # Upload image to img.vim-cn.com and return the link
    UPLOAD_URL = 'https://img.vim-cn.com/'
    with open(path, 'rb') as f:
        files = {'name': f.read()}
        resp = requests.post(UPLOAD_URL, files=files)
        if resp.status_code != 200:
            raise CoolQUnknownException("Failed to upload images to vim-cn.com")
        return resp.text


def upload_image_sogou(file, path):  # Upload image to pic.sogou.com and return the link
    UPLOAD_URL = 'https://pic.sogou.com/pic/upload_pic.jsp'
    with open(path, 'rb') as f:
        files = {'pic_path': f.read()}
        resp = requests.post(UPLOAD_URL, files=files)
        if resp.status_code != 200:
            raise CoolQUnknownException("Failed to upload images to sogou.com")
        return "https" + resp.text[4:]  # Replace http with https


def upload_image_mi(file, path):  # Upload image to shopapi.io.mi.com and return the link
    UPLOAD_URL = 'https://shopapi.io.mi.com/homemanage/shop/uploadpic'
    with open(path, 'rb') as f:
        files = {'pic': (ntpath.basename(path), f.read(), "image/jpeg")}
        resp = requests.post(UPLOAD_URL, files=files)
        if resp.status_code != 200:
            raise CoolQUnknownException("Failed to upload images to mi.com")
        status = json.loads(resp.text)
        print(status)
        if status['message'] != "ok":
            raise CoolQUnknownException("Failed to upload images to mi.com")
        return status['result']


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


def download_user_avatar(uid: str):
    file = tempfile.NamedTemporaryFile()
    url = "https://q1.qlogo.cn/g?b=qq&nk={}&s=0".format(uid)
    try:
        opener = urllib.request.build_opener()
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, file.name)
    except (URLError, HTTPError, ContentTooShortError) as e:
        logging.getLogger(__name__).warning("Error occurs when downloading files: " + str(e))
        return _("Error occurs when downloading files: ") + str(e)
    if file.seek(0, 2) <= 0:
        raise EOFError('File downloaded is Empty')
    file.seek(0)
    return file


def download_group_avatar(uid: str):
    file = tempfile.NamedTemporaryFile()
    url = "https://p.qlogo.cn/gh/{}/{}/".format(uid, uid)
    try:
        opener = urllib.request.build_opener()
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, file.name)
    except (URLError, HTTPError, ContentTooShortError) as e:
        logging.getLogger(__name__).warning("Error occurs when downloading files: " + str(e))
        return _("Error occurs when downloading files: ") + str(e)
    if file.seek(0, 2) <= 0:
        raise EOFError('File downloaded is Empty')
    file.seek(0)
    return file


def get_friend_list_via_qq_show(cookie: str, csrf_token: str):
    # This function won't check before execute, instead all the exceptions will be thrown
    cookie_arr = param_spliter(cookie)
    url = "http://show.qq.com/cgi-bin/qqshow_user_friendgroup?g_tk={csrf_token}&omode=4" \
        .format(csrf_token=csrf_token)
    ret = requests.get(url, cookies=cookie_arr)
    data = json.loads(ret.text)
    return data['data']['group']


def download_voice(filename: str, api_root: str, access_token: str):
    file = tempfile.NamedTemporaryFile()
    url = '{url}/data/record/{file}'.format(url=api_root, file=filename)
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [("Authorization", "Bearer {at}".format(at=access_token))]

        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, file.name)
    except (URLError, HTTPError, ContentTooShortError) as e:
        logging.getLogger(__name__).warning("Error occurs when downloading files: " + str(e))
        return _("Error occurs when downloading files: ") + str(e)
    if file.seek(0, 2) <= 0:
        raise EOFError('File downloaded is Empty')
    file.seek(0)
    return file
