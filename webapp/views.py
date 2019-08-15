# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/8/15 17:50
# @File   : views.py
from webapp import app


@app.route("/", methods=['GET'])
def wx_index():

    return ""


if __name__ == '__main__':
    pass
