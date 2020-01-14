# -*- coding: utf-8 -*-
import scrapy


class VivaanunciosSpider(scrapy.Spider):
    name = 'vivaanuncios'
    allowed_domains = ['vivaanuncios.com']
    start_urls = ['https://vivaanuncios.com/']

    def parse(self, response):
        pass
