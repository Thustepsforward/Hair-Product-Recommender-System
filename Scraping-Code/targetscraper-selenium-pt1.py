# from seleniumwire import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
import time

driver = webdriver.Chrome()

driver.get('https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f')

# Target's Styling Products 
# Page 1 : https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f
# Page 8 : https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=168
# Page 10 : https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=216
# Page 22 : https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=504
# Page 27 : https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=624
# Page 31 : https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=720
# Page 45: https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=1056
# Page 50: https://www.target.com/c/hair-styling-products-care-beauty/-/N-5xu0f?moveTo=product-list-grid&Nao=1176

# Target's Shampoo & Conditioners  
# Page 1 : https://www.target.com/c/shampoo-conditioner-hair-care-beauty/-/N-5xu0g
# Page 3 : https://www.target.com/c/shampoo-conditioner-hair-care-beauty/-/N-5xu0g?Nao=48&moveTo=product-list-grid
# Page 50 : https://www.target.com/c/shampoo-conditioner-hair-care-beauty/-/N-5xu0g?Nao=1176&moveTo=product-list-grid

# Target's Treatments 
# Page 1 : https://www.target.com/c/hair-treatments-care-beauty/-/N-55kmm
# Page 35 : https://www.target.com/c/hair-treatments-care-beauty/-/N-55kmm?Nao=816&moveTo=product-list-grid


# Target's Texture Hair Care 
# Page 1 : https://www.target.com/c/textured-hair-care/-/N-4rsrf
# Page 31 : https://www.target.com/c/textured-hair-care/-/N-4rsrf?Nao=720&moveTo=product-list-grid
# Page 49 : https://www.target.com/c/textured-hair-care/-/N-4rsrf?Nao=1152&moveTo=product-list-grid
# Page 50: https://www.target.com/c/textured-hair-care/-/N-4rsrf?Nao=1176&moveTo=product-list-grid

# Initialize the page counter
page_number = 1

def find_element_with_retry(driver, by_method, selectors, retries=3, delay=5, default=None):
    last_exception = None
    for selector in selectors:  # Loop through the list of selectors
        for attempt in range(retries):
            try:
                element = driver.find_element(by_method, selector)
                return element
            except NoSuchElementException as e:
                last_exception = e
                time.sleep(delay)  # Wait before retrying
    if default is not None:
        return default  # Return a default value instead of raising an exception
        # If all retries fail for this selector, try the next selector
    raise last_exception  # If no selectors work after all retries, raise the last exception

def go_to_next_page(driver, products):
    try:
        # Find the 'Next' button using the selector for the button containing the SVG
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="next"]'))
        )
        
        # Click the 'Next' button
        next_button.click()
        
        # Wait for the staleness of the first product of the previous page
        WebDriverWait(driver, 10).until(
            EC.staleness_of(products[0])
        )

        # Then, fetch new products
        products = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="sc-f82024d1-0 rLjwS"]'))
        )
        
        print("Navigated to next page.")
        return products
        
    except TimeoutException:
        print("Timed out waiting for the next page to load.")
    except NoSuchElementException:
        print("Next button not found or not clickable. May be on the last page.")
    except Exception as e:
        print(f"An error occurred: {e}")

with open('Target_test.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Product Name', 'Brand', 'Price', 'Rating', 'Number of Ratings', 'Link'])
    products = None
    try:
        products = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="sc-f82024d1-0 rLjwS"]')))
        while products:
            
            # Scroll to load more items
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # Wait for items to load

            print("-----------Products from Page", page_number, "---------")
            
            products = driver.find_elements(By.CSS_SELECTOR, 'div[class="sc-f82024d1-0 rLjwS"]')
            
            for product in products:
                try:
                    product_name = find_element_with_retry(product, By.CSS_SELECTOR, ['a[data-test="product-title"]'], retries=3).text
                    product_brand = find_element_with_retry(product, By.CSS_SELECTOR, ['a[data-test="@web/ProductCard/ProductCardBrandAndRibbonMessage/brand"]'], retries=3).text
                    # Include both selectors for the price
                    product_price_element = find_element_with_retry(product, By.CSS_SELECTOR, ['span[data-test="current-price"] span', 'div[data-test="comparison-price"] span'], retries=3)
                    product_price = product_price_element.text if product_price_element != '0' else '0'
                    product_rating_element = find_element_with_retry(product, By.CSS_SELECTOR, ['span[data-test="ratings"] span'], retries=3, default='0')
                    product_rating = product_rating_element.text if product_rating_element != '0' else '0'
                    product_rating_number_element = find_element_with_retry(product, By.CSS_SELECTOR, ['[data-test="rating-count"]'], retries=3, default='0')
                    product_rating_number = product_rating_number_element.text if product_rating_number_element != '0' else '0'
                    product_link = find_element_with_retry(product, By.CSS_SELECTOR, ['a[data-test="product-title"]'], retries=3).get_attribute('href')

                    # Only write and print products with a rating not equal to '0'
                    if product_rating != '0':
                        writer.writerow([product_name, product_brand, product_price, product_rating, product_rating_number, product_link])
                        print("[", product_name, product_brand, product_price, product_rating, product_rating_number, product_link, "]")
                except NoSuchElementException as e:
                    print(f"Failed to retrieve complete information for a product: {e}")
            
            # Print completion of the current page
            print("Completed scraping page", page_number)
            

            # Attempt to go to the next page
            products = go_to_next_page(driver, products)
            if not products:
                print("No more pages to navigate. Ending scrape.")
                break
            page_number += 1  # Increment the page number after successfully clicking next

            
            # # Check if the 'Next' button is still clickable for the next loop
            # if not WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="next"]'))):
            #     print("No more pages to navigate. Ending scrape.")
            #     break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()


################### Code to Retrieve Product Info  ####################

# try: 
#     # Prepare to write to CSV
#     with open('scraped_data.csv', 'w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         # Write the headers of the CSV file
#         writer.writerow(['Product Name', 'Brand', 'Price', 'Rating', 'Number of Ratings', 'Link'])

#         while True:
            
#             # Wait up to 15 seconds for the elements to be visible
#             WebDriverWait(driver, 30).until(
#                 EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-test="product-title"]'))
#             )
            
#             products = driver.find_elements(By.CSS_SELECTOR, 'div[class="sc-f82024d1-0 rLjwS"]') # driver.find_elements(By.CLASS_NAME, 'sc-f82024d1-0.rLjwS')

#             data = []
#             for product in products:
#                 product_name = product.find_element(By.CSS_SELECTOR, 'a[data-test="product-title"]').text
#                 product_brand = product.find_element(By.CSS_SELECTOR, 'a[data-test="@web/ProductCard/ProductCardBrandAndRibbonMessage/brand"]').text
#                 product_price = product.find_element(By.CSS_SELECTOR, 'span[data-test="current-price"] span').text
#                 product_rating = product.find_element(By.CSS_SELECTOR, 'span[data-test="ratings"] span').text
#                 # product_rating = product.find_element(By.CSS_SELECTOR, '.sc-fd6a822c-0.ivBHhT').text
#                 product_rating_number = product.find_element(By.CSS_SELECTOR, '[data-test="rating-count"]').text
#                 # product_link = product.find_element(By.LINK_TEXT, f'{product_name}')
#                 # data.append({
#                 #     "product": product_name,
#                 #     "brand": product_brand,
#                 #     "price" : product_price,
#                 #     "rating": product_rating,
#                 #     "num_of_ratings" : product_rating_number,
#                 #     "link" : product_link
#                 # })
                
#                 print("[", product_name, product_brand, product_price, product_rating, product_rating_number, "]")

#                 # Write product details to the CSV file
#                 writer.writerow([product_name, product_brand, product_price, product_rating, product_rating_number, product_link])
#             # print(json.dumps(data, ensure_ascii=False))
# except Exception as e:
#     print(f"An error occurred: {e}")
# finally:
#     # time.sleep(30)
#     driver.quit()



#################### Another Code to Retrieve Products  ####################


# try:
#     # Prepare to write to CSV
#     with open('target_test.csv', 'w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         # Write the headers of the CSV file
#         writer.writerow(['Product Name', 'Brand', 'Price', 'Rating', 'Number of Ratings', 'Link'])

#         while True:
#             # Wait for product elements to be visible
#             WebDriverWait(driver, 15).until(
#                 EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test="product-title"]'))
#             )

#             # Collect data for each product on the page
#             products = driver.find_elements(By.CLASS_NAME, 'sc-f82024d1-0.rLjwS')
#             for product in products:
#                 product_name = product.find_element(By.CSS_SELECTOR, '[data-test="product-title"]').text
#                 product_brand = product.find_element(By.CSS_SELECTOR, '[data-test="@web/ProductCard/ProductCardBrandAndRibbonMessage/brand"]').text
#                 product_price = product.find_element(By.CSS_SELECTOR, 'span[data-test="current-price"] span').text
#                 product_rating = product.find_element(By.CSS_SELECTOR, '.sc-fd6a822c-0.ivBHhT').text
#                 product_rating_number = product.find_element(By.CSS_SELECTOR, '[data-test="rating-count"]').text
#                 product_link = product.find_element(By.CSS_SELECTOR, '[data-test="product-title"] a').get_attribute('href')
#                 # Write product details to the CSV file
#                 writer.writerow([product_name, product_brand, product_price, product_rating, product_rating_number, product_link])

#             # Attempt to find and click the 'Next page' button if it's not disabled
#             next_page_button = driver.find_element(By.CSS_SELECTOR, 'button[data-test="next"]')
#             if "disabled" in next_page_button.get_attribute("class"):
#                 break  # If the button is disabled, break the loop
#             else:
#                 next_page_button.click()
#                 WebDriverWait(driver, 15).until(
#                     EC.staleness_of(next_page_button)  # Wait until the old next page button is stale (i.e., new page has loaded)
#                 )

# finally:
#     driver.quit()

