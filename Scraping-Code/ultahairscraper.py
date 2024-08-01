import scrapy

class UltaHairSpider(scrapy.Spider):
    name = 'hair'
    start_urls = ['https://www.ulta.com/shop/hair/treatment']
    # Ulta's Styling Products : https://www.ulta.com/shop/hair/styling-products
    # Ulta's Shampoo & Conditioners : https://www.ulta.com/shop/hair/shampoo-conditioner
    # Ulta's Treatments : https://www.ulta.com/shop/hair/treatment
      
    def parse(self, response):
        
        for products in response.css('div.ProductCard'):
            
            regular_price = products.css('div.ProductPricing span.Text-ds.Text-ds--body-2.Text-ds--left.Text-ds--black::text').get()
            original_price = products.css('div.ProductPricing span.Text-ds.Text-ds--body-2.Text-ds--left.Text-ds--neutral-600.Text-ds--line-through::text').get()
            
            rating_text = products.css('div.ReviewStarsCard span.sr-only::text').get()
            if rating_text:
                rating = rating_text.split(';')[0].replace(' out of 5 stars', '').strip()
            else:
                rating = "No rating"
     
            num_of_ratings_text = products.css('div.ReviewStarsCard span.Text-ds.Text-ds--body-3.Text-ds--left.Text-ds--neutral-600::text').get()
            if num_of_ratings_text:
                num_of_ratings = num_of_ratings_text.replace('(', '').replace(')', '').replace(',', '')
            else:
                num_of_ratings = "No ratings"
       
            yield {
                'brand' : products.css('span.ProductCard__brand span.Text-ds.Text-ds--body-2.Text-ds--left.Text-ds--neutral-600::text').get(),
                'product' : products.css('span.ProductCard__product span.Text-ds.Text-ds--body-2.Text-ds--left::text').get(),
                # If sale item, get original price. If a regularly-priced item, get regular price.
                'price' : regular_price if regular_price else original_price,
                'rating' : rating,
                'num_of_ratings' : num_of_ratings,
                'link': products.css('a.Link_Huge.Link_Huge--secondary').attrib['href'],
            }
            
        next_page = response.css('div.ProductListingWrapper__LoadContent[data-test="load-more-wrapper"] a::attr(href)').get()
        if next_page is not None: 
            yield response.follow(next_page, callback = self.parse)