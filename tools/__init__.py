# -*- coding: utf-8 -*-
# @Time    : 2019/8/13 20:17
# @Author  : xzkzdx
# @File    : __init__.py.py
import hashlib
import json

import redis

from settings import WX_REDIS_CONFIG
from tools.proxy import open_system_proxy, system_proxy_status, close_system_proxy
from tools.handle import HandleModel, CheckHandle, WeChatWnd, Fiddler, WeChatWebViewWnd


def get_pass_key_and_uin(article_url: str, biz):
    from time import sleep, time
    from settings import FIDDLER_SERVER_PROXY, WX_CHAT_WND_NAME
    wx_chat = WeChatWnd(WX_CHAT_WND_NAME)
    redis_server = redis.StrictRedis(connection_pool=redis.ConnectionPool(**WX_REDIS_CONFIG))
    hash_key = hashlib.md5(biz.encode("utf-8")).hexdigest()
    key_uin = redis_server.get(hash_key)

    while not key_uin:
        try:
            wx_chat.send_msg(article_url)
            wx_chat.click_last_msg()
            key_uin = redis_server.get(hash_key)
        except Exception as e:
            print(e.args)
            sleep(0.2)
        finally:
            wx_chat.close_web()
            sleep(2)

    return key_uin.split("|")


if __name__ == "__main__":
    pass
