# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from scrapy.exceptions import DropItem
from scrady.items import BaseAd, PropertyAd


class ScradyPipeline(object):
    def process_item(self, item, spider):
        return item

class ValidateItemPipeline():
    '''Pipeline used for validating items from items.py.

    This calls is_valid method from item. See items implementation for details.
    '''
    def process_item(self, item, spider):
        try:
            item.is_valid()
        except DropItem:
            raise
        else:
            return item

class MongoPipeline():
    '''Base MongoDB pipeline class to manage connections.
    MONGO_URI,MONGO_DATABASE are set on settings.py via .env file. See settings.py

    Variables:
        MONGO_URI: by default 'localhost'
        MONGO_DATABASE: by default 'scrapy_items'
        collection_name: by default spider.name
    '''

    def __init__(self, mongo_uri, mongo_db, collection_name):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.collection_name = collection_name

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE'),
            collection_name=crawler.spider.name
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        raise NotImplementedError('This is a base class to inherit for pipelines using DB connection.')
        

class DuplicatesPipeline(MongoPipeline):
    def process_item(self, item, spider):
        try:
            dbitem=self.db[self.collection_name].find({'id':item['id']})
        except:
            spider.logger.exception('Error querying item in db')
            return item

        if dbitem:
            DropItem(f'Item with url={item["url"]} already saved in MongoDB')
        if dbitem.count()>=2:
            spider.logger.warning(f'MongoDB has duplicated item in {self.mongo_db}.{self.collection_name} with id<{item["id"]}>')

        return item

class SaveItem(MongoPipeline):
    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))

        return item