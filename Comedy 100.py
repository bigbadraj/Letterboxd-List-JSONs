import requests
from bs4 import BeautifulSoup
import json
import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import os
import platform
from tqdm import tqdm

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

# Define a custom print function
def print_to_csv(message: str):
    """Prints a message to the terminal and appends it to All_Outputs.csv."""
    print(message)  # Print to terminal
    with open(os.path.join(output_dir, 'All_Outputs.csv'), mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([message])  # Write the message as a new row

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

# The process_film function is no longer needed since we extract data directly from the list page

def process_page(session, url, max_films, min_watches, approved_films):
    try:
        # Check if we've already hit the max_films limit before processing the page
        if len(approved_films) >= max_films:
            return False, []
            
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the poster list - try different possible selectors
        film_grid = soup.find('ul', class_='poster-list')
        if not film_grid:
            # Try alternative selector for the new structure
            film_grid = soup.find('ul', class_='poster-list')
            if not film_grid:
                # Look for any ul containing posteritem elements
                film_grid = soup.find('ul')
        
        if not film_grid:
            print_to_csv("Warning: Could not find poster list container")
            return False, []
            
            
        film_elements = film_grid.find_all('li', class_='posteritem')
        if not film_elements:
            print_to_csv("Warning: Could not find posteritem elements")
            return False, []
        
        print_to_csv(f"Found {len(film_elements)} film elements on this page")
        
        # Debug: Show attributes of first film element
        if film_elements:
            first_film = film_elements[0]
            print_to_csv(f"First film attributes: {dict(first_film.attrs)}")
        
        film_data_list = []
        
        for i, film in enumerate(film_elements, 1):
            # Check if we've hit the max_films limit before processing each film
            if len(approved_films) >= max_films:
                print_to_csv(f"\nReached maximum number of films ({max_films}). Stopping...")
                return False, film_data_list
                
            try:
                # First try to get data from the li element attributes
                film_url = film.get('data-item-link')
                film_title = film.get('data-item-full-display-name')
                film_id = film.get('data-film-id')
                
                # If not found on li element, look inside the nested div.react-component
                if not all([film_url, film_title, film_id]):
                    react_component = film.find('div', class_='react-component')
                    if react_component:
                        film_url = react_component.get('data-item-link') or film_url
                        film_title = react_component.get('data-item-full-display-name') or film_title
                        film_id = react_component.get('data-film-id') or film_id
                
                if film_url and film_title and film_id:
                    # Extract year from the full display name
                    year = ''
                    if '(' in film_title and ')' in film_title:
                        year = film_title[film_title.rindex('(')+1:film_title.rindex(')')]
                        title = film_title[:film_title.rindex('(')].strip()
                    else:
                        title = film_title
                    
                    # Check for duplicate using title+year combination
                    film_key = f"{title}_{year}"
                    if film_key in approved_films:
                        print_to_csv(f"❌ {film_title} - Not added (Duplicate film)")
                        continue
                    
                    # We need to check the rating count, so visit the individual film page
                    try:
                        full_film_url = f"https://letterboxd.com{film_url}"
                        film_response = session.get(full_film_url, timeout=10)
                        film_soup = BeautifulSoup(film_response.content, 'html.parser')
                        
                        # Look for rating count in JSON-LD data
                        json_ld = film_soup.find('script', type='application/ld+json')
                        rating_count = 0
                        if json_ld:
                            try:
                                json_text = json_ld.string.strip()
                                if '/* <![CDATA[ */' in json_text:
                                    json_text = json_text.replace('/* <![CDATA[ */', '').replace('/* ]]> */', '')
                                film_data_json = json.loads(json_text)
                                rating_count = film_data_json.get('aggregateRating', {}).get('ratingCount', 0)
                            except (json.JSONDecodeError, KeyError):
                                rating_count = 0
                        
                        # Check minimum rating requirement
                        if rating_count < min_watches:
                            print_to_csv(f"❌ {film_title} - Not added (Rating count: {rating_count} < {min_watches})")
                            continue
                        
                        # Create film data
                        film_data = {
                            'title': title,
                            'year': year,
                            'id': film_id,
                            'original_order': len(approved_films) + 1
                        }
                        
                        # Add to approved films
                        approved_films.add(film_key)
                        film_data_list.append(film_data)
                        print_to_csv(f"✅ {film_title}")
                        
                    except Exception as e:
                        print_to_csv(f"❌ {film_title} - Error checking rating count: {str(e)}")
                        continue
                else:
                    print_to_csv(f"Warning: Missing data for film element {i}")
                    # Debug: Show what attributes this element actually has
                    available_attrs = dict(film.attrs)
                    print_to_csv(f"Available attributes for element {i}: {available_attrs}")
                    
            except Exception as e:
                print_to_csv(f"Error processing film element {i}: {str(e)}")
                continue
                    
        has_next = bool(soup.find('a', class_='next'))
        return has_next, film_data_list
        
    except Exception as e:
        print_to_csv(f"Error processing page: {str(e)}")
        return False, []

def main():
    base_url = 'https://letterboxd.com/asset/list/stand-up-comedy-a-comprehensive-list/by/rating/'
    min_watches = 1000
    max_films = 100
    
    session = create_session()
    all_movies = []
    approved_films = set()  # Changed from approved_ids to approved_films
    page = 1
    
    while True:  # Changed from while len(all_movies) < max_films
        url = f'{base_url}page/{page}/'
        print_to_csv(f"\n=== Page {page} ===")
        print_to_csv(f"Progress: {len(all_movies)}/{max_films} movies collected")
        
        has_next, page_data = process_page(session, url, max_films, min_watches, approved_films)
        all_movies.extend(page_data)
        
        # Check if we've hit the max_films limit or reached the end of pages
        if len(approved_films) >= max_films or not has_next:
            break
            
        page += 1
        time.sleep(1)
    
    # Save to CSV maintaining original order
    list_name = "stand_up_comedy"  # You can modify this based on your list
    filepath = os.path.join(output_dir, f"{list_name}.csv")
    
    # Write to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Year', 'LetterboxdID'])  # Header row
        for movie in all_movies:  # Will naturally maintain the order from processing
            writer.writerow([movie['title'], movie['year'], movie['id']])
    
    print_to_csv(f"Scraped {len(all_movies)} movies")

if __name__ == "__main__":
    main()