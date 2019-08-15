# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/7/11 16:47
# @File   : account_monitor.py
import re
import time
from pyquery import PyQuery
from crawlerpage.models import Account, Article, Comment, CommentReply
from crawlerpage import db
from api import *
from functions import get_pass_key_and_uin
from settings import SLEEP_TIME, DOWNLOAD_DELAY
from exceptions import KeyExpireError, NoneValueError, ArticleHasBeenDeleteError, IPError


class WeiXin:
    @staticmethod
    def get_comment_id_from_html(res_html):
        return re.search(r"comment_id = .*?\"([\d]+)\"", res_html).group(1)

    @staticmethod
    def get_content_from_html(res_html):
        # return re.search(r"(.*)", res_html).group(1)
        # print(PyQuery(res_html)("#js_content").html())
        return PyQuery(res_html)("#js_content").html().replace("\n", "").strip()

    @staticmethod
    def get_uin_from_html(res_html):
        return re.search(r"window.uin = params.*?\"([\w]+==)\"", res_html).group(1)

    @staticmethod
    def get_key_from_html(res_html):
        return re.search(r"window.key = params[^\"]*?\"([\w]+)\"", res_html).group(1)


class Monitor:

    def __init__(self):
        self.wx = WeiXin()
        self.key_dict = {}

    @staticmethod
    def check_account_status(_id: int, status: int):
        db.session.commit()
        status_flag = Account.query.get(_id).status == status
        db.session.commit()
        return status_flag

    def save_each_history(self, _id, account_url, info_dict, article_item):
        article_url = article_item["article_content_url"]
        new_article = False
        while 1:
            try:
                read_like = get_article_read_like_api(**info_dict, **split_article_url2mis(article_url))
                read_like = read_like["results"]
                article_item['read_count'] = read_like.get("read_count")
                article_item['like_count'] = read_like.get("like_count")
                articles = Article.query.filter_by(
                    article_title=article_item["article_title"],
                    article_content_url=article_item["article_content_url"],
                    article_publish_time=article_item["article_publish_time"],
                ).all()
                if len(articles) == 0:
                    article = Article(
                        **article_item,
                        account_id=_id
                    )
                    new_article = True
                else:
                    article = articles[0]
                    article.read_count = read_like.get("read_count")
                    article.like_count = read_like.get("like_count")
                db.session.add(article)
                db.session.commit()
                return new_article
            except (KeyExpireError, KeyError) as e:
                print("save_each_batch_articles save_each_history")
                self.key_dict[info_dict['biz']] = get_pass_key_and_uin(account_url)
                info_dict["key"], info_dict["uin"] = self.key_dict[info_dict['biz']]
            # time.sleep(0.1)

    def save_each_batch_articles(self, _id, account_url, info_dict):
        articles = Article.query.filter_by(
            account_id=_id,
            article_done=False,
        ).all()
        for article in articles:
            article_url = article.article_content_url
            article_html = None
            try:
                while article_html is None:
                    try:
                        article_html = get_html_api(article_url, use_key=True, **info_dict)
                    except IPError:
                        article_html = get_html_api(article_url, use_key=True,  **info_dict)
                    except (KeyExpireError, IPError):
                        print("save_each_batch_articles article_html")
                        self.key_dict[info_dict['biz']] = get_pass_key_and_uin(account_url)
                        info_dict["key"], info_dict["uin"] = self.key_dict[info_dict['biz']]
                    time.sleep(DOWNLOAD_DELAY)
            except ArticleHasBeenDeleteError:
                article.article_done = True
                article.article_fail = True
                db.session.add(article)
                db.session.commit()
                continue
            article.article_content = self.wx.get_content_from_html(article_html)

            comment_id = self.wx.get_comment_id_from_html(article_html)
            if comment_id == "0":
                continue
            while 1:
                try:
                    comment_dict = get_article_comments_api(comment_id=comment_id, **info_dict)['results']
                    comment_count = comment_dict['comment_count']
                    for comment_item in comment_dict['comments']:
                        if Comment.query.filter_by(content_id=str(comment_item["content_id"])).count() == 0:
                            comment = Comment(
                                user_name=comment_item["user_name"],
                                user_logo=comment_item["user_logo"],
                                content=comment_item["content"],
                                datetime=str(comment_item["datetime"]),
                                content_id=str(comment_item["content_id"]),
                                like_count=int(comment_item["like_count"]),
                                article_id=article.id
                            )
                            # print(comment_item["content"])
                            db.session.add(comment)
                            db.session.commit()
                        comment = Comment.query.filter_by(content_id=str(comment_item["content_id"])).first()
                        reply_list = comment_item["reply_list"]
                        # print(reply_list)
                        for reply_item in reply_list:
                            reply = CommentReply(
                                **reply_item,
                                comment_id=comment.id
                            )
                            db.session.add(reply)
                            db.session.commit()
                    article.comment_count = comment_count
                    article.article_done = True
                    db.session.add(article)
                    db.session.commit()
                    break
                except KeyExpireError:
                    print("save_each_batch_articles comment", self.key_dict[info_dict['biz']])
                    self.key_dict[info_dict['biz']] = get_pass_key_and_uin(account_url)
                    info_dict["key"], info_dict["uin"] = self.key_dict[info_dict['biz']]
                    print("save_each_batch_articles comment", self.key_dict[info_dict['biz']])
                # time.sleep(0.1)

    def account_run(self, _id: int):
        account = Account.query.get(_id)
        biz = account.account_biz
        account_offset = account.offset
        account_url = account.account_url
        self.key_dict[biz] = get_pass_key_and_uin(account_url)
        offset = 0
        one_add = False
        while 1:
            if not self.check_account_status(_id, 2):
                break
            s_time = time.time()
            try:
                histories = get_history_api(**{
                    "key": self.key_dict[biz][0],
                    "uin": self.key_dict[biz][1],
                    "biz": biz,
                    "offset": offset,
                })
                ending = histories['ending']
                next_offset = histories["next_offset"]
                print(f"biz: {biz} offset: {offset} next_offset: {next_offset}")
                article_items = histories["results"]["article_infos"]
                new_article = False
                for article_item in article_items:
                    if new_article:
                        self.save_each_history(_id, account_url, {
                            "key": self.key_dict[biz][0],
                            "uin": self.key_dict[biz][1],
                            "biz": biz,
                        }, article_item)
                    else:
                        new_article = self.save_each_history(_id, account_url, {
                            "key": self.key_dict[biz][0],
                            "uin": self.key_dict[biz][1],
                            "biz": biz,
                        }, article_item)
                    self.save_each_batch_articles(_id, account_url, {
                        "key": self.key_dict[biz][0],
                        "uin": self.key_dict[biz][1],
                        "biz": biz,
                    })
                account.counts = Article.query.filter_by(account_id=account.id).count()

                if account_offset == 0:
                    account.offset = offset
                    offset = next_offset
                elif new_article:
                    if one_add:
                        account.offset = offset
                    offset = next_offset
                else:
                    print(f"biz: {biz} 当前offset: {offset}文章都存在 next_offset: {next_offset}")
                    if one_add or account_offset == 0:
                        account.offset = offset
                        offset = next_offset
                    else:
                        offset += account_offset
                        account.offset = offset
                        one_add = True
                if ending:
                    account.offset = offset
                    account.end = True
                db.session.add(account)
                db.session.commit()
                if ending:
                    break
            except KeyExpireError:
                self.key_dict[biz] = get_pass_key_and_uin(account_url)
                time.sleep(0.1)
            # print("将在%s秒后开始下一次爬取" % abs(time.time() - s_time - SLEEP_TIME))
            while time.time() - s_time < SLEEP_TIME:
                time.sleep(1)

    def start(self):
        while 1:
            account_list = Account.query.filter_by(
                status=1,
                # end=False,
                fail=False,
            ).order_by(
                Account.created.desc()
            ).all()
            db.session.commit()
            for account in account_list:
                _id = account.id
                account.status = 2
                db.session.add(account)
                db.session.commit()
                try:
                    self.account_run(_id)
                    account.status = 0
                    db.session.add(account)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    if self.check_account_status(_id, 2):
                        account.status = 1
                        db.session.add(account)
                        db.session.commit()
                    raise
                time.sleep(1)
                # break
            time.sleep(2)
            # break


if __name__ == '__main__':
    Monitor().start()
