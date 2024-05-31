import scrapy
from scrapy.http import FormRequest
from piratehub.items import CategoryItem
import configparser

# config
config = configparser.ConfigParser()
config.read("config.ini")

class CategorySpider(scrapy.Spider):
    name = "category"

    custom_settings = {
        'ITEM_PIPELINES': {
            'piratehub.pipelines.CategoryPipeline': 100,
        }
    }

    allowed_domains = ["s1.piratehub.biz"]
    start_urls = ["https://s1.piratehub.biz/login/login"]

    def parse(self, response):
        csrf_token = response.xpath('//*[@name="_xfToken"]/@value').extract_first()
        redirect_url = response.xpath('//*[@name="_xfRedirect"]/@value').extract_first()
        return FormRequest.from_response(
            response,
            formnumber=2,
            formdata={
                "_xfToken": csrf_token,
                "login": config["piratehub"]["username"],
                "password": config["piratehub"]["password"],
                "remember": "1",
                "_xfRedirect": redirect_url,
            },
            method="POST",
            callback=self.after_login,
        )

    def after_login(self, response):
        if 'data-logged-in="true"' in response.text:
            self.logger.info("Login successful!")
            return self.parse_categories(response)
        else:
            self.logger.error("Login failed!")

    def parse_categories(self, response):
        categoryItem = CategoryItem()

        infoCategories = response.css("div.block--category30 div.block-container div.block-body div.node.node--forum")
        for category in infoCategories:
            title = category.css("h3.node-title a::text").get()
            if title not in ["Разное", "Раздачи от пользователей", "Запросы на поиск материалов"]:
                categoryItem["title"] = category.css("h3.node-title a::text").get()

                categoryItem["link"] = "https://s1.piratehub.biz" + category.css("h3.node-title a::attr(href)").get()
                yield categoryItem

        affiliateCategories = response.css("div.block--category203 div.block-container div.block-body div.node.node--forum")
        for category in affiliateCategories:
            categoryItem["title"] = category.css("h3.node-title a::text").get()
            categoryItem["link"] = "https://s1.piratehub.biz" + category.css("h3.node-title a::attr(href)").get()
            yield categoryItem