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
    name = "detail"

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
            cursor.execute("SELECT id, title, link FROM courses WHERE 1 = 1")
            courses = cursor.fetchall()
            connection.close()

            self.logger.info(courses)

            for course in courses:

                yield scrapy.Request(
                    url=course[2],
                    callback=self.parse_detail,
                    cb_kwargs={"data": course},
                )
        else:
            self.logger.error("Login failed!")

    def parse_detail(self, response, data):
        post = response.css("div.p-body-main article:first-child")

        if post:
            detailItem = DetailItem()

            courseId = data[0]
            postId = post.css("::attr(data-content)").get().split("-")[1]
            
            imageUrl = post.css(".bbWrapper .bbImage::attr(data-url)").get()
            links = post.css(".bbWrapper .bbCodeBlock .bbCodeBlock-content .link.link--external")
            downloadLink = ""
            download_text_arr = ["СКАЧАТЬ", "ССЫЛКА"]

            for link in links:
                title = link.css("::text").get()
                contains_text = any(word in title for word in download_text_arr)

                if contains_text:
                    downloadLink = link.css("::attr(href)").get()
                    break

            desc = post.css(".bbWrapper::text").extract()

            description = ""
            for result in desc:
                result = result.replace("\n", "")
                result = result.replace("\t", "")
                if result != "":
                    description = description + result + "\n"

            detailItem = {
                "id": courseId,
                "postId": postId,
                "imageUrl": imageUrl,
                "description": description.strip(),
                "downloadLink": downloadLink,
            }

            self.logger.info(detailItem)

            yield detailItem
