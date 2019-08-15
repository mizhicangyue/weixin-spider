# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/8/2 15:15
# @File   : comment_monitor.py
import re
import time

from pyquery import PyQuery

from api import get_history_api, get_html_api, get_article_comments_api, get_article_read_like_api, \
    split_article_url2mis
from crawlerpage import models
from crawlerpage import db
from exceptions import KeyExpireError, IPError, ArticleHasBeenDeleteError
from functions import get_pass_key_and_uin
from settings import SLEEP_TIME, WX_UPDATE_TIME, WX_NOT_UPDATE_TIME


class ReadLikeMonitor:
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
                article_done=True,
            ).filter(
                models.Article.article_fail == False,
                models.Article.read_like_update < time.time() - WX_UPDATE_TIME,
                models.Article.article_publish_time > time.time() - WX_NOT_UPDATE_TIME,
            ).all()
            db.session.commit()
            for article in article_list:
                print("文章评论开始同步；", article)
                try:
                    self._run(article.id)
                    print("文章评论已同步完成；", article)
                except Exception as e:
                    print(e)
                    raise
                finally:
                    time.sleep(2)
                # break
            while time.time() - s_time < SLEEP_TIME:
                time.sleep(1)

    def _run(self, article_id):
        article = models.Article.query.get(article_id)
        article_url = article.article_content_url
        comment_id = article.article_comment_id
        biz = models.Account.query.get(article.account_id).account_biz
        if not self.key_dict.get(biz, None):
            self.key_dict[biz] = get_pass_key_and_uin(article_url)
        print(self.key_dict[biz])
        while 1:
            try:
                print(article_url)
                print(split_article_url2mis(article_url))
                read_like = get_article_read_like_api(
                    biz=biz,
                    key=self.key_dict[biz][0],
                    uin=self.key_dict[biz][1],
                    comment_id=comment_id,
                    **split_article_url2mis(article_url))
                read_like = read_like["results"]
                article.read_count = read_like['read_count']
                article.like_count = read_like['like_count']
                article.read_like_update = str(int(time.time()))
                db.session.add(article)
                db.session.commit()
                break
            except KeyExpireError:
                time.sleep(SLEEP_TIME)
                print("save_each_batch_articles comment", self.key_dict[biz])
                self.key_dict[biz] = get_pass_key_and_uin(article_url)
                print("save_each_batch_articles comment", self.key_dict[biz])
            finally:
                time.sleep(1)

    @staticmethod
    def save_comment(article_id, comment_dict):
        for comment_item in comment_dict['comments']:
            if models.Comment.query.filter_by(content_id=str(comment_item["content_id"])).count() == 0:
                comment = models.Comment(
                    user_name=comment_item["user_name"],
                    user_logo=comment_item["user_logo"],
                    content=comment_item["content"],
                    datetime=str(comment_item["datetime"]),
                    content_id=str(comment_item["content_id"]),
                    like_count=int(comment_item["like_count"]),
                    article_id=article_id
                )
                db.session.add(comment)
                db.session.commit()
            comment = models.Comment.query.filter_by(content_id=str(comment_item["content_id"])).first()
            reply_list = comment_item["reply_list"]
            # print(reply_list)
            for reply_item in reply_list:
                reply = models.CommentReply(
                    **reply_item,
                    comment_id=comment.id
                )
                db.session.add(reply)
                db.session.commit()


if __name__ == '__main__':
    ReadLikeMonitor().start()
