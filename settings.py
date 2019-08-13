# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/6/21 11:15
# @File   : settings.py

SLEEP_TIME = 10  # 调用时建议使用的睡眠时间，以免账号被限制

USER_AGENT_WECHAT = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 QBCore/3.53.1159.400 QQBrowser/9.0.2524.400 Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"

WX_REDIS_CONFIG = {
    'host': 'localhost',
    'password': None,
    'port': 6379,
    'db': 0,
    'decode_responses': True,
}

WX_ACCOUNT_BIZ_SET = "wx_account_BIZ"

WX_UPDATE_TIME = 60 * 60 * 24
WX_NOT_UPDATE_TIME = 60 * 60 * 24 * 7

WX_CHAT_WND_NAME = "文件传输助手"

DOWNLOAD_DELAY = 1

FIDDLER_SERVER_PROXY = "127.0.0.1:8888"
FIDDLER_REQUEST_FILEPATH = "C:/Fiddler/headers/request.txt"
FIDDLER_RESPONSE_FILEPATH = "C:/Fiddler/headers/response.txt"
