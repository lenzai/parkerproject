# -*- coding: utf-8 -*-
import scrapy


class GrouponSpiderSpider(scrapy.Spider):
    name = "groupon_spider"
    allowed_domains = ["groupon.com"]
    start_urls = (
        'http://www.groupon.com/',
    )

    def parse(self, response):
        pass
