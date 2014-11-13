# -*- coding: utf-8 -*-
import scrapy
from scrapy import log
import itertools
import json
from scrapy import Selector
from groupon.items import GrouponItem
from scrapy import Request
from urlparse import urljoin


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
            deals_info.pop('metadata', None)
        except ValueError:
            self.log("Exception raised during json load: %s" % response.url, log.DEBUG)
            deals_info = {'body': response.body}

        for string in deals_info.values():
            for node in Selector(text=string).xpath('//*/figure[contains(@class,"deal-card")]'):
                base_item = GrouponItem('Today')
                for field, xpath in {
                    'url': 'a/@href',
                    'small_image': 'a/img/@data-original',
                    'title': './/p[contains(@class,"deal-title")]/text()',
                    'merchant_name': './/p[contains(@class,"merchant-name")]/text()',
                }.iteritems():
                    base_item[field] = node.xpath(xpath).extract().pop()

                base_item['description'] = ' '.join(node.xpath('.//div[contains(@class,"description")]//text()').extract()).strip()
                base_item['price'] = (node.xpath('.//div[contains(@class,"discount-price")]//text()').extract() or ["View price"]).pop()
                base_item['url'] = urljoin(response.url, base_item['url'])

                yield Request(
                    base_item['url'],
                    meta={'base_item': base_item},
                    callback=self.parse_deal)

    def parse_deal(self, response):
        self.log("parsing deal page: %s" % response.url, log.INFO)
        yield response.meta['base_item']
