# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from scrapy.exceptions import DropItem
from scrady.items import BaseAd, PropertyAd
from warnings import warn


class ScradyPipeline(object):
    def process_item(self, item, spider):
        return item

class ValidateItemPipeline():
    '''Pipeline used for validating items from items.py.

    Steps to add a class to validate:
    - Add the class name if statement in process_item function
    - Implement a validate_classname function as classmethod. 
    This function should raise a DropItem exception if item not valid
    '''
    def process_item(self, item, spider):
        if isinstance(item, BaseAd):
            self.validate_BaseAd(item)
        if isinstance(item, PropertyAd):
            self.validate_PropertyAd(item)
            
    @staticmethod
    def validateVariables(obj, objname, objid, vars):
        '''Function to validate if a variable is set on a class. 
        
        If the variable not in object scrapy.DropItem is called.
        See implementations for details.
        '''
        for var in vars:
            if var not in obj:
                DropItem(f'{objname}[{var}] missing in {objid}. Dropping item.')
        
    @classmethod
    def validate_BaseAd(cls, item):
        nonlocal item
        itemClassname=item.__class__.__name__
        if not item.get('type'):
            DropItem(f'type of ad missing in {itemClassname}')
        if not item.get('url'):
            DropItem(f'URL not saved in {itemClassname}')
        if not item.get('id'):
            warn(f'{itemClassname} not generating id hash. Setting it myself', RuntimeWarning)
            item['id']=hash(item['id'])

    @classmethod
    def validate_PropertyAd(cls, item):
        requiredFields=[
            'type',
            'category',
            'estate_type',
            'title',
            'price',
            'description'
        ]

        cls.validateVariables(item, 'item', item['url'], requiredFields)
        cls.validateVariables(item['price'], 'price', item['url'], ('amount','currency'))
        cls.validateVariables(item['geocoordinates'], 'geocoordinates', item['url'], ('latitude','longitude'))


class MongoPipeline():
    '''Base MongoDB pipeline class to manage connections.

    Variables:
        MONGO_URI,MONGO_DATABASE: are set on settings.py via .env file. See settings.py
        collection_name: by default the spider.name
    '''
    collection_name = 'scrapy_items'

    def __init__(self, mongo_uri, mongo_db, collection_name):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

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
        itemCount=self.db[self.collection_name].find_one({'id':item['id']}).count()
        if itemCount!=0:
            DropItem(f'Item with url={item["url"]} already saved in MongoDB')

        return item

class SaveItem(MongoPipeline):
    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item