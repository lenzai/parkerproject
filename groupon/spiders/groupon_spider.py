# -*- coding: utf-8 -*-
import scrapy
from scrapy import log
import itertools
import json
from scrapy import Selector


class GrouponSpiderSpider(scrapy.Spider):
    name = "groupon_spider"
    allowed_domains = ["groupon.com"]
    locations = [
        ['new-york-city', 'new york'],
        ['manhattan', 'new york'],
        ['boston', 'boston'],
        ['chicago', 'chicago'],
        ['dallas', 'dallas'],
        ['houston', 'houston'],
        ['los-angeles', 'los angeles'],
        ['las-vegas', 'las vegas'],
        ['miami', 'miami'],
        ['philadelphia', 'philadelphia'],
        ['san-diego', 'san diego'],
        ['san-francisco', 'san francisco'],
        ['seattle', 'seattle'],
        ['washington-dc', 'washington dc'],
        ['phoenix', 'phoenix']
    ]


    deal_pages = [
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=hair-salons'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=hair-removal'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=nail-salons'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=cosmetic-procedures'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=skin-care'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=salons'],
        ['Spas', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=spa&page='],
        ['Spas', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=massage'],
        ['Food, Drinks', 'http://www.groupon.com/browse/deals/partial?address=%s?category=food-and-drink'],
        ['Fitness', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=gyms'],
        ['Fitness', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=sports'],
        ['Health', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=weight-loss'],
        ['Health', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=natural-medicine'],
        ['Health', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=medical'],
        ['Dental', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=dental'],
        ['Health', 'http://www.groupon.com/browse/deals/partial?address=%s?category=health-and-fitness&category2=vision'],
        ['Services', 'http://www.groupon.com/local/%s/home-improvement'],
        ['Services', 'http://www.groupon.com/local/%s/local-services'],
        ['Shopping', 'http://www.groupon.com/local/%s/shopping'],
        ['Activities', 'http://www.groupon.com/browse/deals/partial?address=%s?category=things-to-do&category2=activities'],
        ['Activities', 'http://www.groupon.com/browse/deals/partial?address=%s?category=things-to-do&category2=classes'],
        ['Activities', 'http://www.groupon.com/browse/deals/partial?address=%s?category=things-to-do&category2=nightlife'],
        ['Events', 'http://www.groupon.com/browse/deals/partial?address=%s?category=things-to-do&category2=tickets-and-events'],
        ['Activities', 'http://www.groupon.com/browse/deals/partial?address=%s?category=things-to-do&category2=sightseeing']
    ]


    def __init__(self, *a, **kw):
        super(GrouponSpiderSpider, self).__init__(*a, **kw)
        self.start_urls = self.start_urls_generator()

    def start_urls_generator(self):
        for url, location in itertools.product(self.deal_pages, self.locations):
            yield url[1] % location[0]

    def parse(self, response):
        try:
            deals_info = json.loads(response.body).get('deals', {})
        except Exception as e:
            self.log("Exception raised during json load: %s" % str(e), log.ERROR)
            deals_info = {}

        for key, val in deals_info.iteritems():
            if key == 'metadata':
                continue
            sel = Selector(text=val)

            for node in sel.xpath('//*/figure[contains(@class,"deal-card")]'):
                for val, xpath in {
                    "href": 'a/@href',
                    "image": 'a/img/@data-original',
                    "title": './/p[contains(@class,"deal-title")]/text()',
                    "merchant": './/p[contains(@class,"merchant-name")]/text()',
                }.iteritems():
                    self.log("found %s: %s" % (val, node.xpath(xpath).extract().pop()), log.DEBUG)

                self.log("found description: %s" % '\n'.join(node.xpath('.//div[contains(@class,"description")]//text()').extract()), log.DEBUG)
                price = node.xpath('.//div[contains(@class,"discount-price")]//text()').extract()
                self.log("found price: %s" % price.pop() if price else "View price", log.DEBUG)
