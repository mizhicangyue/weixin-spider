# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/8/7 15:26
# @File   : wx_monitor.py
import time
import threading
import redis
import hashlib
from api import get_history_api
from crawlerpage import models
from crawlerpage import db
from exceptions import NoneKeyUinError, KeyExpireError
from settings import SLEEP_TIME, WX_REDIS_CONFIG


def delete_key_uin(account_biz):
    redis_server = redis.StrictRedis(connection_pool=redis.ConnectionPool(**WX_REDIS_CONFIG))
    hash_key = hashlib.md5(account_biz.encode("utf-8")).hexdigest()
    redis_server.delete(hash_key)


def get_key_uin(account_biz):
    redis_server = redis.StrictRedis(connection_pool=redis.ConnectionPool(**WX_REDIS_CONFIG))
    hash_key = hashlib.md5(account_biz.encode("utf-8")).hexdigest()
    key_uin = redis_server.get(hash_key)
    if not key_uin:
        raise NoneKeyUinError("NoneKeyUinError")
    return key_uin.split("|")


class _MonitorThread(threading.Thread):

    @staticmethod
    def update_obj(obj, **kwargs):
        for k, v in kwargs.items():
            setattr(obj, k, v)
        db.session.add(obj)
        db.session.commit()

    def run(self):
        self.setName(self.__class__.__name__)
        while 1:
            self.start_run()

    def start_run(self):
        pass


class History(_MonitorThread):

    def update_account(self, account, **kwargs):
        self.update_obj(account, **kwargs)

    def update_article(self, article, **kwargs):
        self.update_obj(article, **kwargs)

    @staticmethod
    def load_accounts():
        account_list = models.Account.query.filter_by(
            # status=1,
            # end=False,
            fail=False,
        ).order_by(
            models.Account.created.desc()
        ).all()
        db.session.commit()
        return [account for account in account_list if account.status in [1, 2]]

    @staticmethod
    def check_account_status(_id: int, status: int):
        status_flag = models.Account.query.get(_id).status == status
        db.session.commit()
        return status_flag

    @staticmethod
    def save_article(account_id, article_item):
        counts = models.Article.query.filter_by(
            article_content_url=article_item["article_content_url"],
            article_publish_time=article_item["article_publish_time"],
        ).count()
        new_article = False
        if counts == 0:
            article = models.Article(
                **article_item,
                account_id=account_id
            )
            print(article)
            db.session.add(article)
            db.session.commit()
            new_article = True
        return new_article

    def account_run(self, account_id):
        account = models.Account.query.get(account_id)
        account_biz = account.account_biz
        account_offset = account.offset
        account_key, account_uin = get_key_uin(account_biz)
        offset = 0
        one_add = False
        while 1:
            if not self.check_account_status(account_id, 2):
                break
            s_time = time.time()
            try:
                histories = get_history_api(**{
                    "key": account_key,
                    "uin": account_uin,
                    "biz": account_biz,
                    "offset": offset,
                })
                ending = histories['ending']
                next_offset = histories["next_offset"]
                print(f"biz: {account_biz} offset: {offset} next_offset: {next_offset}")
                article_items = histories["results"]["article_infos"]
                new_article = False
                for article_item in article_items:
                    print(article_item)
                    if not article_item["article_content_url"]:
                        continue
                    if new_article:
                        self.save_article(account_id, article_item)
                    else:
                        new_article = self.save_article(account_id, article_item)

                account.counts = models.Article.query.filter_by(account_id=account.id).count()
                if account_offset == 0:
                    account.offset = offset
                    offset = next_offset
                elif new_article:
                    if one_add:
                        account.offset = offset
                    offset = next_offset
                else:
                    print(f"biz: {account_biz} 当前offset: {offset}文章都存在 next_offset: {next_offset}")
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
                self.update_obj(account)
                print(account)
                if ending:
                    break
            except KeyExpireError:
                delete_key_uin(account_biz)
                raise NoneKeyUinError(f"key: {account_key} 已过期 offset: {offset}")
            while time.time() - s_time < SLEEP_TIME:
                time.sleep(0.1)

    def start_run(self):
        account_list = self.load_accounts()
        print(account_list)
        for account in account_list:

            account_id = account.id
            account_biz = account.account_biz
            try:
                if not get_key_uin(account_biz):
                    raise NoneKeyUinError("NoneKeyUinError")
                print("开始同步；", account)
                self.update_account(account, status=2)
                self.account_run(account_id)
                self.update_account(account, status=0, update=str(int(time.time())))
                print("数据已同步；", account)
            except NoneKeyUinError:
                print("NoneKeyUin: ", account)
            finally:
                if self.check_account_status(account_id, 2):
                    self.update_account(account, status=1)
                time.sleep(SLEEP_TIME)


class Article(_MonitorThread):
    def start_run(self):
        time.sleep(SLEEP_TIME)


class Comment(_MonitorThread):
    def start_run(self):
        time.sleep(SLEEP_TIME)


class ReadLike(_MonitorThread):
    def start_run(self):
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    # thread_list = []
    # for thread_name in ["History", "Article", "Comment", "ReadLike"]:
    #     thread_list.append(globals()[thread_name]())

    thread_list = [globals()[thread_name]() for thread_name in ["History", "Article", "Comment", "ReadLike"]]

    while 1:
        for thread in thread_list:
            if not thread.is_alive():
                thread.start()
                print("thread.start: ", thread.name)
            time.sleep(1)
