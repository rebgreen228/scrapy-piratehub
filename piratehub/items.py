# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class CategoryItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()

class CourseItem(scrapy.Item):
    categoryId = scrapy.Field()
    title = scrapy.Field()
    link = scrapy.Field()
    rating = scrapy.Field()
    startTime = scrapy.Field()
    views = scrapy.Field()

class DetailItem(scrapy.Item):
    id = scrapy.Field()
    postId = scrapy.Field()
    imageUrl = scrapy.Field()
    description = scrapy.Field()
    downloadLink = scrapy.Field()
