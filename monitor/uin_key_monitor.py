# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/8/7 15:25
# @File   : uin_key_monitor.py
import time
import hashlib
import redis
from webapp import models, db
from tools import get_pass_key_and_uin
from settings import WX_REDIS_CONFIG, WX_ACCOUNT_BIZ_SET


def uin_key_monitor():

    redis_server = redis.StrictRedis(connection_pool=redis.ConnectionPool(**WX_REDIS_CONFIG))
    while 1:
        account_list = models.Account.query.all()
        db.session.commit()
        for account in account_list:
            print(account)
            account_biz = account.account_biz
            account_url = account.account_url
            hash_key = hashlib.md5(account_biz.encode("utf-8")).hexdigest()
            key_uin = redis_server.get(hash_key)
            if not key_uin:
                key_uin = get_pass_key_and_uin(account_url, account_biz)
                if key_uin and len(key_uin) == 2:
                    redis_server.set(hash_key, "|".join(key_uin))
                print(hash_key, account_biz, account_url, key_uin[1], key_uin[0])
            time.sleep(2)


if __name__ == '__main__':
    uin_key_monitor()
