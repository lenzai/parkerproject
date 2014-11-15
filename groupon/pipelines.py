# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import log
from items import GrouponItem

import sys
sys.dont_write_bytecode = True
# legacy code
try:
    from pymongo.mongo_replica_set_client import MongoReplicaSetClient
    import os

    MONGO_URL = os.environ['boxedsales_mongo_url']
    mongo_set = True

    client = MongoReplicaSetClient(MONGO_URL, replicaSet='set-543c2c03128e2799a7007378')
    db = client.Boxedsales
    dealsCollection = db.deals
    cronCollection = db.cron

    db_import_success = True
except ImportError:
    db_import_success = False


class GrouponPipeline(object):
    """
    Naive merge of legacy Mongo DB
    Should be better to use ScrapyMongo dedicated pipeline !?
    e.g.: https://github.com/sebdah/scrapy-mongodb
    """
    def process_item(self, item, spider):
        # legacy code - untested and should probably be rewritten in a feed exporter
        if isinstance(item, GrouponItem) and db_import_success and item['price'] != 'View price':
            dealsCollection.update({"title": item['title']}, item, upsert=True)
            cronCollection.update({"batch_id": spider.cron_id},
                                  {"batch_id": spider.cron_id, "network": "Groupon", "cron_date": spider.insert_date},
                                  upsert=True)
            spider.log('inserted deal', log.INFO)  # from original print
            # return  # if we don't want the item to appear in other pipelines & std output
        return item
