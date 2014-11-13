# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item
from scrapy import Field


class GrouponItem(Item):
    url = Field()
    small_image = Field()
    title = Field()
    merchant_name = Field()
    description = Field()
    price = Field()
