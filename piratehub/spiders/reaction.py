import scrapy
from scrapy.http import FormRequest
import mysql.connector
from piratehub.items import DetailItem
import configparser
import json

# config
config = configparser.ConfigParser()
config.read("config.ini")

class DetailSpider(scrapy.Spider):
    name = "reaction"

    custom_settings = {
        "ITEM_PIPELINES": {
            "piratehub.pipelines.DetailPipeline": 300,
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

            connection = mysql.connector.connect(
                host=config["mysql"]["host"],
                user=config["mysql"]["user"],
                password=config["mysql"]["password"],
                database=config["mysql"]["database"],
            )
            cursor = connection.cursor()
            cursor.execute("SELECT id, title, link, postId FROM courses")
            courses = cursor.fetchall()
            connection.close()

            for course in courses:
                reaction_url = "https://s1.piratehub.biz/posts/" + str(course[3]) + "/react?reaction_id=1"
                self.logger.info(reaction_url)
                yield scrapy.Request(
                    url=reaction_url,
                    callback=self.parse_reaction,
                )
        else:
            self.logger.error("Login failed!")

    def parse_reaction(self, response):
        csrf_token = response.xpath('//*[@name="_xfToken"]/@value').extract_first()
        self.logger.info(csrf_token)

        form = response.css("div.p-body-main form.block")
        if form:
            url = form.css("::attr(action)").get()
            self.logger.info(url)
            return FormRequest.from_response(
                response,
                formnumber=2,
                formdata={
                    "_xfToken": csrf_token,
                },
                method="POST",
                callback=self.after_reaction,
            )

    def after_reaction(self, response):
        self.logger.info("Success!")