import scrapy
import json
# from scrapy.exceptions import CloseSpider
from errors.items import BestBuyItem
from logs.error_handler import ErrorManager

class BestBuy(scrapy.Spider):
    name = "bestBuy"
    
    base_url = "https://www.bestbuy.ca/api/v2/json/search?categoryid=20001&currentRegion=ON&include=facets%2C%20redirects&lang=en-CA&page={page}&pageSize=24&path=&query=&exp=labels%2Csearch_abtesting_personalization_epsilon%3Ab1&token=md5cjgb92piczdj&contextId=&isPLP=true&hasConsent=true&sortBy=relevance&sortDir=desc"
    max_pages = 10  # Adjust the number of pages you want to scrape


    def __init__(self, *args, **kwargs):
        super(BestBuy, self).__init__(*args, **kwargs)
        self.error_manager = ErrorManager()


    def start_requests(self):
        # First request with empty `page=` parameter
        # first_url = self.base_url.format(page="")
        # yield scrapy.Request(
        #     first_url,
        #     headers=self.settings.get("DEFAULT_REQUEST_HEADERS"),
        #     callback=self.parse,
        #     meta={'page': ""}  # Custom meta to track first page
        # )
        cat_id= [882185,20001]
        # Requests for pages 1 to max_pages
        for page in range(1, self.max_pages + 1):
            url = self.base_url.format(page=page)
            yield scrapy.Request(
                url,
                headers=self.settings.get("DEFAULT_REQUEST_HEADERS"),
                callback=self.parse,
            )

    def parse(self, response):
        # parsed_data = []
        try:
            data = response.json()
            current_page = data.get("currentPage")  # Retrieve the current page from meta

            for product in data.get("products", []):
                item = BestBuyItem()
                item["currentPage"]= current_page
                item["sku"]= product.get("sku"),
                item["name"]= product.get("name")
                item["customerRating"]= product.get("customerRating")
                item["customerRatingCount"]= product.get("customerRatingCount")
                item["customerReviewCount"]= product.get("customerReviewCount")
                item["productUrl"]= product.get("productUrl")
                item["regularPrice"]= product.get("regularPrice")
                item["salePrice"]= product.get("salePrice")
                item["thumbnailImage"]= product.get("thumbnailImage")
                item["categoryName"]= product.get("categoryName")
                yield item

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON response for page {current_page}")
            return

        # # Save JSON data to a file (append to existing file)
        # with open("data.json", "a", encoding="utf-8") as f:
        #     json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        #     f.write("\n")  # New line for each page’s data

        self.logger.info(f"Data for page {current_page} successfully saved to data.json")
  
