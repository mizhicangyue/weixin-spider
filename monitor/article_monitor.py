# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/8/2 15:19
# @File   : article_monitor.py
import re
import time

from pyquery import PyQuery

from api import get_history_api, get_html_api
from crawlerpage import models
from crawlerpage import db
from exceptions import KeyExpireError, IPError, ArticleHasBeenDeleteError
from functions import get_pass_key_and_uin
from settings import SLEEP_TIME


class ArticleMonitor:
    def __init__(self):
        self.key_dict = {}

    @staticmethod
    def get_content_from_html(res_html):
        # return re.search(r"(.*)", res_html).group(1)
        # print(PyQuery(res_html)("#js_content").html())
        # js_content = PyQuery(res_html)("#js_content").html().replace("\n", "").strip()
        # js_content = re.sub(r'data-src', "src", js_content)
        return PyQuery(res_html)("#js_content").html().replace("\n", "").strip()

    @staticmethod
    def get_comment_id_from_html(res_html):
        return re.search(r"comment_id = .*?\"([\d]+)\"", res_html).group(1)

    @staticmethod
    def check_account_status(_id: int, status: int):
        db.session.commit()
        status_flag = models.Account.query.get(_id).status == status
        db.session.commit()
        return status_flag

    def start(self):
        while 1:
            s_time = time.time()
            article_list = models.Article.query.filter_by(
                article_done=False,
            ).order_by(
                models.Article.article_publish_time.desc()
            ).all()
            db.session.commit()
            for article in article_list:
                print("文章开始同步；", article)
                article_id = article.id
                try:
                    self._run(article_id)
                    print("文章已同步；", article)
                except Exception as e:
                    print(e)
                    raise
                time.sleep(1)
                # break
            while time.time() - s_time < SLEEP_TIME:
                time.sleep(1)

    def _run(self, article_id):
        article = models.Article.query.get(article_id)
        article_url = article.article_content_url
        biz = models.Account.query.get(article.account_id).account_biz
        try:
            if self.key_dict.get(biz, None):
                article_url = article_url + '&key=%s&ascene=1&uin=%s' % (
                    self.key_dict[biz][0], self.key_dict[biz][1]
                )
            article_html = get_html_api(article_url)

            comment_id = self.get_comment_id_from_html(article_html)

            article.article_html = self.get_content_from_html(article_html)
            article.article_comment_id = comment_id
            article.article_done = True
        except ArticleHasBeenDeleteError:
            article.article_fail = True
            article.article_done = True
        except IPError:
            self.key_dict[biz] = get_pass_key_and_uin(article_url)
        finally:
            db.session.add(article)
            db.session.commit()

    @staticmethod
    def save_article(_id, article_item):
        counts = models.Article.query.filter_by(
            article_content_url=article_item["article_content_url"],
            article_publish_time=article_item["article_publish_time"],
        ).count()
        new_article = False
        if counts == 0:
            article = models.Article(
                **article_item,
                account_id=_id
            )
            db.session.add(article)
            db.session.commit()
            new_article = True
        return new_article


if __name__ == '__main__':
    ArticleMonitor().start()
