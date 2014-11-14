# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item
from scrapy import Field


class GrouponItem(Item):
    # init
    provider_name = Field()
    insert_date = Field()
    category_name = Field()
    merchant_locality = Field()
    # first pass
    url = Field()
    small_image = Field()
    title = Field()
    merchant_name = Field()
    description = Field()
    price = Field()
    # second pass
    large_image = Field()
    savings = Field()
    merchant_address = Field()
    expires_at = Field()
    phone = Field()
    def __repr__(self):
        return '{Groupon %s: %s [%s] "%s"}' % (self['merchant_locality'], self['price'], self['merchant_name'], self['title'])
