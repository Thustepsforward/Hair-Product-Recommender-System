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
    columns_details = ['Product ID', 'Picture URL', 'Description', 'Health Facts', 'Highlights']
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

# def page_not_found(driver):
#     """Check if the 'Page Not Found' title is present on the page."""
#     try:
#         driver.find_element(By.CSS_SELECTOR, 'div.TextOnlyHero div.TextOnlyHero__headline h1.Text-ds.Text-ds--title-2.Text-ds--center.Text-ds--black')
#         return True
#     except NoSuchElementException:
#         return False

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

# Parameters for batch processing
# start_product_id = 'T461'  # Adjust as needed 
# batch_size = 100  # Adjust as needed

# Uncomment for processing specific products
product_ids_to_filter = ['T380', 'T426', 'T542', 'T450', 'T171', 'T115', 'T423', 'T427', 'T154', 'T432', 'T398', 'T404', 'T403', 'T431', 'T489', 'T349', 'T516', 'T464', 'T26', 'T341', 'T6', 'T142', 'T417', 'T379', 'T513', 'T88']


# Setup for collecting skipped product IDs
skipped_products = []
# List to track IDs with reviews less than 100
products_less_than_100rev = []
# List to track IDs with reviews less than 4.5
products_less_criteria_rating = []

# Load the list of products
products_df = pd.read_csv('/Users/thumato/Desktop/Final_Capstone_Project/Cleaned Datasets/Target_products_links_only.csv')
# Path for scraping leftover product descriptions: '/Users/thumato/Desktop/Capstone Project - Selenium/Ulta_product_description_extra.csv'

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
    
    # Reset ingredient information for each product
    product_ingredients_label_info = ''
    combined_ingredients_drug_facts = ''
    product_ingredients = ''
    
    driver.get(product_link)
    scroll_to_load_content(driver)
    
    # if page_not_found(driver):
    #     print(f"Page not found for product ID: {product_id}")
    #     skipped_products.append(product_id)
    #     continue  # Skip to the next iteration of the loop
    try:
        
        ############# Check for Ratings & Reviews Before Proceed with Scraping BELOW #############
        scroll_to_load_content(driver)
        
        # Scroll to Reviews Section
        review_dashboard = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='ReviewsDashboard'] h3[data-test='reviews-heading']"], retries=3)
        driver.execute_script("arguments[0].scrollIntoView(true);", review_dashboard)
        
        rating_listed = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='rating-value']"], retries=3).text
        rating_listed_float = float(rating_listed)   
        
        reviews_text = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='ReviewsDashboard'] div[class='h-padding-l-jumbo h-text-hd4']"], retries=3).text
        cleaned_reviews_text = reviews_text.replace("We found ", "").replace(" matching reviews", "")
        total_reviews_on_page = int(cleaned_reviews_text)
        
        if total_reviews_on_page < 100 and rating_listed_float < 4.5:
            print(f"Product {product_id} has less than 100 reviews and less than 4.5 rating. It is being skipped")
            products_less_than_100rev.append(product_id)
            products_less_criteria_rating.append(product_id)
            continue
        elif total_reviews_on_page < 100:
            print(f"Product {product_id} has less than 100 reviews. It is being skipped")
            products_less_than_100rev.append(product_id)
            continue    # Move to the next product immediately
        elif rating_listed_float < 4.5:
            print(f"Product {product_id} has less than 4.5 rating. It is being skipped")
            products_less_criteria_rating.append(product_id)
            continue 
        
        ############# Retrieving Info for CSV containing Product Details BELOW #############
        # # Find the image link of the first picture  
        # product_img_link = find_element_with_retry(driver, By.CSS_SELECTOR, ['div[data-test="image-gallery-item-0"] img'], retries=3).get_attribute('src')
        # print("Link:", product_img_link)

        # # Wait for the Details section to be visible 
        # WebDriverWait(driver, 10).until(
        #     EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id='product-detail-tabs']"))
        # )

        # # Scroll the summary into view
        # details_summary = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[id='product-detail-tabs']"], retries=3)
        # driver.execute_script("arguments[0].scrollIntoView(true);", details_summary)
        # time.sleep(1)  # Allow time for any floating elements to move away

        # # # Wait for the content under the Details to become visible. No need to click button since details section should already be open.
        # # WebDriverWait(driver, 10).until(
        # #     EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-test='productDetailTabs-itemDetailsTab'] > div[class='sc-ba8e49e-10 iKYepR'] > h4[class='sc-fe064f5c-0 fsJuM h-text-bs h-margin-b-none']"))
        # # )
        
        # # Find description under the 'Details' section  div[data-test="productDetailTabs-itemDetailsTab"]  
        # product_description = find_element_with_retry(driver, By.CSS_SELECTOR, ['div[data-test="item-details-description"]'], retries=3).text
        # print("Description:", product_description)
        
        # # Find all highlights under the 'Details' section
        # headers = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div[data-test="productDetailTabs-itemDetailsTab"] div[class="sc-6a3f6e8d-1 fGwsUn h-bg-white"] h4[class="sc-fe064f5c-0 fsJuM h-text-bs h-margin-b-none"]'], retries=3)
        
        # for header in headers:
        #     category = header.text.strip()
        #     if 'Highlights' in category:
        #         highlights_list = find_element_with_retry(header, By.XPATH, ["./following-sibling::ul"], retries = 3)
        #         highlights_texts = find_elements_with_retry(highlights_list, By.CSS_SELECTOR, ["span"], retries = 3)
        #         product_hightlight = ', '.join([item.text for item in highlights_texts])
        #         print("Highlights:", product_hightlight)
        #     else:
        #         product_hightlight = ''
        #         print("Highlights can not be found.")    
        
        # # Find Health Facts under the 'Specifications' section
        # specification_title = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='@web/site-top-of-funnel/ProductDetailCollapsible-Specifications'] button.styles_button__D8Xvn.styles_buttonStandard__0BuND.styles_buttonEnabled__3cVAx h3.sc-fe064f5c-0.cJJgsH.h-margin-b-none"])
        # driver.execute_script("arguments[0].scrollIntoView(true);", specification_title)
        # time.sleep(1)  # Allow time for any floating elements to move away        

        # # Try clicking the summary using JavaScript
        # button_specification = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='@web/site-top-of-funnel/ProductDetailCollapsible-Specifications'] button.styles_button__D8Xvn.styles_buttonStandard__0BuND.styles_buttonEnabled__3cVAx"])
        # driver.execute_script("arguments[0].click();", button_specification)

        # # # Wait for the 'Health Facts' content under the Specifications to become visible
        # # WebDriverWait(driver, 10).until(
        # #     EC.visibility_of_element_located((By.CSS_SELECTOR, "//div[@data-test='productDetailTabs-itemDetailsTab']//div[@data-test='item-details-specifications']//div/div[b[text()='Health Facts']]/following-sibling"))
        # # )
        
        # # Retrieve all div elements within the specifications section
        # details_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-test="item-details-specifications"] div div')

        # # Iterate over each div to find the one that contains 'Health Facts'
        # for div in details_divs:
        #     # Check if the 'b' tag within the div contains 'Health Facts'
        #     b_tag = div.find_element(By.TAG_NAME, 'b')
        #     if b_tag.text == 'Health Facts:':
        #         # Extract the text of the div, which includes the health facts
        #         product_health_facts = div.text.split(':', 1)[1].strip() if ':' in div.text else div.text
        #         print("Health Facts:", product_health_facts)
        #         break

        # # product_health_facts = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div[data-test="item-details-specifications"] div div:has(b:contains("Health Facts"))'], retries=3).text
        # # print("Health Facts:", product_health_facts)

        # # Append to review dataframe
        # new_data_details = pd.DataFrame({
        #     'Product ID': [product_id],
        #     'Picture URL': [product_img_link],
        #     'Description': [product_description],
        #     'Health Facts': [product_health_facts],
        #     'Highlights' : [product_hightlight]
        # })

        # details_df = pd.concat([details_df, new_data_details], ignore_index=True)

        ############# Retrieving Info for CSV containing Product Details ABOVE #############
        
        ############# Retrieving Info for CSV containing Product Ingredients BELOW #############
        ### For Products with Label Info section ###
        try:
            # Scroll the Label Info section into view
            label_info_title = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='@web/site-top-of-funnel/ProductDetailCollapsible-LabelInfo'] button.styles_button__D8Xvn.styles_buttonStandard__0BuND.styles_buttonEnabled__3cVAx h3.sc-fe064f5c-0.cJJgsH.h-margin-b-none"], retries = 3)
            driver.execute_script("arguments[0].scrollIntoView(true);", label_info_title)
            time.sleep(1)  # Allow time for any floating elements to move away

            # Try clicking the label info using JavaScript
            button_label_info = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='@web/site-top-of-funnel/ProductDetailCollapsible-LabelInfo'] button.styles_button__D8Xvn.styles_buttonStandard__0BuND.styles_buttonEnabled__3cVAx"], retries = 3)
            
            if button_label_info:
                # Try clicking the summary using JavaScript
                driver.execute_script("arguments[0].click();", button_label_info)
                    
                # Wait for the content under the Label info to become visible
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test="productDetailTabs-nutritionFactsTab"] div[class="h-margin-b-default"]'))
                )
                    
                # Navigate to the parent div that likely contains the ingredients list
                label_info_section = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div[data-test="productDetailTabs-nutritionFactsTab"] div[class="h-margin-b-default"]'], retries = 3)

                # Loop through the sections to find 'Ingredients'
                for label_info in label_info_section:
                    header = find_element_with_retry(label_info, By.TAG_NAME, ['h4'], retries = 4).text
                    if 'Ingredients:' in header:
                        # The ingredients text is expected to be in a div below the h4
                        product_ingredients_label_info = find_element_with_retry(label_info, By.CSS_SELECTOR, ['div.h-text-transform-caps'], retries = 3).text
                        print("Ingredients:", product_ingredients_label_info)
                        break   
        except Exception as e:
            print(f"Could not process Label Info for {product_id}: {e}")
            
        ### For Products with Drug Facts section ###
        try: 
            # Scroll the Label Info section into view
            drug_facts_title = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='@web/site-top-of-funnel/ProductDetailCollapsible-DrugFacts'] button.styles_button__D8Xvn.styles_buttonStandard__0BuND.styles_buttonEnabled__3cVAx h3.sc-fe064f5c-0.cJJgsH.h-margin-b-none"], retries = 3)
            driver.execute_script("arguments[0].scrollIntoView(true);", drug_facts_title)
            time.sleep(1)  # Allow time for any floating elements to move away

            # Try clicking the label info using JavaScript
            button_drug_facts_info = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='@web/site-top-of-funnel/ProductDetailCollapsible-DrugFacts'] button.styles_button__D8Xvn.styles_buttonStandard__0BuND.styles_buttonEnabled__3cVAx"], retries = 3)
            
            if button_drug_facts_info:
                # Try clicking the summary using JavaScript
                driver.execute_script("arguments[0].click();", button_drug_facts_info)
                    
                # Wait for the content under the Label info to become visible
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test="productDetailTabs-drugFactsTab"] div[class="h-margin-b-default"]'))
                )
                    
                # Navigate to the parent div that likely contains the ingredients list
                drug_facts_section = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div[data-test="productDetailTabs-drugFactsTab"] > div > div[class="h-margin-b-default"]'], retries=3)

                # Initialize variables to hold active and inactive ingredients
                active_ingredients = ''
                inactive_ingredients = ''

                # Loop through the sections to find 'Active ingredients' and 'Inactive ingredients'
                for drug_facts in drug_facts_section:
                    print(drug_facts)
                    header_drug_facts = find_element_with_retry(drug_facts, By.TAG_NAME, ['h4'], retries=3).text
                    if 'Active ingredients' in header_drug_facts:
                        # Retrieve active ingredients text, expected to be in a div below the h4
                        active_ingredients = find_element_with_retry(drug_facts, By.CSS_SELECTOR, ['div.h-text-transform-caps'], retries=3).text
                    elif 'Inactive ingredients' in header_drug_facts:
                        # Retrieve inactive ingredients text, expected to be in a div below the h4
                        inactive_ingredients = find_element_with_retry(drug_facts, By.CSS_SELECTOR, ['div.h-text-transform-caps'], retries=5).text

            # Combine active and inactive ingredients if they exist
            if active_ingredients or inactive_ingredients:
                combined_ingredients_drug_facts = f"Active Ingredients: {active_ingredients}; Inactive Ingredients: {inactive_ingredients}"
                print("Combined Ingredients:", combined_ingredients_drug_facts)
        except TimeoutException:
            print("Timeout waiting for drug facts to be visible.")
        except Exception as e:
            print(f"Could not process Drug Facts for {product_id}: {e}")

        # Decide which ingredients data to use
        if product_ingredients_label_info:
            product_ingredients = product_ingredients_label_info
        elif combined_ingredients_drug_facts:
            product_ingredients = combined_ingredients_drug_facts
        print(f"Final Ingredients for {product_id}: {product_ingredients}")  # Debugging output
        
        # Append to the ingredients DataFrame
        if product_ingredients:  # Ensure there's something to append
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
        product_ingredients = ''  # Ensure to catch any failures
        continue  # Optionally skip to next product instead of stopping

# append_to_csv(details_df, 'Target_product_description.csv')
append_to_csv(ingredients_df, 'Target_additional_ingredients.csv')

if products_less_than_100rev:
    print("Product IDs that have less than 100 reviews:")
    print(products_less_than_100rev)  
else: 
    print("No products with less than 100 reviews found.")

if products_less_criteria_rating:
    print("Product IDs that have less than 4.5 rating:")
    print(products_less_criteria_rating)  
else: 
    print("No products with less than 4.5 rating found.")

driver.quit()   
