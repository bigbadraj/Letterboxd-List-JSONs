import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import platform
from tqdm import tqdm
import csv

# Detect operating system and set appropriate paths
def get_os_specific_paths():
    """Return OS-specific file paths."""
    system = platform.system()
    
    if system == "Windows":
        # Windows paths
        base_dir = r'C:\Users\bigba\aa Personal Projects\Letterboxd List Scraping'
        output_dir = os.path.join(base_dir, 'Outputs')
    elif system == "Darwin":  # macOS
        # macOS paths
        base_dir = '/Users/calebcollins/Documents/Letterboxd List Scraping'
        output_dir = os.path.join(base_dir, 'Outputs')
    
    return {
        'base_dir': base_dir,
        'output_dir': output_dir
    }

# Get OS-specific paths
paths = get_os_specific_paths()
output_dir = paths['output_dir']

# Thread-safe list for storing movie data
class ThreadSafeList:
    def __init__(self):
        self.items = []
        self.lock = threading.Lock()
    
    def append(self, item):
        with self.lock:
            self.items.append(item)
    
    def __len__(self):
        return len(self.items)

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def process_film(session, film_url, movies_data):
    try:
        film_response = session.get(f"https://letterboxd.com{film_url}", timeout=10)
        film_response.raise_for_status()
        film_soup = BeautifulSoup(film_response.content, 'html.parser')
        
        og_title = film_soup.find('meta', property='og:title')
        if og_title:
            title_text = og_title['content']
            
            year = ''
            if '(' in title_text and ')' in title_text:
                year = title_text[title_text.rindex('(')+1:title_text.rindex(')')]
                title = title_text[:title_text.rindex('(')].strip()
            else:
                title = title_text
            
            movies_data.append({'Title': title, 'Year': year})
            
            if len(movies_data) % 10 == 0:
                print(f'Scraped {len(movies_data)} titles. Latest: {title}')
            
            sleep(0.05)  # Reduced sleep time
    except Exception as e:
        print(f"Error processing film {film_url}: {e}")

def process_page(session, url, movies_data, max_films):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        # Updated selector for new Letterboxd HTML structure
        film_list = soup.find('ul', class_='poster-list')
        
        if not film_list:
            return False
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            # Look for the new posteritem structure
            for li in film_list.find_all('li', class_='posteritem'):
                if max_films and len(movies_data) >= max_films:
                    return False
                    
                # Extract movie information from the inner div with data attributes
                # The data attributes are on the inner div, not the li element
                inner_div = li.find('div', class_='react-component')
                if inner_div:
                    film_url = inner_div.get('data-target-link') or inner_div.get('data-item-link')
                else:
                    film_url = None
                
                if not film_url:
                    # Fallback: look for anchor tag
                    anchor = li.find('a', href=True)
                    if anchor:
                        film_url = anchor['href']
                
                # Additional fallback: look for any link with /film/ in it
                if not film_url:
                    film_link = li.find('a', href=lambda x: x and '/film/' in x)
                    if film_link:
                        film_url = film_link['href']
                
                if film_url:
                    futures.append(
                        executor.submit(process_film, session, film_url, movies_data)
                    )
            
            for future in as_completed(futures):
                future.result()
        
        return bool(soup.find('a', class_='next'))
    except Exception as e:
        print(f"Error processing page {url}: {e}")
        return False

def main():
    # Configure these as needed
    base_url = "https://letterboxd.com/bigbadraj/list/every-movie-ive-seen-ranked/"
    max_films = None  # Set to None for no limit
    
    if base_url[-1] != '/':
        base_url += '/'
    
    session = create_session()
    movies_data = ThreadSafeList()
    page = 1
    
    while True:
        url = f'{base_url}page/{page}/'
        has_next = process_page(session, url, movies_data, max_films)
        
        if not has_next or (max_films and len(movies_data) >= max_films):
            break
            
        page += 1
    
    df = pd.DataFrame(movies_data.items)
    output_csv = os.path.join(output_dir, 'film_titles.csv')
    df.to_csv(output_csv, index=False)
    print(f"\nScraping complete. {len(movies_data)} films saved to {output_csv}")

if __name__ == "__main__":
    main()