from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import requests
from bs4 import BeautifulSoup
import time
from fake_useragent import UserAgent

app = FastAPI()

# Function to get a random user agent
def get_random_user_agent():
    ua = UserAgent()
    return ua.random

# Function to get the HTML content of a given URL using rotating user agents
def get_html(url, retries=5):
    for attempt in range(retries):
        custom_user_agent = get_random_user_agent()
        headers = {
            'User-Agent': custom_user_agent,
            'Accept-Language': 'en-GB,en;q=0.9'
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Attempt {attempt + 1}: Failed to retrieve page with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}: Request failed: {e}")
        
        # Wait before retrying
        time.sleep(2 + random.uniform(0, 2))
    
    print("Max retries reached. Skipping URL.")
    return None

# Function to extract product links from a single page
def extract_product_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_links = set()  # Use a set to avoid duplicates
    for link in soup.select('a.a-link-normal.s-no-outline'):
        product_url = 'https://www.amazon.com' + link['href']
        # Filter out links that do not appear to be product pages
        if '/dp/' in product_url or '/gp/product/' in product_url:
            product_links.add(product_url)
    return product_links

# Function to scrape all product links for a given keyword
def scrape_amazon_products(keyword, delay=5):
    base_url = "https://www.amazon.com/s?k=" + keyword.replace(" ", "+")
    page = 1

    while True:
        url = f"{base_url}&page={page}"
        html = get_html(url)
        if html:
            product_links = extract_product_links(html)
            if product_links:
                # Return a random product link
                return random.choice(list(product_links))
            else:
                print("No more products found or end of pages.")
                break
        else:
            print("Failed to retrieve page after multiple attempts.")
            break
    
    return None

# Define a model for the request body
class KeywordRequest(BaseModel):
    keyword: str

@app.post("/get-product-link/")
def get_product_link(request: KeywordRequest):
    keyword = request.keyword
    product_link = scrape_amazon_products(keyword)
    if product_link:
        return {"product_link": product_link}
    else:
        raise HTTPException(status_code=404, detail="No product link found")

# Run the server with: uvicorn script_name:app --reload
