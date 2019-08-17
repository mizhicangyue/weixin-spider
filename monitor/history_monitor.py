# -*- encoding: utf-8 -*-
# !/usr/bin/python3
# @Time   : 2019/8/2 15:15
# @File   : history_monitor.py
import time

from api import get_history_api
from webapp import models
from webapp import db
from exceptions import KeyExpireError
from tools import get_pass_key_and_uin
from settings import SLEEP_TIME


class HistoryMonitor:
    def __init__(self):
        self.key_dict = {}

    @staticmethod
    def check_account_status(_id: int, status: int):
        db.session.commit()
        status_flag = models.Account.query.get(_id).status == status
        db.session.commit()
        return status_flag

    def start(self):
        while 1:
            account_list = models.Account.query.filter_by(
                status=1,
                # end=False,
                fail=False,
            ).order_by(
                models.Account.created.desc()
            ).all()
            db.session.commit()
            for account in account_list:
                print("开始同步；", account)
                account_id = account.id
                account.status = 2
                db.session.add(account)
                db.session.commit()
                try:
                    self._run(account_id)
                    account.status = 0
                    account.update = str(int(time.time()))
                    db.session.add(account)
                    db.session.commit()
                    print("数据已同步；", account)
                except Exception as e:
                    print(e)
                    if self.check_account_status(account_id, 2):
                        account.status = 1
                        db.session.add(account)
                        db.session.commit()
                    raise
                time.sleep(1)
                # break
            time.sleep(2)
            # break

    def _run(self, account_id):
        account = models.Account.query.get(account_id)
        biz = account.account_biz
        account_offset = account.offset
        account_url = account.account_url
        self.key_dict[biz] = get_pass_key_and_uin(account_url)
        offset = 0
        one_add = False
        while 1:
            if not self.check_account_status(account_id, 2):
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
                print(account)
                if ending:
                    break
            except KeyExpireError:
                self.key_dict[biz] = get_pass_key_and_uin(account_url, account.account_biz)
                # time.sleep(0.1)
                print(f"key 过期 offset: {offset}")
            # print("将在%s秒后开始下一次爬取" % abs(time.time() - s_time - SLEEP_TIME))
            while time.time() - s_time < SLEEP_TIME:
                time.sleep(0.1)

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
            db.session.add(article)
            db.session.commit()
            new_article = True
        return new_article


if __name__ == '__main__':
    HistoryMonitor().start()
