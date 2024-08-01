from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import pandas as pd
import os

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

def find_elements_with_retry(driver, by_method, selectors, retries=3, delay=5):
    last_exception = None
    for selector in selectors:  # Loop through the list of selectors
        for attempt in range(retries):
            try:
                elements = driver.find_elements(by_method, selector)
                if elements:  # Check if any elements were found
                    return elements
                time.sleep(delay)  # Wait before retrying if no elements were found
            except NoSuchElementException as e:
                last_exception = e
                time.sleep(delay)  # Wait before retrying
    return []  # Return an empty list if all retries fail

def setup_dataframe():
    # Dataframe for CSV containing product details
    columns_details = ['Product ID', 'Picture URL', 'Description', 'Health Facts', 'Benefits', 'Features']
    df_details = pd.DataFrame(columns=columns_details)
    
    # Dataframe for CSV containing ingredients
    columns_ingredients = ['Product ID', 'Product Ingredients']
    df_ingredients = pd.DataFrame(columns=columns_ingredients)
    return df_details, df_ingredients

def append_to_csv(df, filename):
    if not os.path.exists(filename):
        df.to_csv(filename, index=False, mode='w')
    else:
        df.to_csv(filename, index=False, mode='a', header=False)

# Initialize DataFrame
details_df, ingredients_df = setup_dataframe()

def page_not_found(driver):
    """Check if the 'Page Not Found' title is present on the page."""
    try:
        driver.find_element(By.CSS_SELECTOR, 'div.TextOnlyHero div.TextOnlyHero__headline h1.Text-ds.Text-ds--title-2.Text-ds--center.Text-ds--black')
        return True
    except NoSuchElementException:
        return False

def scroll_to_load_content(driver, timeout=30):
    """ Scroll through the page incrementally to ensure all dynamic content loads. """
    scroll_pause_time = 1  # You can adjust this based on how quickly the site loads
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Additional wait to ensure all data has loaded
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

driver = webdriver.Chrome()

# # Parameters for batch processing
# start_product_id = 'U19'  # Adjust as needed 
# batch_size = 60  # Adjust as needed

# Uncomment for processing specific products
product_ids_to_filter = ['U178', 'U172', 'U141', 'U394', 'U236', 'U150', 'U290', 'U77', 'U220', 'U379', 'U631', 'U548', 'U383', 'U51', 'U463', 'U166', 'U179', 'U392', 'U176', 'U504', 'U564', 'U180', 'U507', 'U337', 'U163', 'U539', 'U157', 'U116', 'U335', 'U375', 'U226', 'U93', 'U616', 'U118', 'U186', 'U676', 'U384', 'U30', 'U169', 'U395', 'U230', 'U393', 'U363', 'U655', 'U398', 'U482', 'U223', 'U389', 'U681', 'U660', 'U373', 'U342', 'U390', 'U680', 'U367', 'U360', 'U161', 'U619', 'U345', 'U317', 'U657', 'U448', 'U369', 'U194']


# Setup for collecting skipped product IDs
skipped_products = []
# List to track IDs with reviews less than 100
products_less_than_100rev = []
# List to track IDs with reviews less than 4.5
products_less_criteria_rating = []

# Load the list of products
products_df = pd.read_csv('/Users/thumato/Desktop/Final_Capstone_Project/Cleaned Datasets/Ulta_products_links_only.csv')
# products_df = pd.read_csv('/Users/thumato/Desktop/Capstone Project - Selenium/Ulta_ingredients_extra.csv')
# products_df = pd.read_csv('/Users/thumato/Desktop/Capstone Project - Selenium/Ulta_product_description_extra.csv')
# Path for scraping leftover product descriptions: '/Users/thumato/Desktop/Capstone Project - Selenium/Ulta_product_description_extra.csv'

#################################### Start of Code to Scrape Product Description & Ingredients ####################################
###### Uncomment section if want to retrieve Product Description & Ingredients

# Determine the starting index
try:
    # Uncomment for batch processing
    # start_index = products_df.index[products_df['Product ID'] == start_product_id][0]
    # products_df = products_df.iloc[start_index:start_index + batch_size]
    
    # Uncomment for processing specific products
    products_df = products_df[products_df['Product ID'].isin(product_ids_to_filter)]
except IndexError:
    print("Starting Product ID not found in the DataFrame.")
    driver.quit()
    exit()

# Loop through each product
for index, row in products_df.iterrows():
    product_id = row['Product ID']
    product_link = row['Link']
    
    driver.get(product_link)
    # scroll_to_load_content(driver)
    
    if page_not_found(driver):
        print(f"Page not found for product ID: {product_id}")
        skipped_products.append(product_id)
        continue  # Skip to the next iteration of the loop
    
    # Initialize the page counter
    page_number = 1
    reviews = None
    try:
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="pr-review"]'))
        )

        # # Get Total # of Written Reviews Listed on Page
        # reviews_text = find_element_with_retry(driver, By.CSS_SELECTOR, ["header.pr-rd-main-header h4.pr-rd-review-total.pr-h1"], retries=3).text
        # ### print(f"Total Reviews Found on Page (Full) {reviews_text}")
        # total_reviews_on_page = int(reviews_text.split()[0])
        # ### print(f"Total Reviews Found on Page {total_reviews_on_page}")
        
        # # Get Product Rating
        # reviews_rating_listed = find_element_with_retry(driver, By.CSS_SELECTOR, ["div.pr-snippet-stars-container div.pr-snippet-stars.pr-snippet-stars-png div.pr-snippet-rating-decimal"], retries=3).text
        # review_rating_float = float(reviews_rating_listed)        
        
        # if total_reviews_on_page < 100 and review_rating_float < 4.5:
        #     print(f"Product {product_id} has less than 100 reviews and less than 4.5 rating. It is being skipped")
        #     products_less_than_100rev.append(product_id)
        #     products_less_criteria_rating.append(product_id)
        #     continue
        # elif total_reviews_on_page < 100:
        #     print(f"Product {product_id} has less than 100 reviews. It is being skipped")
        #     products_less_than_100rev.append(product_id)
        #     continue    # Move to the next product immediately
        # elif review_rating_float < 4.5:
        #     print(f"Product {product_id} has less than 4.5 rating. It is being skipped")
        #     products_less_criteria_rating.append(product_id)
        #     continue 
        
         ############# Retrieving Info for CSV containing Product Details BELOW #############
         
        # product_img_link = find_element_with_retry(driver, By.CSS_SELECTOR, ['div.ProductHero__MediaGallery div.Image img'], retries=3).get_attribute('src')
        # # print("Link:", product_img_link)
        
        # product_description = find_element_with_retry(driver, By.CSS_SELECTOR, ['div.ProductSummary p.Text-ds.Text-ds--subtitle-1.Text-ds--left.Text-ds--black'], retries=3).text
        # # print("Description:", product_description)
        
        # # Wait for the Details summary to be clickable
        # WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.CSS_SELECTOR, "details.Accordion_Huge[aria-controls='Details'] > summary[id='Details']"))
        # )

        # # Scroll the summary into view
        # details_summary = driver.find_element(By.CSS_SELECTOR, "details.Accordion_Huge[aria-controls='Details'] > summary[id='Details']")
        # driver.execute_script("arguments[0].scrollIntoView(true);", details_summary)
        # time.sleep(1)  # Allow time for any floating elements to move away

        # # Try clicking the summary using JavaScript
        # driver.execute_script("arguments[0].click();", details_summary)

        # # Wait for the content under the Details to become visible
        # WebDriverWait(driver, 10).until(
        #     EC.visibility_of_element_located((By.CSS_SELECTOR, "details.Accordion_Huge[aria-controls='Details'] > div.Accordion_Huge__content"))
        # )
        
        # product_health_facts_elements = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div.SummaryCard span.Text-ds.Text-ds--body-2.Text-ds--left.Text-ds--black'], retries=3)
        # if product_health_facts_elements:
        #     product_health_facts = ', '.join([fact.text.strip() for fact in product_health_facts_elements])
        # else:
        #     product_health_facts = ''
        # # print("Health Facts:", product_health_facts)

        # # Find all highlights under the 'Benefits' section
        #     # Find all h4 elements within the div with data-test='markdown'
        # headers = driver.find_elements(By.CSS_SELECTOR, "div[data-test='markdown'] h4")
        # product_benefits = ""
        # product_features = ""

        # # Loop through each header and find the sibling ul elements
        # for header in headers:
        #     category = header.text.strip()
        #     if "Benefits" in category:
        #         # Retrieve all li elements from the next ul sibling
        #         benefit_items = header.find_element(By.XPATH, "./following-sibling::ul").find_elements(By.TAG_NAME, "li")
        #         product_benefits = ', '.join([item.text.strip() for item in benefit_items])
        #     elif "Features" in category:
        #         # Retrieve all li elements from the next ul sibling
        #         feature_items = header.find_element(By.XPATH, "./following-sibling::ul").find_elements(By.TAG_NAME, "li")
        #         product_features = ', '.join([item.text.strip() for item in feature_items])

        # # Output the results
        # # print("Product Benefits:", product_benefits)
        # # print("Product Features:", product_features)
        
        # product_highlights = product_benefits + ' ' + product_features
        # # print("Highlights:", product_highlights)

        # # Append to review dataframe
        # new_data_details = pd.DataFrame({
        #     'Product ID': [product_id],
        #     'Picture URL': [product_img_link],
        #     'Description': [product_description],
        #     'Health Facts': [product_health_facts],
        #     'Benefits' : [product_benefits],
        #     'Features' : [product_features]
        # })
        
        # details_df = pd.concat([details_df, new_data_details], ignore_index=True)

        ############ Retrieving Info for CSV containing Product Details ABOVE #############
        
        ############ Retrieving Info for CSV containing Product Ingredients BELOW #############
        # Wait for the Ingredients summary to be clickable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "details.Accordion_Huge[aria-controls='Ingredients'] > summary[id='Ingredients']"))
        )

        # Scroll the summary into view
        ingredients_summary = driver.find_element(By.CSS_SELECTOR, "details.Accordion_Huge[aria-controls='Ingredients'] > summary[id='Ingredients']")
        driver.execute_script("arguments[0].scrollIntoView(true);", ingredients_summary)
        time.sleep(1)  # Allow time for any floating elements to move away

        # Try clicking the summary using JavaScript
        driver.execute_script("arguments[0].click();", ingredients_summary)

        # Wait for the content under the Details to become visible
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "details.Accordion_Huge[aria-controls='Ingredients'] > div.Accordion_Huge__content"))
        )
        
        product_ingredients = find_element_with_retry(driver, By.CSS_SELECTOR, ["details.Accordion_Huge[aria-controls='Ingredients'] div.Accordion_Huge__content div.Markdown.Markdown--body-2.Markdown--left p"], retries=3).text
        print("Ingredients:", product_ingredients)
        
        # Append to review dataframe
        new_data_ingredients = pd.DataFrame({
            'Product ID': [product_id],
            'Product Ingredients': [product_ingredients]
        })
        ingredients_df = pd.concat([ingredients_df, new_data_ingredients], ignore_index=True)

        ############# Retrieving Info for CSV containing Product Ingredients ABOVE #############
            
    except TimeoutException as e:
        print(f"Timeout Error for product {product_id}: {e}")
    except NoSuchElementException as e:
        print(f"Element not found for product {product_id}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for product {product_id}: {e}")
        continue  # Optionally skip to next product instead of stopping

# append_to_csv(details_df, 'Ulta_product_description.csv')
# append_to_csv(details_df, 'Ulta_additional_product_description.csv')
# append_to_csv(ingredients_df, 'Ulta_ingredients.csv')
append_to_csv(ingredients_df, 'Ulta_additional_ingredients.csv')
driver.quit()   

#################################### End of Code to Scrape Product Description & Ingredients ####################################

#################################### Start of Code to Get List of Skipped Products + Products with less than 100 reviews and 4.5 rating ####################################
##### Comment out if just want to retrieve Product Description & Ingredients

# # Loop through each product
# for index, row in products_df.iterrows():
#     product_id = row['Product ID']
#     product_link = row['Link']
    
#     driver.get(product_link)
#     scroll_to_load_content(driver)
    
#     if page_not_found(driver):
#         print(f"Page not found for product ID: {product_id}")
#         skipped_products.append(product_id)
#         continue  # Skip to the next iteration of the loop
    
#     try:
            
#         WebDriverWait(driver, 30).until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="pr-review"]'))
#         )

#         reviews_text = find_element_with_retry(driver, By.CSS_SELECTOR, ["header.pr-rd-main-header h4.pr-rd-review-total.pr-h1"], retries=3).text
#         ### print(f"Total Reviews Found on Page (Full) {reviews_text}")
#         total_reviews_on_page = int(reviews_text.split()[0])
#         ### print(f"Total Reviews Found on Page {total_reviews_on_page}")
        
#         reviews_rating_listed = find_element_with_retry(driver, By.CSS_SELECTOR, ["div.pr-snippet-stars-container div.pr-snippet-stars.pr-snippet-stars-png div.pr-snippet-rating-decimal"], retries=3).text
#         review_rating_float = float(reviews_rating_listed)        
        
#         if total_reviews_on_page < 100 and review_rating_float < 4.5:
#             print(f"Product {product_id} has less than 100 reviews and less than 4.5 rating. It is being skipped")
#             products_less_than_100rev.append(product_id)
#             products_less_criteria_rating.append(product_id)
#             continue
#         elif total_reviews_on_page < 100:
#             print(f"Product {product_id} has less than 100 reviews. It is being skipped")
#             products_less_than_100rev.append(product_id)
#             continue    # Move to the next product immediately
#         elif review_rating_float < 4.5:
#             print(f"Product {product_id} has less than 4.5 rating. It is being skipped")
#             products_less_criteria_rating.append(product_id)
#             continue 
        
#     except TimeoutException as e:
#         print("Timeout Error: ", e)
#     except Exception as e:
#         print(f"An error occurred: {e}")

# if skipped_products:
#     print("Skipped product IDs due to 'Page Not Found':")
#     print(skipped_products)
# else: 
#     print("No skipped product IDs found.")

# if products_less_than_100rev:
#     print("Product IDs that have less than 100 reviews:")
#     print(products_less_than_100rev)  
# else: 
#     print("No products with less than 100 reviews found.")

# if products_less_criteria_rating:
#     print("Product IDs that have less than 4.5 rating:")
#     print(products_less_criteria_rating)  
# else: 
#     print("No products with less than 4.5 rating found.")
     
# driver.quit()        