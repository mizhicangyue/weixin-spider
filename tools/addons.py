# -*- coding: utf-8 -*-
# @Time    : 2019/8/13 20:17
# @Author  : xzkzdx
# @File    : addons.py
import json
import re
from urllib.parse import unquote
import hashlib

import mitmproxy as mp
import redis

from settings import WX_REDIS_CONFIG


class WeiXinProxy:
    redis_server = redis.StrictRedis(connection_pool=redis.ConnectionPool(**WX_REDIS_CONFIG))

    def __init__(self):
        pass

    def uin_md5(self, uin):
        if "%" in uin:
            uin = self.uin_md5(unquote(uin))
        return uin

    def request(self, flow: mp.http.HTTPFlow):
        if flow.request.host == "mp.weixin.qq.com":
            url_path = flow.request.path
            if url_path.startswith("/s?__biz=") and "uin=" in url_path and "key=" in url_path:
                biz = re.search(r"__biz=([^&]+)&?", url_path).group(1)
                key = re.search(r"key=([^&]+)&?", url_path).group(1)
                uin = re.search(r"uin=([^&]+)&?", url_path).group(1)
                hash_key = hashlib.md5(biz.encode("utf-8")).hexdigest()
                self.redis_server.set(hash_key, json.dumps({
                    "key": key,
                    "uin": uin
                }, ensure_ascii=False))


addons = [
    WeiXinProxy()
]

if __name__ == "__main__":
    pass
