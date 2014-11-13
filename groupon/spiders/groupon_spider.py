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

        for key, string in deals_info.iteritems():
            for idx, node in enumerate(Selector(text=string).xpath('//*/figure[contains(@class,"deal-card")]')):
                base_item = GrouponItem('cron_date')
                for field, xpath in {
                    'url': 'a/@href',
                    'small_image': 'a/img/@data-original',
                    'title': './/p[contains(@class,"deal-title")]/text()',
                    'merchant_name': './/p[contains(@class,"merchant-name")]/text()',
                }.iteritems():
                    base_item[field] = node.xpath(xpath).extract().pop()

                base_item['description'] = ','.join(node.xpath('.//div[contains(@class,"description")]//text()').extract()).strip()
                base_item['price'] = (node.xpath('.//div[contains(@class,"discount-price")]//text()').extract() or ["View price"]).pop()
                base_item['url'] = urljoin(response.url, base_item['url'])

                # self.log("loop%d in %s" % (idx, key), log.INFO)  # from original print
                yield Request(
                    base_item['url'],
                    meta={'base_item': base_item},
                    callback=self.parse_deal)

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
                # self.log("phone doesnt exist", log.INFO)  # from original print
                item['phone'] = ''
                # if phone is not available, address should be dropped ?!
                item['merchant_address'] = '\n'.join(add_node_text).strip()
        else:
            item['phone'] = ''
            item['merchant_address'] = ''

        yield item
