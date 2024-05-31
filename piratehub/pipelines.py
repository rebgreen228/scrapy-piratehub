# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import mysql.connector
import configparser

# config
config = configparser.ConfigParser()
config.read('config.ini')

class CategoryPipeline:
    def open_spider(self, spider):
        self.connection = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            database=config['mysql']['database']
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        self.connection.commit()
        self.connection.close()

    def process_item(self, item, spider):
        sql = "SELECT * FROM categories WHERE title = %s"
        self.cursor.execute(sql, (item['title'],))
        result = self.cursor.fetchone()

        if result:
            existing_link = result[2]
            if existing_link != item['link']:
                sql_update = "UPDATE categories SET link = %s WHERE title = %s"
                values = (item['link'], item['title'])
                self.cursor.execute(sql_update, values)
            
        else:
            sql_insert = "INSERT INTO categories (title, link) VALUES (%s, %s)"
            values = (item['title'], item['link'])
            self.cursor.execute(sql_insert, values)

        return item
    
class CoursePipeline:
    def open_spider(self, spider):
        self.connection = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            database=config['mysql']['database']
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        self.connection.commit()
        self.connection.close()

    def process_item(self, item, spider):
        sql = "SELECT * FROM courses WHERE title = %s"
        self.cursor.execute(sql, (item['title'],))
        result = self.cursor.fetchone()

        if result:
            sql_update = "UPDATE courses SET categoryId = %s, link = %s, rating = %s, startTime = %s, views = %s  WHERE title = %s"
            values = (item['categoryId'], item['link'], item['rating'], item['startTime'], item['views'], item['title'])
            self.cursor.execute(sql_update, values)
            
        else:
            sql_insert = "INSERT INTO courses (categoryId, title, link, rating, startTime, views) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (item['categoryId'], item['title'], item['link'], item['rating'], item['startTime'], item['views'])
            self.cursor.execute(sql_insert, values)

        return item
    
class DetailPipeline:
    def open_spider(self, spider):
        self.connection = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            database=config['mysql']['database']
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        self.connection.commit()
        self.connection.close()

    def process_item(self, item, spider):
        sql = "SELECT * FROM courses WHERE id = %s"
        self.cursor.execute(sql, (item['id'],))
        result = self.cursor.fetchone()

        if result:
            sql_update = "UPDATE courses SET postId = %s, imageUrl = %s, description = %s, downloadLink = %s WHERE id = %s"
            values = (item['postId'], item['imageUrl'], item['description'], item['downloadLink'], item['id'])
            self.cursor.execute(sql_update, values)            
        else:
            spider.logger.warn("Item doesnt exists in database")

        return item