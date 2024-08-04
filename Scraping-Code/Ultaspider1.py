import scrapy
import pandas as pd
import time
from scrapy.exceptions import CloseSpider
from scrapy.http import Request
from scrapy.spidermiddlewares.httperror import HttpError

class UltaHairSpider(scrapy.Spider):
    name = "UltaProducts"
    custom_settings = {
        'DOWNLOAD_DELAY': 1,  # Delay between individual requests within a batch
        'CONCURRENT_REQUESTS': 1,  # Only make one request at a time
        'RETRY_TIMES': 3,  # Maximum number of times to retry
        'RETRY_HTTP_CODES': [400, 403, 404, 500, 502, 503, 504]  # Which codes to retry
    }
     
    def start_requests(self):
        print("Executing Ultascraper2Spider")
        # Load your dataset containing links and product IDs
        dataset = pd.read_csv('/Users/thumato/Desktop/Final_Capstone_Project/Cleaned Datasets/Ulta_products_links_only.csv')  
        for index, row in dataset.iterrows():
            # yield scrapy.Request(url=row['Link'], callback=self.parse_ingredients, meta={'product_id': row['Product ID']})   
            yield Request(
                url=row['Link'],
                callback=self.parse_ingredients,
                meta={'product_id': row['Product ID'], 'retry_count': 0},
                errback=self.handle_error
            )

    def __init__(self, *args, **kwargs):
        super(UltaHairSpider, self).__init__(*args, **kwargs)
        self.dataset = pd.read_csv('/Users/thumato/Desktop/Final_Capstone_Project/Cleaned Datasets/Ulta_products_links_only.csv')
        self.start_id = 'U656'  # Set starting Product ID here
        self.batch_size = 29  # Number of requests to process at a time

    def start_requests(self):
        # Find the index of the start ID in the dataset
        start_index = self.dataset[self.dataset['Product ID'] == self.start_id].index[0]
        
        # Process links starting from the index of the start ID
        for index, row in self.dataset.iloc[start_index:].iterrows():
            yield scrapy.Request(
                url=row['Link'],
                callback=self.parse_ingredients,
                meta={'product_id': row['Product ID']},
                errback=self.handle_error  # Add error handling
            )
            if (index - start_index + 1) % self.batch_size == 0:
                time.sleep(60)  # Sleep after processing each batch
                break  # Stop after a batch, need to manually restart or use a scheduler

    # def handle_error(self, failure):
    #     self.logger.error(repr(failure))

    def handle_error(self, failure):
        if failure.check(HttpError):
            response = failure.value.response
            if response.status in [400, 404]:  # You can specify any particular status codes you care about
                retry_count = failure.request.meta['retry_count']
                if retry_count < self.custom_settings['RETRY_TIMES']:
                    retry_count += 1
                    self.logger.error(f"Retrying URL: {response.url} (Retry {retry_count}/{self.custom_settings['RETRY_TIMES']}) due to error {response.status}")
                    retry_req = failure.request.copy()
                    retry_req.meta['retry_count'] = retry_count
                    yield retry_req
                else:
                    self.logger.error(f"Giving up for URL: {response.url} after {retry_count} retries")



    # def parse_description(self, response):
        
    #     product_img_link = response.css('div.ProductHero__MediaGallery div.Image img').attrib['src']
    #     product_description = response.css('div.ProductSummary p.Text-ds.Text-ds--subtitle-1.Text-ds--left.Text-ds--black::text').get()
    #     product_health_facts = response.css('div.SummaryCard span.Text-ds.Text-ds--body-2.Text-ds--left.Text-ds--black::text').getall()
    #     # Joining the extracted text items with ", "
    #     product_health_facts = ', '.join([fact.strip() for fact in product_health_facts])
    #     product_highlights = response.css('h4:contains("Benefits") + ul li::text').getall()
    #     product_highlights = ', '.join([highlight.strip() for highlight in product_highlights])
        
    #     # Yield the result including the product ID from response meta
    #     yield {
    #         'Product ID': response.meta['product_id'],
    #         'Image Link': product_img_link,
    #         'Description': product_description,
    #         'Health Facts': product_health_facts,
    #         'Highlights': product_highlights
    #     }

    def parse_ingredients(self, response):
        
        product_ingredients = response.css('summary#Ingredients + .Accordion_Huge__content .Markdown p::text').get()
        
        # Yield the result including the product ID from response meta
        yield {
            'Product ID': response.meta['product_id'],
            'Ingredients': product_ingredients,
        }
       
    # def parse_reviews(self, response):
        
    #     for review in response.css('div.pr-review')
        
    #     review_title = response.css('summary#Ingredients + .Accordion_Huge__content .Markdown p::text').get()
        
    #     # Yield the result including the product ID from response meta
    #     yield {
    #         'Product ID': response.meta['product_id'],
    #         'Ingredients': product_ingredients,
    #     }