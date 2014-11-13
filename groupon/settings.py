# -*- coding: utf-8 -*-

# Scrapy settings for groupon project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'groupon'

SPIDER_MODULES = ['groupon.spiders']
NEWSPIDER_MODULE = 'groupon.spiders'

CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2
DOWNLOAD_DELAY = 10
DOWNLOAD_TIMEOUT = 60

HTTPCACHE_ENABLED = True
# for debugging - no need to parse too many items
HTTPCACHE_IGNORE_MISSING = True

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'groupon (+http://www.yourdomain.com)'
