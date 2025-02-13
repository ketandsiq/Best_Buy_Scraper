import scrapy
import os
from scrapy.exceptions import CloseSpider
from errors.items import organicItem,sponsorItem
from urllib.parse import urlencode
 
from logs.error_handler import ErrorManager 

API_KEY = os.getenv("SCRAPER_API_KEY")

def get_scraperapi_url(url):
    payload = {'api_key': API_KEY, 'url': url, 'render': 'true'}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url   
# from proxy_manager import perform_proxy_operation
class ErrorSpider(scrapy.Spider):
    name = "error"

    def __init__(self, *args, **kwargs):
        super(ErrorSpider, self).__init__(*args, **kwargs)
        self.error_manager = ErrorManager()
        # perform_proxy_operation()

    def start_requests(self):
    # Check if the spider has been passed a 'urls' parameter.
    # If so, assume it's a comma-separated string of URLs.
        if hasattr(self, 'urls') and self.urls:
            urls = self.urls.split(',')
        else:
            # Fallback to a default list (currently empty or any hardcoded values)
            urls = [
                'https://www.bestbuy.com/site/tvs/97-inch-or-larger-tvs/pcmcat1729520550075.c?id=pcmcat1729520550075'
            ]
        
        for url in urls:
            proxy_url = get_scraperapi_url(url)
            yield scrapy.Request(
                url=proxy_url,
                callback=self.parse,                
                errback=lambda failure: self.error_manager.handle_request_failure(failure, self.name)
            )


    def parse(self, response):
        """Parses the response and extracts product details."""
        self.logger.info('IP address: %s' % response.text)
        if not self.error_manager.check_response_status(response, self.name):
            raise CloseSpider(f"{response.status} Response")
        
        try:
            self.logger.info(f"Crawling: {response.url}")
            items_found = False 
            print(response)
            for sel in response.css(".list-item.lv, .shop-sku-list-item"):
                organicItemData = organicItem()
                # isSponsored = sel.css(".list-item.template-grid.null>.is-sponsored").get()
                # print("isSponsored: ",isSponsored)
                name = sel.css(".column-middle>.sku-title>a::text, .list-item.template-grid.null>.sku-title>a::text").get()
                # print("Name: ",name)
                price = sel.css(".priceView-hero-price.priceView-customer-price>span::text, .priceView-hero-price.priceView-customer-price>.sr-only::text").get()
                # print("price: ",price)
                # compPrice = sel.css(".pricing-price__regular-price-content>.pricing-price__regular-price.sr-only::text").get()
                # print("compPrice: ",compPrice)
                stars = sel.css(".c-ratings-reviews>.visually-hidden::text").get()
                # print("stars: ",stars)
                Sku = sel.css(".sku-attribute-title+.sku-attribute-title>.sku-value::text, .sku-attribute-title>.sku-value::text").get()
                # print("Sku: ",Sku)
                productPageLink = sel.css(".column-middle>.sku-title>a::attr(href), .list-item.template-grid.null>.sku-title>a::attr(href)").get()
                # print("productPageLink: ",productPageLink)
                heroImgURL = sel.css(".column-left>a::attr(href), .list-item.template-grid.null>a>.product-image::attr(src)").get()
                # print("heroImgURL: ",heroImgURL)
                if not name or not price or not stars or not productPageLink or not Sku or not heroImgURL:
                    self.error_manager.log_missing_required_data(response, self.name)
                    continue  
                # if isSponsored is None: isSponsored = False
                # organicItemData['isSponsored'] = isSponsored
                organicItemData['name'] = name
                organicItemData['price'] = price
                # organicItemData['compPrice'] = compPrice
                organicItemData['stars'] = stars
                organicItemData['SKU'] = Sku
                organicItemData['productPageLink'] = productPageLink
                organicItemData['heroImgURL'] = heroImgURL
                items_found = True
                yield organicItemData
            
            # for sel in response.css(".pl-flex-carousel-container.v-no-overlay.-arrows>.pl-flex-carousel>div>.pl-flex-carousel-slider>.c-carousel-list>.item.c-carousel-item>.product-flexbox>.list-item.wrapper"):
            #     sponsorItemData = sponsorItem()
            #     # is_sponsor = bool(sponsorItemData)
            #     name = sel.css(".list-item.wrapper>.info-section>.sku-title>.nc-product-title::text").get()
            #     print("Name: ",name)
            #     price = sel.css(".price-block>div>._none").get()
            #     print("price: ",price)
            #     # compPrice = sel.css(".priceView-hero-price.priceView-previous-price>span::text").get()
            #     # print("compPrice: ",compPrice)
            #     stars = sel.css(".list-item.wrapper>.info-section>.nc-rating-review-wrapper>a>.visually-hidden::text").get()
            #     print("stars: ",stars)
            #     productPageLink = sel.css(".list-item.wrapper>.info-section>.sku-title::attr(href)").get()
            #     print("productPageLink: ",productPageLink)
            #     heroImgURL = sel.css(".list-item.wrapper>.image-section>.product-image::attr(src)").get()
            #     print("heroImgURL: ",heroImgURL)
            #     if not name or not stars or not price or not productPageLink or not heroImgURL:
            #         self.error_manager.log_missing_required_data(response, self.name)
            #         continue  
            #     # sponsorItemData['is_sponsor'] = is_sponsor
            #     sponsorItemData['name'] = name
            #     sponsorItemData['price'] = price
            #     # sponsorItemData['compPrice'] = compPrice
            #     sponsorItemData['stars'] = stars  
            #     sponsorItemData['productPageLink'] = productPageLink
            #     sponsorItemData['heroImgURL'] = heroImgURL
            #     items_found = True
            #     yield sponsorItemData

            if not items_found:
                self.error_manager.log_no_items_found(response, self.name)
        except Exception as e:
            self.error_manager.log_parsing_error(
                response,
                {str(e)},
                self.name
            )


        next_page = response.css(".footer-pagination>.sku-list-page-next::attr(href)").get()
        if next_page:
            try:
                url = "https://www.bestbuy.com"+next_page
                next_page_url = get_scraperapi_url(url)
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse,
                    errback=lambda failure: self.error_manager.handle_request_failure(failure, self.name),
                    meta={'pagination': True}  # Mark this as a pagination request
                )
            except Exception as e:
                self.error_manager.log_pagination_error(response,self.name)
        else:
            is_last_page = response.css(".s-pagination-next[aria-disabled='true']")
            if not is_last_page:
                self.error_manager.log_pagination_error_1(response,self.name)
