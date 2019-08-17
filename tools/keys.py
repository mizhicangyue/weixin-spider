# -*- coding: utf-8 -*-
# @Time    : 2019/8/17 11:25
# @Author  : xzkzdx
# @File    : keys.py
import hashlib
import json
import time
import redis

from settings import WX_REDIS_CONFIG
from tools.handle import WeChatWnd
from settings import WX_CHAT_WND_NAME


def get_pass_key_and_uin(article_url: str, biz):
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
            time.sleep(0.2)
        finally:
            wx_chat.close_web()
            time.sleep(2)

    return json.loads(key_uin, encoding="utf-8")


if __name__ == "__main__":
    pass
