import scrapy


class EmploiticSpider(scrapy.Spider):
    name = "emploitic"
    allowed_domains = ["emploitic.comm"]
    start_urls = ["https://emploitic.comm"]

    def parse(self, response):
        pass
