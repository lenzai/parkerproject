# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item
from scrapy import Field


class GrouponBaseItem(Item):
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


class GrouponItem(GrouponBaseItem):
    def __init__(self, date, category, city, *a, **kwargs):
        super(GrouponItem, self).__init__(*a, **kwargs)
        self['provider_name'] = 'Groupon'
        self['insert_date'] = date
        self['category_name'] = category
        self['merchant_locality'] = city
