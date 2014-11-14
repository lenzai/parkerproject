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
            yield Request(url[1] % location[0], meta=meta)
            # straight forward approach to depth search
            if url[1].startswith('http://www.groupon.com/browse/deals/partial?'):
                for page in range(2, 6):
                    yield Request(url[1] % location[0] + '&page=%d' % page, meta=meta)

    def parse(self, response):
        try:
            deals_info = json.loads(response.body).get('deals', {})
            metadata = deals_info.pop('metadata', {})
        except ValueError:
            self.log("Exception raised during json load: %s" % response.url, log.DEBUG)
            deals_info = {'body': response.body}
            metadata = {}

        for key, string in deals_info.iteritems():
            for idx, node in enumerate(Selector(text=string).xpath('//*/figure[contains(@class,"deal-card")]')):
                base_item = GrouponItem(self.insert_date,
                                        response.meta['category_name'],
                                        response.meta['merchant_locality'])
                for field, xpath in {
                    'url': 'a/@href',
                    'small_image': 'a/img/@data-original',
                    'title': './/p[contains(@class,"deal-title")]/text()',
                    'merchant_name': './/p[contains(@class,"merchant-name")]/text()',
                }.iteritems():
                    base_item[field] = node.xpath(xpath).extract().pop()

                base_item['description'] = ','.join(node.xpath('.//div[contains(@class,"description")]//text()').extract()).strip()
                # testing did no show any price. Need to fix the xpath ?!
                base_item['price'] = (node.xpath('.//s[contains(@class,"discount-price")]//text()').extract() or ["View price"]).pop()
                base_item['url'] = urljoin(response.url, base_item['url'])

                self.log("loop%d in %s" % (idx, key), log.INFO)  # from original print
                yield Request(
                    base_item['url'],
                    meta={'base_item': base_item},
                    callback=self.parse_deal)

        # alternative to complete depth search:
            # - metadata contains information on pages & number of available items, but it doesnt seem usable
            # - sending request for another page after successfully parsing a json response will provide the
            # most complete data, at the cost of 1 extra page downloaded indicated that the last request failed

    def parse_deal(self, response):
        sel = Selector(response)
        item = response.meta['base_item']

        item['savings'] = (sel.xpath('//*[@id="discount-percent"]/text()').extract() or ['N/A']).pop().strip()
        item['large_image'] = (sel.xpath('//*[@id="featured-image"]/@src').extract() or [None]).pop()
        item['expires_at'] = ' '.join(sel.xpath('//*[contains(@class,"limited-time")]//text()').extract() or
                                      sel.xpath('//*[contains(@class,"countdown-timer")]//text()').extract() or
                                      ['Ongoing']).strip()

        address_node = (sel.xpath('//*[contains(@class,"address")]') or [None]).pop()
        if address_node:
            add_node_text = address_node.xpath('.//p//text()').extract()
            last_line = (add_node_text or [''])[-1]
            if re.match(r'^\D*(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$', last_line, re.M | re.I):
                item['phone'] = last_line
                item['merchant_address'] = '\n'.join(add_node_text[:-1]).strip()
            else:
                self.log("phone doesnt exist", log.INFO)  # from original print
                item['phone'] = ''
                # if phone is not available, address should be dropped ?!
                item['merchant_address'] = '\n'.join(add_node_text).strip()
        else:
            item['phone'] = ''
            item['merchant_address'] = ''

        yield item
