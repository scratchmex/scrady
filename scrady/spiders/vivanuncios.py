# -*- coding: utf-8 -*-
import scrapy
import json
import re
import phonenumbers
from urllib.parse import urljoin
from functools import partial
from scrapy.http import Request
from html import unescape
from scrapy.exceptions import CloseSpider
from ..items import PropertyAd

class VivanunciosSpider(scrapy.Spider):
    ''''Spider for vivanuncios.com.mx.
    
    You can set start_url attribute otherwise default url will be used or edit start_urls list. See usage.
    By default this spider expects a search page. See default start_url. You can override this by reimplementing the parse function
    Usage:
        scrapy crawl vivanuncios
        scrapy crawl vivanuncios -a start_url=<url>
    '''
    name = 'vivanuncios'
    allowed_domains = ['vivanuncios.com.mx']
    start_urls = [
        'https://www.vivanuncios.com.mx/s-renta-inmuebles/solidaridad/v1c1098l11804p1',
        'https://www.vivanuncios.com.mx/s-venta-inmuebles/v1c1097p1',
        'https://www.vivanuncios.com.mx/s-renta-inmuebles/v1c1098p1'
    ]
    base_url='https://www.vivanuncios.com.mx/'

    adInfo_pattern=re.compile(r'(\["s.+?\]),(?=\["s)')

    translations={
        'category':{
            'renta':'rent',
            'venta':'sell',
        },
        'estate_type':{
            'departamento':'department',
            'casa':'house',
            'terreno':'land'
        },
        'attributes':{
            'AreaInMeters':'areaInMeters',
            'NumberBedrooms':'numberBedrooms',
            'NumberBathrooms':'numberBathrooms',
            'Parking':'parking'
        },
        'sellerType':{
            'agencia':'agency',
            'inmobiliaria':'agency',
            'particular':'particular'
        }
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_url=start_url

    def start_requests(self):
        if self.start_url:
            print(f'Got start url{self.start_url}')
            self.start_urls=[self.start_url]
        yield from super().start_requests()

    def parse(self, response):
        #parse search page by default
        yield from self.parse_search_page(response)

    def parse_search_page(self, response):
        next_url=response.css('a.arrows.icon-right-arrow::attr(href)').get()
        if next_url:
            yield response.follow(next_url, callback=self.parse_search_page)

        ads_urls=response.css('a.href-link::attr(href)').getall()

        for ad_url in ads_urls:
            yield response.follow(ad_url, callback=self.parse_ad_page)

    def parse_ad_page(self, response):
        item=PropertyAd(url=response.url)
        if response.css('body.Error404').get():
            self.logger.error(f'Getting 404. URL: <{response.url}>')
            return
        adId=response.css('input[name="adId"]::attr(value)').get()
        if not adId:
            self.logger.error(f'No adId?. URL: <{response.url}>')
            return
        try:
            possibles_adInfo=response.css('script::text').re(self.adInfo_pattern, replace_entities=False)
            adInfo=next(filter(lambda i: str(adId) in i, possibles_adInfo))
            adInfo=json.loads(adInfo)[3]['s']
        except Exception as e:
            self.logger.exception(f'Exception while parsing adInfo. This is bad!. URL: <{response.url}>')
            return
        
        raw_PropertyType=adInfo['generalDetails']['attributes'][0]['value'].lower()
        item['estate_type']=''
        for s,e in self.translations['estate_type'].items():
            if s in raw_PropertyType:
                item['estate_type']=e
                break
        item['category']=''
        for s,e in self.translations['category'].items():
            if s in raw_PropertyType:
                item['category']=e
                break

        item['title']=unescape(adInfo['adTitle'])

        item['price']={
            'amount': adInfo['adSummary']['price']['amount'],
            'currency': adInfo['adSummary']['price']['currency']
        }

        item['geocoordinates']={
            'latitude': adInfo['location']['latitude'],
            'longitude': adInfo['location']['longitude']
        }

        item['description']=unescape(adInfo['description']['description'])
        try:
            raw_phone=adInfo['replyInfo']['adPhone']
            phone=phonenumbers.parse(raw_phone, 'MX')
            item['phone']=int(str(phone.country_code)+str(phone.national_number))
        except KeyError:
            pass

        item['seller']['name']=adInfo['adSummary']['sellerName']
        item['seller']['url']=urljoin(self.base_url, adInfo['adSummary']['sellerLink'])
        raw_sellerType=adInfo['generalDetails']['attributes'][-1]['value'].lower()
        try:
            item['seller']['type']=self.translations['sellerType'][raw_sellerType]
        except KeyError:
            pass

        raw_attributes=adInfo['generalDetails']['attributes'][0:-1]
        for i in raw_attributes:
            if i['attrName'] in self.translations['attributes']:
                attribute=self.translations['attributes'][i['attrName']]
                item['attributes'][attribute]=i['value']

        return item
        
