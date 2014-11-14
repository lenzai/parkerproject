# -*- coding: utf-8 -*-
import scrapy
from scrapy import log
import itertools
import json
from scrapy import Selector
from groupon.items import GrouponItem
from scrapy import Request
from urlparse import urljoin
import re
from random import random
from datetime import datetime
# unknown directive...
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


class GrouponSpiderSpider(scrapy.Spider):
    name = "groupon_spider"
    allowed_domains = ["groupon.com"]
    location_data = [
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

    # alternative: use urlencode to build the queries (including page value)
    deals_categories_urls = [
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=hair-salons'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=hair-removal'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=nail-salons'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=cosmetic-procedures'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=skin-care'],
        ['Beauty', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=salons'],
        ['Spas', 'http://www.groupon.com/browse/deals/partial?address=%s?category=beauty-and-spas&category2=spa'],
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
        self.cron_id = random()
        self.insert_date = datetime.now()

    def start_requests(self):
        for url, location in itertools.product(self.deals_categories_urls, self.location_data):
            meta = {'category_name': url[0], 'merchant_locality': location[1]}
            url = url[1]
            location = location[0]
            if url.startswith('http://www.groupon.com/local/'):
                yield Request(url % location, meta=meta, callback=self.parse_deallist)
            elif url.startswith('http://www.groupon.com/browse/deals/partial?'):
                yield Request(url % location, meta=meta, callback=self.parse_json_deallist)
                # straight forward approach to depth search
                for page in range(2, 6):
                    yield Request(url % location + '&page=%d' % page, meta=meta, callback=self.parse_json_deallist)
            else:
                raise Exception('unexpected URL path %s' % url)

    def parse_json_deallist(self, response):
        assert 'application/json; charset=utf-8' == response.headers['Content-Type']
        deals_info = json.loads(response.body).get('deals', {})
        metadata = deals_info.pop('metadata', {})
        for idx, html in deals_info.iteritems():
            assert idx in ['dealsHtml', 'featuredHtml']
            from scrapy.http import HtmlResponse
            response = HtmlResponse(url=response.url, request=response.request, body=html.encode('utf-8'))
            for result in self.parse_deallist(response):
                yield result

    def parse_deallist(self, response):
        base_item = GrouponItem(
            insert_date=self.insert_date,
            category_name=response.meta['category_name'],
            merchant_locality=response.meta['merchant_locality'],
            provider_name='Groupon',
        )
        for idx, node in enumerate(response.selector.xpath('//*/figure[contains(@class,"deal-card")]')):
            item = GrouponItem(base_item)
            for field, xpath in {
                'url': 'a/@href',
                'small_image': 'a/img/@data-original',
                'title': './/p[contains(@class,"deal-title")]/text()',
                'merchant_name': './/p[contains(@class,"merchant-name")]/text()',
            }.iteritems():
                item[field] = node.xpath(xpath).extract().pop()

            item['description'] = ','.join(node.xpath('.//div[contains(@class,"description")]//text()').extract()).strip()
            # testing did no show any price. Need to fix the xpath ?!
            item['price'] = (node.xpath('.//s[contains(@class,"discount-price")]//text()').extract() or ["View price"]).pop()
            item['url'] = urljoin(response.url, item['url'])

            yield Request(item['url'], meta={'item': item}, callback=self.parse_deal)

        # alternative to complete depth search:
            # - metadata contains information on pages & number of available items, but it doesnt seem usable
            # - sending request for another page after successfully parsing a json response will provide the
            # most complete data, at the cost of 1 extra page downloaded indicated that the last request failed

    def parse_deal(self, response):
        item = response.meta['item']
        sel = Selector(response)
        item['savings'] = (sel.xpath('//*[@id="discount-percent"]/text()').extract() or ['N/A']).pop().strip()
        item['large_image'] = (sel.xpath('//*[@id="featured-image"]/@src').extract() or [None]).pop()
        item['expires_at'] = ' '.join(sel.xpath('//*[contains(@class,"limited-time")]//text()').extract() or
                                      sel.xpath('//*[contains(@class,"countdown-timer")]//text()').extract() or
                                      ['Ongoing']).strip()

        address_selector = (sel.xpath('//*[contains(@class,"address")]') or [None]).pop()
        address_text = address_selector.xpath('.//p//text()').extract() if address_selector else []
        last_line = address_text.pop() if address_text else ''
        item['phone'] = last_line if re.match(r'^\D*(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$', last_line, re.M | re.I) \
            else ''
        item['merchant_address'] = '\n'.join(address_text).strip()

        return item
