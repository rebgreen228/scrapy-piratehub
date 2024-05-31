import scrapy
from scrapy.http import FormRequest
import mysql.connector
from piratehub.items import CourseItem
import configparser

# config
config = configparser.ConfigParser()
config.read("config.ini")


class CourseSpider(scrapy.Spider):
    name = "course"

    custom_settings = {
        "ITEM_PIPELINES": {
            "piratehub.pipelines.CoursePipeline": 200,
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
            cursor.execute("SELECT id, title, link FROM categories")
            categories = cursor.fetchall()
            connection.close()

            for category in categories:
                yield scrapy.Request(
                    url=category[2],
                    callback=self.parse_courses,
                    cb_kwargs={"data": category},
                )
        else:
            self.logger.error("Login failed!")

    def parse_courses(self, response, data):
        courseItem = CourseItem()
        threadContent = response.css(
            'div.p-body-main .p-body-content div.p-body-pageContent div.block[data-type="thread"]'
        )
        threadItems = threadContent.css(
            "div.block-container div.block-body div.structItemContainer div.structItem.structItem--thread"
        )

        for item in threadItems:
            categoryId = data[0]
            title = item.css(
                "div.structItem-cell.structItem-cell--main div.structItem-title a:last-child::text"
            ).get()
            link = (
                "https://s1.piratehub.biz"
                + item.css(
                    "div.structItem-cell.structItem-cell--main .structItem-title a:last-child::attr(href)"
                ).get()
            )

            rating = item.css(
                "div.structItem-cell.structItem-cell--main .structItem-minor .structItem-threadRating .t-rating::attr(data-rate)"
            ).get()
            startTime = item.css(
                "div.structItem-cell.structItem-cell--main .structItem-minor .structItem-parts .structItem-startDate .u-dt::attr(data-time)"
            ).get()
            views = item.css(
                "div.structItem-cell.structItem-cell--meta .structItem-minor dd::text"
            ).get()

            courseItem = {
                "categoryId": categoryId,
                "title": title,
                "link": link,
                "rating": rating,
                "startTime": startTime,
                "views": views,
            }

            yield courseItem

        next_page = response.css(
            "div.block-outer div.block-outer-main .pageNavWrapper .pageNav a.pageNav-jump--next::attr(href)"
        ).get()
        if next_page:
            yield response.follow(
                next_page, callback=self.parse_courses, cb_kwargs={"data": data}
            )
        else:
            return
