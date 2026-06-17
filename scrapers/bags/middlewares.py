from scrapy import signals

# intercept and modify requests, responses, or spider behavior, Filtering results, Logging
class BagsSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        # When the spider opens, call my spider_opened() method.
        return s
    

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s", spider.name)
