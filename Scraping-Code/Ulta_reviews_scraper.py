from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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

def go_to_next_review_page(driver, reviews):
    try:
        # Use find_element_with_retry to locate the Next button
        next_button = find_element_with_retry(driver, By.CSS_SELECTOR, ["a.pr-rd-pagination-btn.pr-rd-pagination-btn--next"], retries=5, delay=4)
        
        if next_button:
            
            # Find and wait for the Next button to be clickable
            next_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pr-rd-pagination-btn.pr-rd-pagination-btn--next"))
            )

            # Scroll the Next button into view
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(2)  # Allow time for any floating elements to move away
            
            # Attempt to click using JavaScript
            driver.execute_script("arguments[0].click();", next_button)
            
            # Wait for the staleness of the first product of the previous page
            WebDriverWait(driver, 20).until(
                EC.staleness_of(reviews[0])
            )

            # Then, fetch new reviews
            reviews = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="pr-review"]'))
            ) 
            
            ### print("Navigated to next review page.") # Keep
            return reviews
        else:
            print("Next button not found after retries.")
            return None
        
    except TimeoutException:
        print("Timed out waiting for the next page to load.")
    except NoSuchElementException:
        print("Next button not found or not clickable. May be on the last page.")
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

# # Uncomment for batch processing 
# # Parameters for batch processing
# start_product_id = 'U661'  
# batch_size = 24  

# # Uncomment for processing specific products
product_ids_to_filter = ['U27', 'U28', 'U29', 'U75', 'U105', 'U108', 'U200', 'U206', 'U270', 'U316', 'U320', 'U408', 'U416', 'U450', 'U522', 'U533', 'U557', 'U573', 'U592', 'U628']

# Load the list of products
products_df = pd.read_csv('/Users/thumato/Desktop/Final_Capstone_Project/Cleaned Datasets/Ulta_products_links_only.csv')


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
    # product_reviews_file.close() 
    exit()

total_reviews = 0
# Setup for collecting skipped product IDs
skipped_products = []
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
    
    if page_not_found(driver):
        print(f"Page not found for product ID: {product_id}")
        skipped_products.append(product_id)
        continue  # Skip to the next iteration of the loop
    
    # Initialize the page counter
    page_number = 1
    reviews = None
    try:
        ############# Retrieving Info for CSV containing Product Reviews BELOW ############# 
            
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="pr-review"]'))
        )

        # Get Total # of Written Reviews Listed on Page
        reviews_text = find_element_with_retry(driver, By.CSS_SELECTOR, ["header.pr-rd-main-header h4.pr-rd-review-total.pr-h1"], retries=3).text
        ### print(f"Total Reviews Found on Page (Full) {reviews_text}")
        total_reviews_on_page = int(reviews_text.split()[0])
        ### print(f"Total Reviews Found on Page {total_reviews_on_page}")
        
        # Get Product Rating
        reviews_rating_listed = find_element_with_retry(driver, By.CSS_SELECTOR, ["div.pr-snippet-stars-container div.pr-snippet-stars.pr-snippet-stars-png div.pr-snippet-rating-decimal"], retries=3).text
        review_rating_float = float(reviews_rating_listed)        
        
        if total_reviews_on_page < 100 and review_rating_float < 4.5:
            print(f"Product {product_id} has less than 100 reviews and less than 4.5 rating. It is being skipped")
            products_less_than_100rev.append(product_id)
            products_less_criteria_rating.append(product_id)
            continue
        elif total_reviews_on_page < 100:
            print(f"Product {product_id} has less than 100 reviews. It is being skipped")
            products_less_than_100rev.append(product_id)
            continue    # Move to the next product immediately
        elif review_rating_float < 4.5:
            print(f"Product {product_id} has less than 4.5 rating. It is being skipped")
            products_less_criteria_rating.append(product_id)
            continue 
        
        current_count = 0
        reviews = find_elements_with_retry(driver, By.CSS_SELECTOR, ['div[class="pr-review"]'], retries=3)
        
        while reviews: 
            # Scroll to load more items
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            ### print("-----------Products from Page", page_number, "---------")
            
            reviews = driver.find_elements(By.CSS_SELECTOR, 'div[class="pr-review"]')
            
            for review in reviews:
                try:        
                    review_title = find_element_with_retry(review, By.CSS_SELECTOR, ['header.pr-rd-header.pr-rd-content-block h5.pr-rd-review-headline.pr-h2'], retries=3).text
                    ### print("Review Title:", review_title)
                    
                    review_rating = find_element_with_retry(review, By.CSS_SELECTOR, ['div[aria-label^="Rated"][aria-label$="out of 5 stars"]'], retries=3).get_attribute('aria-label')
                    ### print("Review Rating:", review_rating)
                    
                    review_text = find_element_with_retry(review, By.CSS_SELECTOR, ['section.pr-rd-description.pr-rd-content-block p.pr-rd-description-text'], retries=3).text
                    cleaned_review_text = clean_text(review_text)
                    
                    # Attempt to print the review text
                    # try:
                    #     print("Review Text:", cleaned_review_text)
                    # except Exception as e:
                    #     print(f"An error occurred while printing the review text: {e}")                    
                    
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
            
            # Print completion of the current page - COMMENT IN if needed
            ### print("Completed scraping page", page_number)
        
            # Attempt to go to the next page
            reviews = go_to_next_review_page(driver, reviews)
            
            if not reviews:
                print("No more pages to navigate. Ending scrape.")
                break
            page_number += 1  # Increment the page number after successfully clicking next

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

if skipped_products:
    print("Skipped product IDs due to 'Page Not Found':")
    print(skipped_products)
else: 
    print("No skipped product IDs found.")

if mismatched_reviews_products:
    print("Product IDs with mismatched review counts:")
    print(mismatched_reviews_products)
    filtered_df = reviews_df[~reviews_df['Product ID'].isin(mismatched_reviews_products)]
    append_to_csv(filtered_df, 'Ulta_additional_reviews.csv')  
else:
    append_to_csv(reviews_df, 'Ulta_additional_reviews.csv')
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