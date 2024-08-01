from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import pandas as pd
import os
import re

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

def load_more_reviews(driver):
    # Target has a "Load # More" button that displays more reviews, in addition to the ones already present
    # Function clicks on the button until it does not exist in order to ensure all reviews are visible
    try:
        while True:
            try: 
                # Wait for the "Load More" button to be present
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-test='load-more-btn'] button[class='sc-9306beff-0 sc-e6042511-0 lkICsC ibmrHV']"))
                )

                # Use find_element_with_retry to locate the "Load More" button
                load_more_button = find_element_with_retry(driver, By.CSS_SELECTOR, ["div[data-test='load-more-btn'] button[class='sc-9306beff-0 sc-e6042511-0 lkICsC ibmrHV']"], retries=5, delay=4)
                
                if load_more_button:
                    # Find and wait for the "Load More" button to be clickable
                    WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-test='load-more-btn'] button[class='sc-9306beff-0 sc-e6042511-0 lkICsC ibmrHV']"))
                    )

                    # Scroll the "Load More" button into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(2)  # Allow time for any floating elements to move away
                    
                    # Attempt to click using JavaScript
                    driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(5)  # Wait for more reviews to load and for the button to possibly reappear

                else:
                    # If no "Load More" button is found, exit the loop
                    break
            except StaleElementReferenceException:
                print("Stale element reference, retrying...")
                continue
    except TimeoutException:
        print("Timed out waiting for more reviews to load.")
    except NoSuchElementException:
        print("No more 'Load More' button found or not clickable.")
    except Exception as e:
        print(f"An error occurred: {e}")

def setup_dataframe():
    columns_reviews = ['Product ID', 'Review Title', 'Review Rating', 'Review Text']
    df_reviews = pd.DataFrame(columns=columns_reviews)
    return df_reviews

def append_to_csv(df, filename):
    if not os.path.exists(filename):
        df.to_csv(filename, index=False, mode='w')
    else:
        df.to_csv(filename, index=False, mode='a', header=False)

# Initialize DataFrame
reviews_df = setup_dataframe()

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
    
def clean_text(text):
    # Updated replacements with additional patterns
    replacements = {
        'â€œ': '"',  # Replacing ‘â€œ’ with a standard quotation mark
        'â€”': '-',  # Replacing ‘â€”’ with a hyphen
        'â€™': "'",  # Replacing curly single quote
        'â€¦': '...',  # Replacing ellipsis
        'â€': '',  # Removing any stray occurrences that don't match others
        'â': '',  # Adding this to handle isolated occurrences of â
        'â%': ''  # Adding this to handle occurrences of â% which may be malformed
    }
    
    pattern = re.compile("|".join(replacements.keys()))
    return pattern.sub(lambda m: replacements[re.escape(m.group(0))], text)

driver = webdriver.Chrome()

# Initialize the counter for reviews
total_reviews = 0

# Parameters for batch processing
start_product_id = 'T11'  
batch_size = 10  

# Load the list of products
products_df = pd.read_csv('/Users/thumato/Desktop/Final_Capstone_Project/Cleaned Datasets/Target_products_links_only.csv')

# Determine the starting index
try:
    start_index = products_df.index[products_df['Product ID'] == start_product_id][0]
    products_df = products_df.iloc[start_index:start_index + batch_size]
except IndexError:
    print("Starting Product ID not found in the DataFrame.")
    driver.quit()
    exit()

total_reviews = 0
# Setup for collecting skipped product IDs
# skipped_products = []
# List to track IDs with mismatched review counts
mismatched_reviews_products = []
# List to track IDs with reviews less than 100
products_less_than_100rev = []
# List to track IDs with reviews less than 4.5
products_less_criteria_rating = []

# Loop through each product
for index, row in products_df.iterrows():
    product_id = row['Product ID']
    product_link = row['Link']
    
    driver.get(product_link)
    scroll_to_load_content(driver)
    
    reviews = None
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

        ############# Retrieving Info for CSV containing Product Reviews BELOW ############# 
            
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="sc-9ca3e7a8-0 ICAiK"]'))
        )

        load_more_reviews(driver)
        
        current_count = 0
        
        reviews = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div[class="sc-9ca3e7a8-0 ICAiK"]'], retries=3)
        reviews_item_loaded_count = len(reviews)
        
        if reviews_item_loaded_count != total_reviews_on_page:
            print(f"Mismatch in counts for {product_id}. Expected: {total_reviews_on_page}, Got: {reviews_item_loaded_count}")
            mismatched_reviews_products.append(product_id)
            continue  # Skip to the next product
        
        
        while reviews: 
            # Scroll to load more items
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            ### print("-----------Products from Page", page_number, "---------")
            
            reviews = driver.find_elements(By.CSS_SELECTOR, 'div[class="sc-9ca3e7a8-0 ICAiK"]')
            
            for review in reviews:
                try:        
                    review_title = find_element_with_retry(review, By.CSS_SELECTOR, ['h4[data-test="review-card--title"]'], retries=3).text
                    print("Review Title:", review_title)
                    
                    review_rating = find_element_with_retry(review, By.CSS_SELECTOR, ['span[data-test="ratings"] > span'], retries=3).text
                    print("Review Rating:", review_rating)
                    
                    review_text = find_element_with_retry(review, By.CSS_SELECTOR, ['div[data-test="review-card--text"]'], retries=3).text
                    cleaned_review_text = clean_text(review_text)
                    
                    # Attempt to print the review text
                    try:
                        print("Review Text:", cleaned_review_text)
                    except Exception as e:
                        print(f"An error occurred while printing the review text: {e}")                    
                    
                    new_data = pd.DataFrame({
                        'Product ID': [product_id],
                        'Review Title': [review_title],
                        'Review Rating': [review_rating],
                        'Review Text': [cleaned_review_text]
                    })
                    reviews_df = pd.concat([reviews_df, new_data], ignore_index=True)
                    
                    current_count += 1  # Increment the review counter
                    
                except NoSuchElementException as e:
                    print(f"Failed to retrieve complete information for a product: {e}")

            if current_count >= total_reviews_on_page:
                break

        total_reviews += current_count
        # Print the count of reviews scraped for the current product
        print(f"Reviews scraped for {product_id}: {current_count}")
        
        if current_count != total_reviews_on_page:
            print(f"Mismatch in counts for {product_id}, removing entries. Expected: {total_reviews_on_page}, Got: {current_count}")
            mismatched_reviews_products.append(product_id)
            continue  # Skip to the next product
            
    except TimeoutException as e:
        print("Timeout Error: ", e)
        mismatched_reviews_products.append(product_id)
    except Exception as e:
        print(f"An error occurred: {e}")

if mismatched_reviews_products:
    print("Product IDs with mismatched review counts:")
    print(mismatched_reviews_products)
    filtered_df = reviews_df[~reviews_df['Product ID'].isin(mismatched_reviews_products)]
    append_to_csv(filtered_df, 'Target_reviews.csv')  
else:
    append_to_csv(reviews_df, 'Target_reviews.csv')
    print("No mismatched review counts found.")

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

