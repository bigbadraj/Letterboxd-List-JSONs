# Import necessary libraries
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import requests
import re
import csv
import locale
import os
import platform
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import unicodedata
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from selenium.common.exceptions import NoSuchElementException
from credentials_loader import load_credentials

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
BASE_DIR = paths['output_dir']
LIST_DIR = paths['base_dir']

# Define a custom print function
def print_to_csv(message: str):
    """Prints a message to the terminal and appends it to All_Outputs.csv."""
    print(message)  # Print to terminal
    with open(os.path.join(output_dir, 'All_Outputs.csv'), mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([message])  # Write the message as a new row

# Configure locale and constants
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
MAX_MOVIES = 7000 # Currently using 7000
MAX_MOVIES_5000 = 5000
MAX_MOVIES_MPAA = 250
MAX_MOVIES_RUNTIME = 250
MAX_MOVIES_CONTINENT = 250

# Configure settings
MIN_RATING_COUNT = 1000
MIN_RUNTIME = 40
MAX_RETRIES = 25
RETRY_DELAY = 15
CHUNK_SIZE = 1900

# Configure specific maxes
MAX_180 = 75
MAX_240 = 5
MAX_MOVIES_G = 200
MAX_MOVIES_NC17 = 25
MAX_MOVIES_AFRICA = 20
MAX_MOVIES_OCEANIA = 150
MAX_MOVIES_SOUTH_AMERICA = 100

# File paths
BLACKLIST_PATH = os.path.join(LIST_DIR, 'blacklist.xlsx')
WHITELIST_PATH = os.path.join(LIST_DIR, 'whitelist.xlsx')
ZERO_REVIEWS_PATH = os.path.join(LIST_DIR, 'Zero_Reviews.xlsx')  # Add new path

# Load credentials
credentials = load_credentials()
TMDB_API_KEY = credentials['TMDB_API_KEY']

# Filtering criteria
FILTER_KEYWORDS = {
    'concert film', 'miniseries',
    'live performance', 'filmed theater', 'live theater', 
    'stand-up comedy', 'edited from tv series'
}

FILTER_GENRES = {'Documentary'}

# Add new constants for MPAA ratings
MPAA_RATINGS = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'NR']
mpaa_stats = {rating: {'film_data': [], 'director_counts': defaultdict(int), 'actor_counts': defaultdict(int), 
                       'decade_counts': defaultdict(int), 'genre_counts': defaultdict(int), 
                       'studio_counts': defaultdict(int), 'language_counts': defaultdict(int), 
                       'country_counts': defaultdict(int)} for rating in MPAA_RATINGS}  # Each entry will have Title, Year, tmdbID, and URL fields

# Add new constants for runtime categories
RUNTIME_CATEGORIES = {
    '90_Minutes_or_Less': [],
    '120_Minutes_or_Less': [],
    '180_Minutes_or_Greater': [],
    '240_Minutes_or_Greater': []
}

runtime_stats = {
    '90_Minutes_or_Less': {'film_data': [], 'director_counts': defaultdict(int), 'actor_counts': defaultdict(int), 
                     'decade_counts': defaultdict(int), 'genre_counts': defaultdict(int), 
                     'studio_counts': defaultdict(int), 'language_counts': defaultdict(int), 
                     'country_counts': defaultdict(int)},  # Each entry will have Title, Year, tmdbID, and URL fields
    '120_Minutes_or_Less': {'film_data': [], 'director_counts': defaultdict(int), 'actor_counts': defaultdict(int), 
                      'decade_counts': defaultdict(int), 'genre_counts': defaultdict(int), 
                      'studio_counts': defaultdict(int), 'language_counts': defaultdict(int), 
                      'country_counts': defaultdict(int)},  # Each entry will have Title, Year, tmdbID, and URL fields
    '180_Minutes_or_Greater': {'film_data': [], 'director_counts': defaultdict(int), 'actor_counts': defaultdict(int), 
                         'decade_counts': defaultdict(int), 'genre_counts': defaultdict(int), 
                         'studio_counts': defaultdict(int), 'language_counts': defaultdict(int), 
                         'country_counts': defaultdict(int)},  # Each entry will have Title, Year, tmdbID, and URL fields
    '240_Minutes_or_Greater': {'film_data': [], 'director_counts': defaultdict(int), 'actor_counts': defaultdict(int), 
                         'decade_counts': defaultdict(int), 'genre_counts': defaultdict(int), 
                         'studio_counts': defaultdict(int), 'language_counts': defaultdict(int), 
                         'country_counts': defaultdict(int)}  # Each entry will have Title, Year, tmdbID, and URL fields
}

# Define continents and their associated countries in a case-insensitive manner
CONTINENTS_COUNTRIES = {
    'Africa': ['Ivory Coast', 'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad', 'Comoros', 'Congo, Democratic Republic of the', 'Congo, Republic of the', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe', 'Congo'],
    'Asia': ['State of Palestine', 'Hong Kong', 'Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Bhutan', 'Brunei', 'Cambodia', 'China', 'Cyprus', 'Georgia', 'India', 'Indonesia', 'Iran', 'Iraq', 'Israel', 'Japan', 'Jordan', 'Kazakhstan', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Malaysia', 'Maldives', 'Mongolia', 'Myanmar', 'Nepal', 'North Korea', 'Oman', 'Pakistan', 'Palestine', 'Philippines', 'Qatar', 'Russia', 'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka', 'Syrian Arab Republic', 'Taiwan', 'Tajikistan', 'Thailand', 'Timor-Leste', 'Turkey', 'Turkmenistan', 'United Arab Emirates', 'Uzbekistan', 'Vietnam', 'Yemen', 'Syria'],
    'Europe': ['East Germany', 'North Macedonia', 'Yugoslavia', 'Serbia and Montenegro', 'Czechoslovakia', 'Czechia', 'USSR', 'Albania', 'Latvia', 'Andorra', 'Liechtenstein', 'Armenia', 'Lithuania', 'Austria', 'Luxembourg', 'Azerbaijan', 'Malta', 'Belarus', 'Moldova', 'Belgium', 'Monaco', 'Bosnia and Herzegovina', 'Montenegro', 'Bulgaria', 'Netherlands', 'Croatia', 'Norway', 'Cyprus', 'Poland', 'Czech Republic', 'Portugal', 'Denmark', 'Romania', 'Estonia', 'Russia', 'Finland', 'San Marino', 'Former Yugoslav Republic of Macedonia', 'Serbia', 'France', 'Slovakia', 'Georgia', 'Slovenia', 'Germany', 'Spain', 'Greece', 'Sweden', 'Hungary', 'Switzerland', 'Iceland', 'Ireland', 'Turkey', 'Italy', 'Ukraine', 'Kosovo', 'UK'],
    'North America': ['Bahamas', 'Guadeloupe', 'Cuba', 'The Bahamas', 'Bermuda', 'Canada', 'The Caribbean', 'Clipperton Island', 'Greenland', 'Mexico', 'Saint Pierre and Miquelon', 'Turks and Caicos Islands', 'USA', 'Belize', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras', 'Nicaragua', 'Panama', 'Dominican Republic', 'Haiti', 'Jamaica', 'Martinique', 'Netherlands Antilles', 'Puerto Rico'],
    'Oceania': ['Australia', 'Fiji', 'Kiribati', 'Marshall Islands', 'Micronesia', 'Nauru', 'New Zealand', 'Palau', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Tuvalu', 'Vanuatu', 'French Polynesia'],
    'South America': ['Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay', 'Bolivarian Republic of Venezuela', 'The Falkland Islands', 'South Georgia and the South Sandwich Islands', 'French Guiana', 'Venezuela'],
}

# Initialize continent stats with additional counts
continent_stats = {
    continent: {
        'film_data': [],  # Each entry will have Title, Year, tmdbID, and URL fields
        'country_counts': defaultdict(int),
        'director_counts': defaultdict(int),
        'actor_counts': defaultdict(int),
        'decade_counts': defaultdict(int),
        'genre_counts': defaultdict(int),
        'studio_counts': defaultdict(int),
        'language_counts': defaultdict(int)
    } for continent in CONTINENTS_COUNTRIES.keys()
}

# Track unmapped countries
unmapped_countries = set()

@dataclass
class MovieData:
    url: str  # Only identifier
    title: str  # For reference only
    year: str  # For reference only
    tmdb_id: Optional[str] = None
    rating_count: int = 0
    runtime: int = 0
    keywords: List[str] = None
    genres: List[str] = None

class RequestsSession:
    def __init__(self):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.session.get(url, **kwargs)

def normalize_text(text):
    return unicodedata.normalize('NFKC', str(text)).strip()

class MovieProcessor:
    def __init__(self):
        self.session = RequestsSession()
        self.whitelist = None
        self.whitelist_lookup = {}
        self.zero_reviews = None
        self.zero_reviews_lookup = {}
        self.load_whitelist()
        self.load_zero_reviews()
        
        # Update blacklist loading to include the Link column
        self.blacklist = pd.read_excel(BLACKLIST_PATH, header=0, names=['Title', 'Year', 'Reason', 'Link'], usecols=[0, 1, 2, 3])
        
        # Normalize titles and years in blacklist
        self.blacklist['Title'] = self.blacklist['Title'].apply(normalize_text)
        self.blacklist['Year'] = self.blacklist['Year'].astype(str).str.strip()
        # Fill empty links with empty string instead of None
        self.blacklist['Link'] = self.blacklist['Link'].fillna('')
        
        # Create a lookup dictionary for faster matching using URLs as keys
        self.blacklist_lookup = {}
        for idx, row in self.blacklist.iterrows():
            if row['Link']:  # Only store entries with URLs
                self.blacklist_lookup[row['Link']] = True
        
        self.added_movies: Set[Tuple[str, str]] = set()
        self.film_data: List[Dict] = []
        self.rejected_data: List[List] = []
        self.unfiltered_approved: List[List] = []
        self.unfiltered_denied: List[List] = []
        
        # Statistics tracking
        self.director_counts: Dict[str, int] = {}
        self.actor_counts: Dict[str, int] = {}
        self.decade_counts: Dict[str, int] = {}
        self.genre_counts: Dict[str, int] = {}
        self.studio_counts: Dict[str, int] = {}
        self.language_counts: Dict[str, int] = {}
        self.country_counts: Dict[str, int] = {}
        self.rating_counts: Dict[str, int] = {}
        self.mpaa_counts: Dict[str, int] = {}

    def load_whitelist(self):
        """Load and initialize the whitelist data."""
        try:
            # Read whitelist with explicit string type for Year column and include Information and Link columns
            self.whitelist = pd.read_excel(WHITELIST_PATH, header=0, names=['Title', 'Year', 'Information', 'Link'], dtype={'Year': str})
            
            # Normalize the data
            self.whitelist['Title'] = self.whitelist['Title'].apply(normalize_text)
            self.whitelist['Year'] = self.whitelist['Year'].astype(str).str.strip()
            # Fill empty links with empty string instead of None
            self.whitelist['Link'] = self.whitelist['Link'].fillna('')
            
            # Create a lookup dictionary for faster matching using URLs as keys
            self.whitelist_lookup = {}
            for idx, row in self.whitelist.iterrows():
                if row['Link']:  # Only store entries with URLs
                    try:
                        # Handle null/empty Information values by treating them as empty dictionaries
                        if pd.isna(row['Information']) or row['Information'] == '':
                            info = {}
                        else:
                            info = json.loads(row['Information']) if isinstance(row['Information'], str) else row['Information']
                        self.whitelist_lookup[row['Link']] = (info, idx, row['Link'])  # Added URL to tuple
                    except (json.JSONDecodeError, TypeError):
                        # If there's any error parsing, treat it as an empty dictionary
                        info = {}
                        self.whitelist_lookup[row['Link']] = (info, idx, row['Link'])  # Added URL to tuple
                        continue
                
        except FileNotFoundError:
            print_to_csv("whitelist.xlsx not found. Creating new file.")
            self.whitelist = pd.DataFrame(columns=['Title', 'Year', 'Information', 'Link'])
            self.whitelist.to_excel(WHITELIST_PATH, index=False)



    def load_zero_reviews(self):
        """Load and initialize the zero reviews data."""
        try:
            # Check if file exists
            if os.path.exists(ZERO_REVIEWS_PATH):
                # Read zero reviews with explicit string type for Year column
                self.zero_reviews = pd.read_excel(ZERO_REVIEWS_PATH, header=0, names=['Title', 'Year', 'Blank', 'Link'], dtype={'Year': str})
                
                # Normalize the data
                self.zero_reviews['Title'] = self.zero_reviews['Title'].apply(normalize_text)
                self.zero_reviews['Year'] = self.zero_reviews['Year'].astype(str).str.strip()
                self.zero_reviews['Link'] = self.zero_reviews['Link'].fillna('')
                self.zero_reviews['Blank'] = ''  # Ensure Blank column is empty
                            
                # Create a lookup dictionary for faster matching using URLs as keys
                self.zero_reviews_lookup = {}
                for idx, row in self.zero_reviews.iterrows():
                    if row['Link']:  # Only store entries with URLs
                        self.zero_reviews_lookup[row['Link']] = idx
                    
            else:
                self.zero_reviews = pd.DataFrame(columns=['Title', 'Year', 'Blank', 'Link'])
                self.zero_reviews.to_excel(ZERO_REVIEWS_PATH, index=False)
                
        except Exception as e:
            print_to_csv(f"ERROR loading zero reviews: {str(e)}")
            print_to_csv(f"ERROR type: {type(e)}")
            print_to_csv(f"ERROR details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            raise  # Re-raise the exception to see the full traceback

    def process_whitelist_info(self, info: Dict, film_url: str = None):
        """Process information from whitelist and update statistics."""
        if not isinstance(info, dict):
            print_to_csv("❌ Info is not a dictionary, skipping")
            return

        # Create film_data entry
        film_data = {
            'Title': info.get('Title'),
            'Year': info.get('Year'),
            'tmdbID': info.get('tmdbID')
        }

        # Add to film data
        self.film_data.append(film_data)

        # Process runtime category if we have runtime info
        runtime = info.get('Runtime')
        if runtime:
            categories = []
            if runtime < 91:
                categories.append('90_Minutes_or_Less')
            if runtime < 121:
                categories.append('120_Minutes_or_Less')
            if runtime > 179:
                categories.append('180_Minutes_or_Greater')
            if runtime > 239:
                categories.append('240_Minutes_or_Greater')
        
            for category in categories:
                if add_to_runtime_stats(category, info.get('Title'), info.get('Year'), info.get('tmdbID'), film_url):
                    self.update_runtime_statistics(info.get('Title'), info.get('Year'), info.get('tmdbID'), None, category)

        # Process MAX_MOVIES_5000 using centralized function
        if add_to_max_movies_5000(info.get('Title'), info.get('Year'), info.get('tmdbID'), film_url):
            
            # Update statistics for max_5000_stats
            # Directors
            for director in info.get('Directors', []):
                max_movies_5000_stats['director_counts'][director] += 1

            # Actors
            for actor in info.get('Actors', []):
                max_movies_5000_stats['actor_counts'][actor] += 1

            # Decade
            decade = info.get('Decade')
            if decade:
                max_movies_5000_stats['decade_counts'][decade] += 1

            # Genres
            for genre in info.get('Genres', []):
                max_movies_5000_stats['genre_counts'][genre] += 1

            # Studios
            for studio in info.get('Studios', []):
                max_movies_5000_stats['studio_counts'][studio] += 1

            # Languages
            for language in info.get('Languages', []):
                max_movies_5000_stats['language_counts'][language] += 1

            # Countries
            for country in info.get('Countries', []):
                max_movies_5000_stats['country_counts'][country] += 1

        # Process MPAA rating if we have it
        mpaa_rating = info.get('MPAA')
        if mpaa_rating and mpaa_rating in MPAA_RATINGS:
            if add_to_mpaa_stats(mpaa_rating, info.get('Title'), info.get('Year'), info.get('tmdbID'), film_url):
                self.update_statistics(mpaa_rating, film_url)

        # Process continent data if we have countries
        countries = info.get('Countries', [])
        if countries:
            for country in countries:
                country_mapped = False
                for continent, country_list in CONTINENTS_COUNTRIES.items():
                    if country in country_list:
                        if add_to_continent_stats(continent, info.get('Title'), info.get('Year'), info.get('tmdbID'), film_url):
                            self.update_continent_statistics(continent, film_url)
                        country_mapped = True
                        break
                if not country_mapped:
                    unmapped_countries.add(country)
                    # Store country with movie info for better tracking
                    if not hasattr(self, 'unmapped_countries_movies'):
                        self.unmapped_countries_movies = {}
                    if country not in self.unmapped_countries_movies:
                        self.unmapped_countries_movies[country] = []
                    movie_info = {
                        'title': info.get('Title', 'Unknown'),
                        'year': info.get('Year', 'Unknown'),
                        'url': film_url
                    }
                    if movie_info not in self.unmapped_countries_movies[country]:
                        self.unmapped_countries_movies[country].append(movie_info)
                    print_to_csv(f"DEBUG: {info.get('Title')} has unmapped country: {country}")


            
    def update_whitelist(self, film_title: str, release_year: str, movie_data: Dict, film_url: str = None) -> bool:
        """Update whitelist with movie data using URL as primary identifier."""
        if not film_url:
            return False  # Can't update whitelist without URL
            
        try:
            # Check if URL already exists in whitelist
            for row_idx, row in self.whitelist.iterrows():
                url = row.get('Link', '')
                if url == film_url:
                    # Update existing entry
                    self.whitelist.at[row_idx, 'Information'] = json.dumps(movie_data)
                    self.whitelist_lookup[film_url] = (movie_data, row_idx, film_url)
                    # Save to Excel
                    self.whitelist.to_excel(WHITELIST_PATH, index=False)
                    self.load_whitelist()  # Reload to ensure consistency
                    return True
            
            # Add new entry if URL not found
            new_row = pd.DataFrame([{
                'Title': film_title,
                'Year': release_year,
                'Information': json.dumps(movie_data),
                'Link': film_url
            }])
            self.whitelist = pd.concat([self.whitelist, new_row], ignore_index=True)
            self.whitelist_lookup[film_url] = (movie_data, len(self.whitelist) - 1, film_url)
            print_to_csv(f"🔗 Added link to whitelist for {film_title}")
            
            # Save to Excel
            self.whitelist.to_excel(WHITELIST_PATH, index=False)
            self.load_whitelist()  # Reload to ensure consistency
            return True
            
        except Exception as e:
            print_to_csv(f"Error updating whitelist: {str(e)}")
            return False

    def get_whitelist_data(self, film_title: str, release_year: str = None, film_url: str = None) -> Optional[Tuple[Dict, int]]:
        """Get the whitelist data for a movie if it exists. Only matches by URL."""
        if not film_url:
            return None, None  # Movie not in whitelist
            
        # Check if URL exists in whitelist lookup
        if film_url in self.whitelist_lookup:
            info, row_idx, _ = self.whitelist_lookup[film_url]
            try:
                # If info is a string, parse it as JSON
                if isinstance(info, str):
                    info = json.loads(info)
                elif not isinstance(info, dict):
                    print_to_csv(f"WARNING: Unexpected data type for {film_title}: {type(info)}")
                    return None, None
                    
                return info, row_idx
            except json.JSONDecodeError as e:
                print_to_csv(f"ERROR parsing whitelist data for {film_title}: {str(e)}")
                print_to_csv(f"Raw data: {info}")
                return None, None
            except Exception as e:
                print_to_csv(f"ERROR processing whitelist data for {film_title}: {str(e)}")
                return None, None
                
        return None, None  # Movie not in whitelist

    def fetch_tmdb_details(self, tmdb_id: str) -> Optional[Tuple[List[str], List[str]]]:
        movie_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=keywords"
        response = self.session.get(movie_url)

        if response.status_code == 200:
            movie_data = response.json()
            keywords = [keyword['name'] for keyword in movie_data['keywords']['keywords']]
            genre_elements = movie_data['genres']
            genres = [genre['name'] for genre in genre_elements]
            return keywords, genres
        else:
            if response.status_code == 401:
                print_to_csv("Check your API key.")
            return None

    def add_to_blacklist(self, film_title: str, release_year: str, reason: str, film_url: str = None) -> None:
        """Add a movie to the blacklist if it fails a criteria, including the link if available. Never patch missing links in existing entries."""
        if not film_url or not reason:
            return
            
        # Check if URL already exists in lookup
        if film_url in self.blacklist_lookup:
            return
            
        # Add new entry
        new_row = pd.DataFrame([[film_title, release_year, reason, film_url]],
                               columns=['Title', 'Year', 'Reason', 'Link'])
        self.blacklist = pd.concat([self.blacklist, new_row], ignore_index=True)
        self.blacklist_lookup[film_url] = True
        self.blacklist.to_excel(BLACKLIST_PATH, index=False)
        print_to_csv(f"⚫ {film_title} ({release_year}) added to blacklist {reason}")

    def is_whitelisted(self, film_title: str, release_year: str, film_url: str = None) -> bool:
        """Check if a movie is in the whitelist using ONLY URL as identifier."""
        if not film_url:
            return False
            
        # Only check URL match, never use title/year
        return film_url in self.whitelist_lookup

    def extract_runtime(self, driver, film_title: str) -> Optional[int]:
        try:
            runtime_element = driver.find_element(By.CSS_SELECTOR, 'p.text-link.text-footer')
            runtime_text = runtime_element.text
            match = re.search(r'(\d+)\s*min(?:s)?', runtime_text)
            if match:
                runtime = int(match.group(1))
                return runtime
        except Exception:
            pass
        
        print_to_csv(f"⚠️ No runtime found. Skipping {film_title}.")
        return None

    def process_runtime_category(self, film_title: str, release_year: str, tmdb_id: str, runtime: int, film_url: str = None, driver=None):
        """Process a movie's runtime category."""
        
        # Determine which categories this runtime falls into
        categories = []
        if runtime < 91:
            categories.append('90_Minutes_or_Less')
        if runtime < 121:
            categories.append('120_Minutes_or_Less')
        if runtime > 179:
            categories.append('180_Minutes_or_Greater')
        if runtime > 239:
            categories.append('240_Minutes_or_Greater')
                    
        # Add to each applicable category
        for category in categories:
            if add_to_runtime_stats(category, film_title, release_year, tmdb_id, film_url):
                self.update_runtime_statistics(film_title, release_year, tmdb_id, driver, category, film_url)

    def update_runtime_statistics(self, film_title: str, release_year: str, tmdb_id: str, driver, category: str, film_url: str = None):
        """Update statistics for the given runtime category."""
        # Get the most recently added movie from the runtime category's film_data
        if not runtime_stats[category]['film_data']:
            return
            
        latest_movie = runtime_stats[category]['film_data'][-1]
        film_title = latest_movie['Title']
        release_year = latest_movie['Year']
        film_url = latest_movie['Link']  # Get URL from the movie data
        
        # Get the movie info from whitelist using URL
        movie_info, _ = self.get_whitelist_data(None, None, film_url)
        if not movie_info:
            return
        
        # Update directors
        for director in movie_info.get('Directors', []):
            runtime_stats[category]['director_counts'][director] += 1

        # Update actors
        for actor in movie_info.get('Actors', []):
            runtime_stats[category]['actor_counts'][actor] += 1

        # Update decade
        decade = movie_info.get('Decade')
        if decade:
            runtime_stats[category]['decade_counts'][decade] += 1

        # Update genres
        for genre in movie_info.get('Genres', []):
            runtime_stats[category]['genre_counts'][genre] += 1

        # Update studios
        for studio in movie_info.get('Studios', []):
            runtime_stats[category]['studio_counts'][studio] += 1

        # Update languages
        for language in movie_info.get('Languages', []):
            runtime_stats[category]['language_counts'][language] += 1

        # Update countries
        for country in movie_info.get('Countries', []):
            runtime_stats[category]['country_counts'][country] += 1

    def update_statistics(self, mpaa_rating: str, film_url: str = None):
        """Update statistics for the given MPAA rating."""
        # Get the most recently added movie from the MPAA rating's film_data
            
        latest_movie = mpaa_stats[mpaa_rating]['film_data'][-1]
        film_title = latest_movie['Title']
        release_year = latest_movie['Year']
        film_url = latest_movie['Link']  # Get URL from the movie data
        
        # Get the movie info from whitelist using URL
        movie_info, _ = self.get_whitelist_data(None, None, film_url)
        if not movie_info:
            return
        
        # Update directors
        for director in movie_info.get('Directors', []):
            mpaa_stats[mpaa_rating]['director_counts'][director] += 1

        # Update actors
        for actor in movie_info.get('Actors', []):
            mpaa_stats[mpaa_rating]['actor_counts'][actor] += 1

        # Update decade
        decade = movie_info.get('Decade')
        if decade:
            mpaa_stats[mpaa_rating]['decade_counts'][decade] += 1

        # Update genres
        for genre in movie_info.get('Genres', []):
            mpaa_stats[mpaa_rating]['genre_counts'][genre] += 1

        # Update studios
        for studio in movie_info.get('Studios', []):
            mpaa_stats[mpaa_rating]['studio_counts'][studio] += 1

        # Update languages
        for language in movie_info.get('Languages', []):
            mpaa_stats[mpaa_rating]['language_counts'][language] += 1

        # Update countries
        for country in movie_info.get('Countries', []):
            mpaa_stats[mpaa_rating]['country_counts'][country] += 1

    def update_continent_statistics(self, continent: str, film_url: str = None):
        """Update statistics for the given continent."""
        if not film_url:
            print_to_csv("WARNING: No film URL provided for continent statistics update")
            return

        # Get the most recently added movie from the continent's film_data
        if not continent_stats[continent]['film_data']:
            return
            
        latest_movie = continent_stats[continent]['film_data'][-1]
        film_title = latest_movie['Title']
        release_year = latest_movie['Year']
        
        # Get the movie info from whitelist
        movie_info, _ = self.get_whitelist_data(film_title, release_year, film_url)
        if not movie_info:
            return

        # Update directors
        for director in movie_info.get('Directors', []):
            continent_stats[continent]['director_counts'][director] += 1

        # Update actors
        for actor in movie_info.get('Actors', []):
            continent_stats[continent]['actor_counts'][actor] += 1

        # Update decade
        decade = movie_info.get('Decade')
        if decade:
            continent_stats[continent]['decade_counts'][decade] += 1

        # Update genres
        for genre in movie_info.get('Genres', []):
            continent_stats[continent]['genre_counts'][genre] += 1

        # Update studios
        for studio in movie_info.get('Studios', []):
            continent_stats[continent]['studio_counts'][studio] += 1

        # Update languages
        for language in movie_info.get('Languages', []):
            continent_stats[continent]['language_counts'][language] += 1

        # Update countries
        for country in movie_info.get('Countries', []):
            continent_stats[continent]['country_counts'][country] += 1

    def update_max_movies_5000_statistics(self, film_title: str, release_year: str, tmdb_id: str, driver, film_url: str = None):
        """Update statistics for the given movie for MAX_MOVIES_5000."""
        if not film_url:
            print_to_csv("WARNING: No film URL provided for statistics update")
            return

        # Find the movie in film_data
        movie_data = next((movie for movie in max_movies_5000_stats['film_data'] 
                          if movie['Title'] == film_title and movie['Year'] == release_year), None)
        
        if not movie_data:
            return

        # Directors
        try:
            director_elements = driver.find_elements(By.CSS_SELECTOR, 'span.creatorlist a.contributor')
            for director in director_elements:
                director_name = director.text.strip()
                if director_name:
                    max_movies_5000_stats['director_counts'][director_name] += 1
        except Exception:
            pass

        # Actors
        try:
            actor_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-cast .text-sluglist a.text-slug.tooltip')
            for actor in actor_elements:
                actor_name = actor.text.strip()
                if actor_name:
                    max_movies_5000_stats['actor_counts'][actor_name] += 1
        except Exception:
            pass

        # Decade
        try:
            meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = meta_tag.get_attribute('content')
            if content and '(' in content and ')' in content:
                year = int(content.split('(')[-1].split(')')[0])
                decade = (year // 10) * 10
                max_movies_5000_stats['decade_counts'][decade] += 1
        except Exception:
            pass

        # Genres - Only get main genres, not microgenres
        try:
            genre_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-genres .text-sluglist a.text-slug[href*="/films/genre/"]')
            genres = []
            for genre in genre_elements:
                genre_name = genre.get_attribute('textContent').strip()
                if genre_name and not any(char in genre_name for char in ['…', 'Show All']):
                    genres.append(genre_name)
                    max_movies_5000_stats['genre_counts'][genre_name] += 1
            movie_data['Genres'] = genres
        except Exception:
            pass

        # Studios
        try:
            studio_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/studio/"]')
            studios = []
            for studio in studio_elements:
                studio_name = studio.get_attribute('textContent').strip()
                if studio_name:
                    studios.append(studio_name)
                    max_movies_5000_stats['studio_counts'][studio_name] += 1
            movie_data['Studios'] = studios
        except Exception:
            pass

        # Languages
        try:
            language_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/films/language/"]')
            languages = []
            for language in language_elements:
                language_name = language.get_attribute('textContent').strip()
                if language_name:
                    languages.append(language_name)
                    max_movies_5000_stats['language_counts'][language_name] += 1
            movie_data['Languages'] = languages
        except Exception:
            pass

        # Countries
        try:
            country_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/films/country/"]')
            countries = []
            for country in country_elements:
                country_name = country.get_attribute('textContent').strip()
                if country_name:
                    countries.append(country_name)
                    max_movies_5000_stats['country_counts'][country_name] += 1
            movie_data['Countries'] = countries
        except Exception:
            pass

    def is_blacklisted(self, film_title: str, release_year: str = None, film_url: str = None, driver = None) -> bool:
        """Check if a movie is blacklisted using URL as primary identifier."""
        if not film_url:
            return False
            
        # Check if URL exists in blacklist lookup
        return film_url in self.blacklist_lookup



    def add_to_zero_reviews(self, film_title: str, release_year: str, film_url: str):
        """Add a movie to the zero reviews list using URL as primary identifier."""
        if not film_url:
            return
            
        try:
            # Check if URL already exists in lookup
            if film_url in self.zero_reviews_lookup:
                return
                
            # Create new row
            new_row = pd.DataFrame([{
                'Title': film_title,
                'Year': release_year,
                'Blank': '',
                'Link': film_url
            }])
            # Add to DataFrame
            self.zero_reviews = pd.concat([self.zero_reviews, new_row], ignore_index=True)
            # Add to lookup
            self.zero_reviews_lookup[film_url] = len(self.zero_reviews) - 1
            # Save to Excel
            self.zero_reviews.to_excel(ZERO_REVIEWS_PATH, index=False)
                
        except Exception as e:
            print_to_csv(f"ERROR adding to zero reviews: {str(e)}")

    def is_zero_reviews(self, film_title: str, release_year: str, film_url: str) -> bool:
        """Check if a movie is in the zero reviews list using URL as primary identifier."""
        if not film_url:
            return False
            
        try:
                        # Check if URL exists in zero reviews lookup
            if film_url in self.zero_reviews_lookup:
                # 1 in 10 chance to remove the entry after finding it
                if random.random() < (1/10):
                    # Get the index from lookup
                    idx_to_remove = self.zero_reviews_lookup[film_url]
                    # Remove the row
                    self.zero_reviews = self.zero_reviews.drop(idx_to_remove)
                    # Remove from lookup
                    del self.zero_reviews_lookup[film_url]
                    # Save the updated DataFrame
                    self.zero_reviews.to_excel(ZERO_REVIEWS_PATH, index=False)
                    print_to_csv(f"🗑️  Removed {film_title} from zero reviews list")
                return True
            return False
                
        except Exception as e:
            print_to_csv(f"ERROR checking zero reviews: {str(e)}")
            return False

def setup_webdriver() -> webdriver.Firefox:
    options = Options()
    options.headless = True
    options.set_preference("permissions.default.image", 2)  # Disable images
    options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
    options.set_preference("browser.display.use_document_fonts", 0)
    options.set_preference("browser.display.document_color_use", 2)
    
    # Add these preferences to prevent random downloads
    options.set_preference("browser.download.folderList", 2)  # Use custom download location
    options.set_preference("browser.download.manager.showWhenStarting", False)  # Don't show download manager
    options.set_preference("browser.download.dir", os.path.join(BASE_DIR, "downloads"))  # Set download directory
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/html,text/plain")  # Don't ask to save HTML files
    options.set_preference("browser.helperApps.alwaysAsk.force", False)  # Don't force asking
    options.set_preference("browser.download.manager.alertOnEXEOpen", False)  # Don't alert on exe downloads
    options.set_preference("browser.download.manager.focusWhenStarting", False)  # Don't focus download manager
    options.set_preference("browser.download.manager.useWindow", False)  # Don't use window for downloads
    options.set_preference("browser.download.manager.showAlertOnComplete", False)  # Don't show alert when complete
    options.set_preference("browser.download.manager.closeWhenDone", True)  # Close download manager when done
    
    # Add these optimizations:
    options.set_preference("javascript.enabled", True)  # Keep JS enabled but optimize
    options.set_preference("network.http.connection-timeout", 30)  # Reduce timeout
    options.set_preference("network.http.max-connections-per-server", 10)  # Limit connections
    options.set_preference("browser.cache.disk.enable", True)  # Enable disk cache
    options.set_preference("browser.cache.memory.enable", True)  # Enable memory cache
    
    service = Service()
    return webdriver.Firefox(service=service, options=options)

def format_time(seconds):
    """Format seconds into hours, minutes, seconds string"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def extract_mpaa_rating(driver) -> Optional[str]:
    """Extract the MPAA rating from the movie's page if the country is USA."""
    try:
        # Wait for the page to be fully loaded
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.release-country-list')))
        
        # Use JavaScript to extract all country data
        js_script = """
        const countries = Array.from(document.querySelectorAll('.release-country'));
        return countries.map(country => {
            const name = country.querySelector('.name')?.textContent?.trim() || '';
            const rating = country.querySelector('.release-certification-badge .label')?.textContent?.trim() || '';
            return { name, rating };
        });
        """
        
        country_data = driver.execute_script(js_script)
        
        # Collect all USA ratings
        usa_ratings = []
        for data in country_data:
            name = data['name']
            rating = data['rating']
            
            if name == "USA" and rating:
                usa_ratings.append(rating)
        
        # If no USA ratings found, return None
        if not usa_ratings:
            return None
        
        # Check if ANY USA rating exists and is not unrated
        # If there are any rated releases, use the most appropriate one
        rating_map = {
            'R': 'R',
            'PG-13': 'PG-13',
            'PG': 'PG',
            'G': 'G',
            'NC-17': 'NC-17',
            'X': 'NC-17',  # Historical rating
            'M': 'PG',     # Historical rating
            'GP': 'PG',    # Historical rating
        }
        
        # First, look for any rated releases (non-NR)
        for rating in usa_ratings:
            if rating.upper() not in ['NR', 'NOT RATED', 'UNRATED']:
                if rating in rating_map:
                    return rating_map[rating]
        
        # Only return NR if ALL USA releases were unrated
        # This means the movie was never rated by the MPAA in the USA
        return 'NR'
        
    except Exception as e:
        # Only print error if it's not a NoSuchElementException
        if not isinstance(e, NoSuchElementException):
            print_to_csv(f"Error extracting MPAA rating: {str(e)}")
        return None

# Initialize stats for MAX_MOVIES_5000
max_movies_5000_stats = {
    'film_data': [],  # Each entry will have Title, Year, tmdbID, and URL fields
    'director_counts': defaultdict(int),
    'actor_counts': defaultdict(int),
    'decade_counts': defaultdict(int),
    'genre_counts': defaultdict(int),
    'studio_counts': defaultdict(int),
    'language_counts': defaultdict(int),
    'country_counts': defaultdict(int)
}

def add_to_max_movies_5000(film_title: str, release_year: str, tmdb_id: str, film_url: str) -> bool:
    """
    Centralized function to add a movie to max_movies_5000_stats if it's not already present.
    Returns True if the movie was added, False if it was already present or if we've reached the limit.
    """

    if not film_url:
        return False

    # Check if movie already exists by URL
    if any(movie['Link'] == film_url for movie in max_movies_5000_stats['film_data']):
        return False

    # Check if we've reached the limit
    if len(max_movies_5000_stats['film_data']) >= MAX_MOVIES_5000:
        return False

    # Add the movie
    max_movies_5000_stats['film_data'].append({
        'Title': film_title,  # For reference only
        'Year': release_year,  # For reference only
        'tmdbID': tmdb_id,
        'Link': film_url  # Primary identifier
    })
    return True

def add_to_continent_stats(continent: str, film_title: str, release_year: str, tmdb_id: str, film_url: str) -> bool:
    """
    Add a movie to the continent statistics.
    
    Args:
        continent: The continent to add the movie to
        film_title: The title of the movie (for reference only)
        release_year: The release year of the movie (for reference only)
        tmdb_id: The TMDB ID of the movie
        film_url: The URL of the movie (primary identifier)
        
    Returns:
        bool: True if the movie was added, False otherwise
    """
    # Check if movie already exists
    if any(movie['Title'] == film_title and movie['Year'] == release_year 
           for movie in continent_stats[continent]['film_data']):
        return False

    # Determine the max limit based on the continent
    max_limit = (
        MAX_MOVIES_AFRICA if continent == 'Africa' else
        MAX_MOVIES_OCEANIA if continent == 'Oceania' else
        MAX_MOVIES_SOUTH_AMERICA if continent == 'South America' else
        MAX_MOVIES_CONTINENT
    )

    # Check if we've reached the limit
    if len(continent_stats[continent]['film_data']) >= max_limit:
        return False

    # Add the movie
    continent_stats[continent]['film_data'].append({
        'Title': film_title,
        'Year': release_year,
        'tmdbID': tmdb_id,
        'Link': film_url
    })
    return True

def add_to_runtime_stats(category: str, film_title: str, release_year: str, tmdb_id: str, film_url: str) -> bool:
    """
    Add a movie to the runtime statistics.
    
    Args:
        category: The runtime category to add the movie to
        film_title: The title of the movie (for reference only)
        release_year: The release year of the movie (for reference only)
        tmdb_id: The TMDB ID of the movie
        film_url: The URL of the movie (primary identifier)
        
    Returns:
        bool: True if the movie was added, False otherwise
    """
    # Check if movie already exists
    if any(movie['Title'] == film_title and movie['Year'] == release_year 
           for movie in runtime_stats[category]['film_data']):
        return False

    # Determine the max limit based on the category
    max_limit = (
        MAX_180 if category == '180_Minutes_or_Greater' else
        MAX_240 if category == '240_Minutes_or_Greater' else
        MAX_MOVIES_RUNTIME
    )

    # Check if we've reached the limit
    if len(runtime_stats[category]['film_data']) >= max_limit:
        return False

    # Add the movie
    runtime_stats[category]['film_data'].append({
        'Title': film_title,
        'Year': release_year,
        'tmdbID': tmdb_id,
        'Link': film_url
    })
    return True

def add_to_mpaa_stats(rating: str, film_title: str, release_year: str, tmdb_id: str, film_url: str) -> bool:
    """
    Add a movie to the MPAA rating statistics.
    
    Args:
        rating: The MPAA rating to add the movie to
        film_title: The title of the movie (for reference only)
        release_year: The release year of the movie (for reference only)
        tmdb_id: The TMDB ID of the movie
        film_url: The URL of the movie (primary identifier)
        
    Returns:
        bool: True if the movie was added, False otherwise
    """
    # Check if movie already exists
    if any(movie['Title'] == film_title and movie['Year'] == release_year 
           for movie in mpaa_stats[rating]['film_data']):
        return False

    # Determine the max limit based on the rating
    max_limit = (
        MAX_MOVIES_G if rating == 'G' else
        MAX_MOVIES_NC17 if rating == 'NC-17' else
        MAX_MOVIES_MPAA
    )

    # Check if we've reached the limit
    if len(mpaa_stats[rating]['film_data']) >= max_limit:
        return False

    # Add the movie
    mpaa_stats[rating]['film_data'].append({
        'Title': film_title,
        'Year': release_year,
        'tmdbID': tmdb_id,
        'Link': film_url
    })
    return True

class LetterboxdScraper:
    def __init__(self):
        self.driver = setup_webdriver()
        self.processor = MovieProcessor()
        self.base_url = 'https://letterboxd.com/films/by/popular/'
        self.total_titles = 0
        self.processed_titles = 0
        self.valid_movies_count = 0
        self.page_number = 1
        self.start_time = time.time()
        self.unknown_continent_films = []  # Initialize the list for unknown continent films
        self.top_movies_count = 0  # Track the number of movies added to the top 5000 list
        self.rejected_movies_count = 0  # Add counter for rejected movies
        print_to_csv("Initialized Letterboxd Scraper.")

    def process_movie_data(self, info, film_title=None, film_url=None):
        """Process movie data from the whitelist using URL as the primary identifier."""
        try:
            if not info or not film_url:
                return False
                
            film_title = info.get('Title')  # Only for display purposes
            release_year = info.get('Year')  # Only for display purposes
            tmdb_id = info.get('tmdbID')  # Only for display purposes
                        
            # Process using URL as primary identifier
            if self.processor.is_whitelisted(None, None, film_url):
                # If info is empty or incomplete, collect fresh data
                required_fields = [
                    'Title', 'Year', 'Runtime', 'RatingCount',
                    'Languages', 'Countries', 'Directors', 'Genres', 'Studios', 'Actors'
                ]
                missing_fields = [field for field in required_fields if not info.get(field)]
                if not info or info == {} or missing_fields:
                    try:
                        self.driver.get(film_url)
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[property=\"og:title\"]'))
                        )
                        #time.sleep(random.uniform(1.0, 1.5))
                        
                        # Extract basic info
                        meta_tag = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                        release_year = None
                        if meta_tag:
                            release_year_content = meta_tag.get_attribute('content')
                            release_year = release_year_content.split('(')[-1].strip(')')

                        # Extract rating count
                        rating_count = 0
                        try:
                            page_source = self.driver.page_source
                            match = re.search(r'ratingCount":(\d+)', page_source)
                            if match:
                                rating_count = int(match.group(1))
                            
                            # Extract TMDB ID from body tag
                            tmdb_match = re.search(r'data-tmdb-id="(\d+)"', page_source)
                            if tmdb_match:
                                tmdb_id = tmdb_match.group(1)
                            else:
                                print_to_csv(f"No TMDB ID found in page source for {film_title}")
                        except Exception as e:
                            print_to_csv(f"Error extracting rating count or TMDB ID: {str(e)}")
                        
                        # Extract runtime
                        runtime = None
                        try:
                            runtime_element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.text-link.text-footer'))
                            )
                            runtime_text = runtime_element.text
                            match = re.search(r'(\d+)\s*min(?:s)?', runtime_text)
                            if match:
                                runtime = int(match.group(1))
                        except Exception as e:
                            print_to_csv(f"Error extracting runtime: {str(e)}")
                        
                        # Extract directors
                        movie_directors = []
                        try:
                            director_elements = self.driver.find_elements(By.CSS_SELECTOR, 'span.creatorlist a.contributor span.prettify')
                            for director in director_elements:
                                director_name = director.text.strip()
                                if director_name:
                                    movie_directors.append(director_name)
                        except Exception:
                            pass
                        
                        # Extract actors
                        movie_actors = []
                        try:
                            actor_elements = self.driver.find_elements(By.CSS_SELECTOR, '#tab-cast .text-sluglist a.text-slug.tooltip')
                            for actor in actor_elements:
                                actor_name = actor.text.strip()
                                if actor_name:
                                    movie_actors.append(actor_name)
                        except Exception as e:
                            print_to_csv(f"Error extracting actors: {str(e)}")
                        
                        # Extract genres
                        movie_genres = []
                        try:
                            genre_elements = self.driver.find_elements(By.CSS_SELECTOR, '#tab-genres .text-sluglist a.text-slug[href*="/films/genre/"]')
                            for genre in genre_elements:
                                genre_name = genre.get_attribute('textContent').strip()
                                if genre_name and not any(char in genre_name for char in ['…', 'Show All']):
                                    movie_genres.append(genre_name)
                        except Exception as e:
                            print_to_csv(f"Error extracting genres: {str(e)}")
                        
                        # Extract studios
                        movie_studios = []
                        try:
                            studio_elements = self.driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/studio/"]')
                            for studio in studio_elements:
                                studio_name = studio.get_attribute('textContent').strip()
                                if studio_name:
                                    movie_studios.append(studio_name)
                        except Exception as e:
                            print_to_csv(f"Error extracting studios: {str(e)}")
                        
                        # Extract languages
                        movie_languages = set()
                        try:
                            headings = self.driver.find_elements(By.CSS_SELECTOR, '#tab-details h3')
                            for heading in headings:
                                span = heading.find_element(By.TAG_NAME, 'span')
                                heading_text = span.get_attribute('textContent').strip() if span else heading.get_attribute('textContent').strip()
                                
                                if any(lang in heading_text for lang in ["Language", "Primary Language", "Languages", "Primary Languages"]):
                                    try:
                                        sluglist = heading.find_element(By.XPATH, "following-sibling::div[contains(@class, 'text-sluglist')]")
                                        if sluglist:
                                            p_tag = sluglist.find_element(By.TAG_NAME, 'p')
                                            language_elements = p_tag.find_elements(By.CSS_SELECTOR, 'a.text-slug[href*="/films/language/"]')
                                            for language in language_elements:
                                                language_name = language.get_attribute('textContent').strip()
                                                if language_name:
                                                    movie_languages.add(language_name)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        
                        # Extract countries
                        movie_countries = []
                        try:
                            country_elements = self.driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/films/country/"]')
                            for country in country_elements:
                                country_name = country.get_attribute('textContent').strip()
                                if country_name:
                                    movie_countries.append(country_name)
                        except Exception as e:
                            print_to_csv(f"Error extracting countries: {str(e)}")
                        
                        # Extract MPAA rating
                        mpaa_rating = None
                        try:
                            mpaa_rating = extract_mpaa_rating(self.driver)
                        except Exception as e:
                            print_to_csv(f"Error extracting MPAA rating: {str(e)}")
                        
                        # Create updated movie data
                        info = {
                            "Title": film_title,
                            "Year": release_year,
                            "tmdbID": tmdb_id,
                            "MPAA": mpaa_rating,
                            "Runtime": runtime,
                            "RatingCount": rating_count,
                            "Languages": list(movie_languages),
                            "Countries": movie_countries,
                            "Decade": (int(release_year) // 10) * 10 if release_year else None,
                            "Directors": movie_directors,
                            "Genres": movie_genres,
                            "Studios": movie_studios,
                            "Actors": movie_actors
                        }
                        
                        # Update whitelist with fresh data
                        if self.processor.update_whitelist(film_title, release_year, info, film_url):
                            print_to_csv(f"📝 Updated whitelist data for {film_title}")
                    except Exception as e:
                        print_to_csv(f"Error collecting fresh data for {film_title}: {str(e)}")
                        self.processor.rejected_data.append([film_title, release_year, None, f'Error collecting data: {str(e)}'])
                        return False
                
                # Process the whitelist information regardless of MAX_MOVIES_5000 limit
                self.processor.process_whitelist_info(info, film_url)
                self.valid_movies_count += 1
                print_to_csv(f"✅ Processed whitelist data for {film_title} ({self.valid_movies_count}/{MAX_MOVIES})")
                
                # 2% chance to clear the whitelist data for random auditing
                if random.random() < 0.02:
                    self.processor.update_whitelist(film_title, release_year, {}, film_url)
                    print_to_csv(f"🤓 Random data audit scheduled for {film_title} ({release_year})")
                
                return True
            
            # If not whitelisted, process as a new movie
            self.process_approved_movie(film_title, release_year, tmdb_id, film_url, 'unfiltered')
            return True
                
        except Exception as e:
            print_to_csv(f"Error processing movie data: {str(e)}")
            print_to_csv(f"Error type: {type(e)}")
            print_to_csv(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return False

    def scrape_movies(self):
        seen_titles = set()  # <-- Add this at the start of the method

        while self.valid_movies_count < MAX_MOVIES:
            # Safety check: if we've tried too many pages without success, save and exit
            if self.page_number > 1000:  # Arbitrary high limit
                print_to_csv(f"⚠️ Reached page {self.page_number}, which seems too high. Saving progress and stopping.")
                self.save_results()
                break
                
            # Construct the URL for the current page
            url = f'{self.base_url}page/{self.page_number}/'
            print_to_csv(f"\nLoading page {self.page_number}: {url}")
            
            # Send a GET request to the URL with retry mechanism
            page_retries = 20
            for retry in range(page_retries):
                try:
                    self.driver.get(url)
                    
                    # Check if page loaded successfully
                    try:
                        page_title = self.driver.title
                        print_to_csv(f"Page loaded: {page_title}")
                        
                        # Check if we got redirected to an error page
                        if "not found" in page_title.lower() or "error" in page_title.lower():
                            print_to_csv(f"❌ Page {self.page_number} appears to be an error page: {page_title}")
                            self.page_number += 1
                            continue
                            
                    except Exception as e:
                        print_to_csv(f"Warning: Could not get page title: {str(e)}")
                    
                    # Wait for the page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'li.posteritem'))
                    )
                    
                    # Additional check: verify we're on the right page
                    current_url = self.driver.current_url
                    if current_url != url and "page" not in current_url:
                        print_to_csv(f"⚠️ Page redirected from {url} to {current_url}")
                    
                    break
                except Exception as e:
                    if retry == page_retries - 1:
                        print_to_csv(f"❌ Failed to load page after {page_retries} attempts: {str(e)}")
                        # Try to move to next page instead of crashing
                        print_to_csv(f"Moving to next page and continuing...")
                        self.page_number += 1
                        continue
                    print_to_csv(f"Retry {retry + 1}/{page_retries} loading page {self.page_number}: {str(e)}")
                    time.sleep(2)
                    
                    # Additional error handling for network issues
                    if "timeout" in str(e).lower() or "connection" in str(e).lower():
                        print_to_csv(f"⚠️ Network issue detected, waiting longer before retry...")
                        time.sleep(10)  # Wait longer for network issues
            
            #time.sleep(random.uniform(1.0, 1.5))
                    
            # Find all film containers with retry mechanism
            film_containers = []
            container_retries = 25  # Maximum number of retries
            for retry in range(container_retries):
                try:
                    film_containers = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.posteritem'))
                    )
                    
                    # Log what we found
                    print_to_csv(f"Found {len(film_containers)} film containers on attempt {retry + 1}")
                    
                    # Check if we have a reasonable number of containers (not necessarily exactly 72)
                    if len(film_containers) >= 50:  # Allow some flexibility
                        print_to_csv(f"✅ Found {len(film_containers)} containers, proceeding...")
                        break
                    else:
                        print_to_csv(f"Found only {len(film_containers)} containers, retrying... (Attempt {retry + 1}/{container_retries})")
                        time.sleep(5)  # Wait longer between retries
                        self.driver.refresh()  # Refresh the page
                        time.sleep(2)  # Wait for refresh
                except Exception as e:
                    if retry == container_retries - 1:
                        print_to_csv(f"❌ Failed to find film containers after {container_retries} attempts: {str(e)}")
                        print_to_csv(f"Moving to next page and continuing...")
                        self.page_number += 1
                        continue
                    print_to_csv(f"Retry {retry + 1}/{container_retries} finding film containers: {str(e)}")
                    time.sleep(5)
                    self.driver.refresh()
                    time.sleep(2)
                    
                    # Additional error handling for specific issues
                    if "timeout" in str(e).lower():
                        print_to_csv(f"⚠️ Timeout detected, waiting longer before retry...")
                        time.sleep(10)  # Wait longer for timeouts
            
            if len(film_containers) < 30:  # More flexible threshold
                print_to_csv(f"❌ Found only {len(film_containers)} film containers, which seems too low")
                print_to_csv(f"Moving to next page and continuing...")
                self.page_number += 1
                continue

            print_to_csv(f"\n{f' Page {self.page_number} ':=^100}")

            # First collect all film data from the page
            film_data_list = []
            for container in film_containers:
                try:
                    # Get the anchor element first - look specifically for film links
                    anchor = container.find_element(By.CSS_SELECTOR, 'a[href*="/film/"]')
                    film_url = anchor.get_attribute('href')
                    
                    # Try multiple methods to get the film title with fallbacks
                    film_title = None
                    
                    # Method 1: Try data-item-full-display-name first (most reliable)
                    film_title = container.get_attribute('data-item-full-display-name')
                    
                    # Method 2: If empty, try data-item-name
                    if not film_title:
                        film_title = container.get_attribute('data-item-name')
                        if film_title:
                            # Try to get year from data-item-full-display-name if available
                            full_name = container.get_attribute('data-item-full-display-name')
                            if full_name and '(' in full_name and ')' in full_name:
                                film_title = full_name
                    
                    # Method 3: If still empty, try anchor title attribute
                    if not film_title:
                        anchor_title = anchor.get_attribute('title')
                        if anchor_title:
                            # Remove rating from title (e.g., "Barbie 3.75" -> "Barbie")
                            # Split by space and take everything except the last part if it's a rating
                            title_parts = anchor_title.split(' ')
                            if len(title_parts) > 1 and title_parts[-1].replace('.', '').replace(',', '').isdigit():
                                # Last part is a rating, remove it
                                film_title = ' '.join(title_parts[:-1])
                            else:
                                # No rating, use the full title
                                film_title = anchor_title
                    
                    # Method 4: If still empty, try getting from the img alt attribute
                    if not film_title:
                        try:
                            img = container.find_element(By.CSS_SELECTOR, 'img')
                            img_alt = img.get_attribute('alt')
                            if img_alt and 'poster' not in img_alt.lower():
                                film_title = img_alt.replace(' poster', '').strip()
                        except:
                            pass
                    
                    # Method 5: Extract from URL as last resort
                    if not film_title and film_url:
                        # Extract title from URL: /film/title-name/
                        url_parts = film_url.split('/film/')
                        if len(url_parts) > 1:
                            title_from_url = url_parts[1].rstrip('/')
                            # Convert hyphens to spaces and capitalize
                            film_title = title_from_url.replace('-', ' ').replace('_', ' ').title()
                    
                    if film_title and film_url:
                        # Clean up the title
                        film_title = film_title.strip()
                        
                        # Extract year from title if possible
                        release_year = None
                        if '(' in film_title and ')' in film_title:
                            release_year = film_title.split('(')[-1].split(')')[0].strip()
                        
                        # Just check if title exists in blacklist, don't try to get release year yet
                        is_blacklisted = self.processor.is_blacklisted(None, None, film_url, None)  # Pass None as driver
                        film_data_list.append({
                            'title': film_title,
                            'url': film_url,
                            'is_blacklisted': is_blacklisted,
                            'release_year': release_year
                        })
                    else:
                        print_to_csv(f"Missing data for movie - Title: {film_title}, URL: {film_url}")
                        # Debug: show what attributes are available
                        try:
                            debug_info = f"Available data: data-item-full-display-name='{container.get_attribute('data-item-full-display-name')}', data-item-name='{container.get_attribute('data-item-name')}', anchor-title='{anchor.get_attribute('title')}'"
                            print_to_csv(f"   Debug: {debug_info}")
                        except:
                            pass
                        self.processor.rejected_data.append([film_title, None, None, 'Missing title or URL'])
                except Exception as e:
                    print_to_csv(f"Error collecting film data: {str(e)}")
                    continue

            print_to_csv(f"Collected {len(film_data_list)} movies from page {self.page_number}")
            
            # Log some sample titles for debugging
            if film_data_list:
                sample_titles = [f"{item['title']} ({item['release_year']})" for item in film_data_list[:3]]
                print_to_csv(f"Sample titles from page: {', '.join(sample_titles)}")
            
            if not film_data_list:
                print_to_csv("No valid film data collected. Moving to next page...")
                self.page_number += 1
                continue

            # Now process each film one by one
            for film_data in film_data_list:
                if self.valid_movies_count >= MAX_MOVIES:
                    print_to_csv(f"✅ {MAX_MOVIES} unique movies successfully scraped. Stopping scraping.")
                    return

                film_title = film_data['title']
                film_url = film_data['url']
                release_year = film_data['release_year']

                # Get whitelist data using URL only
                whitelist_info, _ = self.processor.get_whitelist_data(None, None, film_url)

                # After processing, add the title to seen_titles for reference only
                seen_titles.add(film_title.lower())

                # Increment total_titles for each movie we process, including blacklisted ones
                self.total_titles += 1
                
                # Check if movie is in zero reviews list (only for pages 31 and onward)
                if self.page_number >= 31 and self.processor.is_zero_reviews(film_title, release_year, film_url):
                    print_to_csv(f"📊 {film_title} is in zero reviews list. Skipping.")
                    self.processor.rejected_data.append([film_title, release_year, None, 'Zero reviews'])
                    self.rejected_movies_count += 1  # Increment rejected counter
                    continue
                
                # Handle blacklisted movies first
                if film_data['is_blacklisted']:
                    print_to_csv(f"❌ {film_title} was not added due to being blacklisted.")
                    self.processor.rejected_data.append([film_title, release_year, None, 'Blacklisted'])
                    self.rejected_movies_count += 1  # Increment rejected counter
                    continue
                
                # First check for exact matches in whitelist
                if whitelist_info:
                    self.process_movie_data(whitelist_info, film_title, film_url)
                    # Check again after whitelist processing
                    if self.valid_movies_count >= MAX_MOVIES:
                        print_to_csv(f"✅ {MAX_MOVIES} unique movies successfully scraped. Stopping scraping.")
                        return
                    continue
                                
                # Get initial movie data without full scrape
                movie_retries = 20  # Maximum number of retries for individual movie pages
                for retry in range(movie_retries):
                    try:
                        self.driver.get(film_url)
                        
                        # Check if we got redirected to an error page
                        try:
                            page_title = self.driver.title
                            if "not found" in page_title.lower() or "error" in page_title.lower():
                                print_to_csv(f"⚠️ Movie page appears to be an error page: {page_title}")
                                break  # Skip to next movie
                        except:
                            pass
                        
                        # Only wait for the page source to be available, not for any specific element
                        page_source = self.driver.page_source
                        # Extract rating count as fast as possible
                        match = re.search(r'ratingCount":(\d+)', page_source)
                        rating_count = int(match.group(1)) if match else 0

                        if rating_count == 0:
                            # Extract title/year if not already known
                            # Try to get year from meta tag if not in film_data_list
                            if not release_year:
                                try:
                                    meta_tag = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                                    if meta_tag:
                                        release_year_content = meta_tag.get_attribute('content')
                                        release_year = release_year_content.split('(')[-1].strip(')')
                                except Exception:
                                    release_year = None
                            print_to_csv(f"📊 {film_title} has no reviews. Adding to zero reviews list.")
                            self.processor.add_to_zero_reviews(film_title, release_year, film_url)
                            self.processor.rejected_data.append([film_title, release_year, None, 'Zero reviews'])
                            self.rejected_movies_count += 1
                            break  # Skip to next movie
                        elif rating_count < MIN_RATING_COUNT:
                            # Not enough reviews, skip immediately
                            print_to_csv(f"❌ {film_title} was not added due to insufficient ratings: {rating_count} ratings.")
                            self.processor.rejected_data.append([film_title, release_year, None, 'Insufficient ratings (< 1000)'])
                            self.rejected_movies_count += 1
                            break  # Skip to next movie
                        # If here, rating_count >= 1000, proceed as before
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[property=\"og:title\"]'))
                        )
                        meta_tag = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                        release_year = None
                        if meta_tag:
                            release_year_content = meta_tag.get_attribute('content')
                            release_year = release_year_content.split('(')[-1].strip(')')
                        # Extract TMDB ID from body tag
                        tmdb_id = None
                        try:
                            tmdb_match = re.search(r'data-tmdb-id="(\d+)"', page_source)
                            if tmdb_match:
                                tmdb_id = tmdb_match.group(1)
                        except Exception as e:
                            print_to_csv(f"Error extracting TMDB ID: {str(e)}")
                        # Extract runtime
                        runtime = None
                        try:
                            runtime_element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.text-link.text-footer'))
                            )
                            runtime_text = runtime_element.text
                            match = re.search(r'(\d+)\s*min(?:s)?', runtime_text)
                            if match:
                                runtime = int(match.group(1))
                                if runtime < MIN_RUNTIME:
                                    print_to_csv(f"❌ {film_title} was not added due to insufficient runtime: {runtime} minutes.")
                                    self.processor.rejected_data.append([film_title, release_year, None, 'Insufficient runtime (< 40 minutes)'])
                                    self.processor.add_to_blacklist(film_title, release_year, 'Insufficient runtime (< 40 minutes)', film_url)
                                    self.rejected_movies_count += 1
                                    break  # Skip to next movie
                        except Exception as e:
                            runtime = None
                            print_to_csv(f"Error extracting runtime for {film_title}: {str(e)}")
                        if runtime is None:
                            runtime_retries = 5
                            print_to_csv(f"⚠️ {film_title} skipped due to missing runtime")
                            self.rejected_movies_count += 1  # Increase rejected movie count
                            if retry < runtime_retries - 1:
                                print_to_csv(f"Retrying... (Attempt {retry + 1}/{movie_retries})")
                                time.sleep(2)
                                continue
                        # If we get here, the movie passed all checks
                        # Create movie data dictionary
                        movie_data = {
                            'Title': film_title,
                            'Year': release_year,
                            'tmdbID': tmdb_id,
                            'MPAA': None,  # We don't need MPAA for processing
                            'Runtime': runtime,
                            'RatingCount': rating_count,
                            'Languages': [],
                            'Countries': [],
                            'Decade': (int(release_year) // 10) * 10 if release_year else None,
                            'Directors': [],
                            'Genres': [],
                            'Studios': [],
                            'Actors': [],
                            'Link': film_url
                        }
                        # Process the movie data
                        self.process_movie_data(movie_data, film_title, film_url)
                        # Check again after processing
                        if self.valid_movies_count >= MAX_MOVIES:
                            print_to_csv(f"✅ {MAX_MOVIES} unique movies successfully scraped. Stopping scraping.")
                            return
                        break  # Break out of retry loop since we successfully processed the movie
                    except Exception as e:
                        if retry == movie_retries - 1:
                            print_to_csv(f"❌ Failed to process movie after {movie_retries} attempts: {str(e)}")
                            self.processor.rejected_data.append([film_title, release_year, None, f'Error: {str(e)}'])
                            self.rejected_movies_count += 1  # Increment rejected counter
                            break  # Skip to next movie
                        else:
                            print_to_csv(f"Retry {retry + 1}/{movie_retries} processing movie: {str(e)}")
                            time.sleep(2)
                            continue
            
            self.page_number += 1



    def process_approved_movie(self, film_title: str, release_year: str, tmdb_id: str, film_url: str, approval_type: str):
        """Process a movie that has been approved."""
        try:
            # Extract TMDB ID from page source
            try:
                page_source = self.driver.page_source
                tmdb_match = re.search(r'data-tmdb-id="(\d+)"', page_source)
                if tmdb_match:
                    tmdb_id = tmdb_match.group(1)
                else:
                    print_to_csv(f"❌ {film_title} was not added due to missing TMDB ID.")
                    self.processor.rejected_data.append([film_title, release_year, None, 'Missing TMDB ID'])
                    self.processor.unfiltered_denied.append([film_title, release_year, None, film_url])
                    self.rejected_movies_count += 1  # Increment rejected counter
                    return
            except Exception as e:
                print_to_csv(f"Error extracting TMDB ID: {str(e)}")
                print_to_csv(f"❌ {film_title} was not added due to missing TMDB ID.")
                self.processor.rejected_data.append([film_title, release_year, None, 'Missing TMDB ID'])
                self.processor.unfiltered_denied.append([film_title, release_year, None, film_url])
                self.rejected_movies_count += 1  # Increment rejected counter
                return

            # Extract rating count
            rating_count = 0
            try:
                match = re.search(r'ratingCount":(\d+)', page_source)
                if match:
                    rating_count = int(match.group(1))
            except Exception as e:
                print_to_csv(f"Error extracting rating count: {str(e)}")

            # Extract runtime using Selenium
            runtime = None
            try:
                runtime_text = self.driver.find_element(By.CSS_SELECTOR, 'p.text-link.text-footer').text
                match = re.search(r'(\d+)\s*min(?:s)?', runtime_text)
                if match:
                    runtime = int(match.group(1))
            except Exception:
                runtime = None

            # Check if movie has zero reviews
            if rating_count == 0:
                print_to_csv(f"📊 {film_title} has no reviews. Adding to zero reviews list.")
                self.processor.add_to_zero_reviews(film_title, release_year, film_url)
                self.processor.rejected_data.append([film_title, release_year, None, 'Zero reviews'])
                self.rejected_movies_count += 1  # Increment rejected counter
                return

            # Check minimum rating count
            if rating_count < MIN_RATING_COUNT:
                print_to_csv(f"❌ {film_title} was not added due to insufficient ratings: {rating_count} ratings.")
                self.processor.rejected_data.append([film_title, release_year, None, 'Insufficient ratings (< 1000)'])
                self.rejected_movies_count += 1  # Increment rejected counter
                return

            if runtime is None:
                print_to_csv(f"❌ {film_title} was not added due to missing runtime.")
                self.processor.rejected_data.append([film_title, release_year, None, 'Missing runtime'])
                self.processor.unfiltered_denied.append([film_title, release_year, None, film_url])
                self.rejected_movies_count += 1  # Increment rejected counter
                return

            if runtime < MIN_RUNTIME:
                print_to_csv(f"❌ {film_title} was not added due to a short runtime of {runtime} minutes.")
                self.processor.rejected_data.append([film_title, release_year, None, f'Short runtime of {runtime} minutes'])
                self.processor.add_to_blacklist(film_title, release_year, f'Short runtime of {runtime} minutes', film_url)
                self.rejected_movies_count += 1  # Increment rejected counter
                return

            # Check for blacklisted keywords and genres
            tmdb_data = self.processor.fetch_tmdb_details(tmdb_id)
            if tmdb_data is None:
                print_to_csv(f"❌ {film_title} was not added due to failed TMDB data fetch.")
                self.processor.rejected_data.append([film_title, release_year, None, 'Failed TMDB data fetch'])
                self.processor.unfiltered_denied.append([film_title, release_year, None, film_url])
                self.rejected_movies_count += 1  # Increment rejected counter
                return
                
            keywords, genres = tmdb_data
            
            # Check keywords - case insensitive comparison
            matching_keywords = [k for k in FILTER_KEYWORDS if k.lower() in [kw.lower() for kw in keywords]]
            if matching_keywords:
                rejection_reason = f"due to being a {', '.join(matching_keywords)}."
                print_to_csv(f"❌ {film_title} was not added {rejection_reason}")
                self.processor.rejected_data.append([film_title, release_year, None, rejection_reason])
                self.processor.add_to_blacklist(film_title, release_year, rejection_reason, film_url)
                self.rejected_movies_count += 1  # Increment rejected counter
                return
            
            # Check genres - case insensitive comparison
            matching_genres = [g for g in FILTER_GENRES if g.lower() in [gen.lower() for gen in genres]]
            if matching_genres:
                rejection_reason = f"due to being a {', '.join(matching_genres)}."
                print_to_csv(f"❌ {film_title} was not added {rejection_reason}")
                self.processor.rejected_data.append([film_title, release_year, None, rejection_reason])
                self.processor.add_to_blacklist(film_title, release_year, rejection_reason, film_url)
                self.rejected_movies_count += 1  # Increment rejected counter
                return

            # If we reach here, the movie is approved
            self.valid_movies_count += 1
            print_to_csv(f"✅ {film_title} was approved ({self.valid_movies_count}/{MAX_MOVIES})")
            
            # Add to unfiltered_approved
            self.processor.unfiltered_approved.append([film_title, release_year, tmdb_id, film_url])
            
            # Add to film data
            self.processor.film_data.append({
                'Title': film_title,
                'Year': release_year,
                'tmdbID': tmdb_id,
                'Link': film_url
            })

            # Add to max_movies_5000_stats only if we haven't reached the limit
            if len(max_movies_5000_stats['film_data']) < MAX_MOVIES_5000:
                max_movies_5000_stats['film_data'].append({
                    'Title': film_title,
                    'Year': release_year,
                    'tmdbID': tmdb_id,
                    'Link': film_url
                })
                # Update statistics for this movie
                self.update_max_movies_5000_statistics(film_title, release_year, tmdb_id, self.driver, film_url)
            else:
                print_to_csv(f"⚠️ {film_title} would be the {len(max_movies_5000_stats['film_data']) + 1}th movie, but we've reached the limit of {MAX_MOVIES_5000}")

            # Add to MPAA stats if applicable
            mpaa_rating = extract_mpaa_rating(self.driver)
            if mpaa_rating in MPAA_RATINGS:
                # Check if we've reached the limit for this rating
                max_limit = (
                    MAX_MOVIES_G if mpaa_rating == 'G' else
                    MAX_MOVIES_NC17 if mpaa_rating == 'NC-17' else
                    MAX_MOVIES_MPAA
                )
                if len(mpaa_stats[mpaa_rating]['film_data']) < max_limit:
                    mpaa_stats[mpaa_rating]['film_data'].append({
                        'Title': film_title,
                        'Year': release_year,
                        'tmdbID': tmdb_id,
                        'Link': film_url
                    })
                    # Update MPAA statistics
                    self.processor.update_statistics(mpaa_rating, film_url)

            # Add to runtime stats if applicable
            if runtime is not None:
                categories = []
                if runtime < 91:
                    categories.append('90_Minutes_or_Less')
                if runtime < 121:
                    categories.append('120_Minutes_or_Less')
                if runtime > 179:
                    categories.append('180_Minutes_or_Greater')
                if runtime > 239:
                    categories.append('240_Minutes_or_Greater')

                for category in categories:
                    # Check if we've reached the limit for this category
                    max_limit = (
                        MAX_180 if category == '180_Minutes_or_Greater' else
                        MAX_240 if category == '240_Minutes_or_Greater' else
                        MAX_MOVIES_RUNTIME
                    )
                    if len(runtime_stats[category]['film_data']) < max_limit:
                        runtime_stats[category]['film_data'].append({
                            'Title': film_title,
                            'Year': release_year,
                            'tmdbID': tmdb_id,
                            'Link': film_url
                        })
                        # Update runtime statistics
                        self.processor.update_runtime_statistics(film_title, release_year, tmdb_id, self.driver, category, film_url)

            # Add to continent stats if applicable
            try:
                country_elements = self.driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/films/country/"]')
                added_to_continent = set()  # Track which continents the film has been added to
                for country in country_elements:
                    country_name = country.get_attribute('textContent').strip()
                    if country_name:
                        # Check if the country belongs to any continent
                        for continent, countries in CONTINENTS_COUNTRIES.items():
                            if country_name in countries and continent not in added_to_continent:
                                # Check if we've reached the limit for this continent
                                max_limit = (
                                    MAX_MOVIES_AFRICA if continent == 'Africa' else
                                    MAX_MOVIES_OCEANIA if continent == 'Oceania' else
                                    MAX_MOVIES_SOUTH_AMERICA if continent == 'South America' else
                                    MAX_MOVIES_CONTINENT
                                )
                                if len(continent_stats[continent]['film_data']) < max_limit:
                                    continent_stats[continent]['film_data'].append({
                                        'Title': film_title,
                                        'Year': release_year,
                                        'tmdbID': tmdb_id,
                                        'Link': film_url
                                    })
                                    # Update continent statistics
                                    self.processor.update_continent_statistics(continent, film_url)
                                    added_to_continent.add(continent)  # Mark the continent as processed
                                break
            except Exception:
                pass

        except Exception as e:
            print_to_csv(f"Error processing approved movie {film_title}: {str(e)}")
            self.processor.rejected_data.append([film_title, release_year, None, f'Error processing: {str(e)}'])
            return False

    def update_max_movies_5000_statistics(self, film_title: str, release_year: str, tmdb_id: str, driver, film_url: str = None):
        """Update statistics for the given movie for MAX_MOVIES_5000."""
        if not film_url:
            print_to_csv("WARNING: No film URL provided for statistics update")
            return

        # Find the movie in film_data
        movie_data = next((movie for movie in max_movies_5000_stats['film_data'] 
                          if movie['Title'] == film_title and movie['Year'] == release_year), None)
        
        if not movie_data:
            return

        # Directors
        try:
            director_elements = driver.find_elements(By.CSS_SELECTOR, 'span.creatorlist a.contributor')
            for director in director_elements:
                director_name = director.text.strip()
                if director_name:
                    max_movies_5000_stats['director_counts'][director_name] += 1
        except Exception:
            pass

        # Actors
        try:
            actor_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-cast .text-sluglist a.text-slug.tooltip')
            for actor in actor_elements:
                actor_name = actor.text.strip()
                if actor_name:
                    max_movies_5000_stats['actor_counts'][actor_name] += 1
        except Exception:
            pass

        # Decade
        try:
            meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = meta_tag.get_attribute('content')
            if content and '(' in content and ')' in content:
                year = int(content.split('(')[-1].split(')')[0])
                decade = (year // 10) * 10
                max_movies_5000_stats['decade_counts'][decade] += 1
        except Exception:
            pass

        # Genres - Only get main genres, not microgenres
        try:
            genre_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-genres .text-sluglist a.text-slug[href*="/films/genre/"]')
            genres = []
            for genre in genre_elements:
                genre_name = genre.get_attribute('textContent').strip()
                if genre_name and not any(char in genre_name for char in ['…', 'Show All']):
                    genres.append(genre_name)
                    max_movies_5000_stats['genre_counts'][genre_name] += 1
            movie_data['Genres'] = genres
        except Exception:
            pass

        # Studios
        try:
            studio_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/studio/"]')
            studios = []
            for studio in studio_elements:
                studio_name = studio.get_attribute('textContent').strip()
                if studio_name:
                    studios.append(studio_name)
                    max_movies_5000_stats['studio_counts'][studio_name] += 1
            movie_data['Studios'] = studios
        except Exception:
            pass

        # Languages
        try:
            language_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/films/language/"]')
            languages = []
            for language in language_elements:
                language_name = language.get_attribute('textContent').strip()
                if language_name:
                    languages.append(language_name)
                    max_movies_5000_stats['language_counts'][language_name] += 1
            movie_data['Languages'] = languages
        except Exception:
            pass

        # Countries
        try:
            country_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-details .text-sluglist a.text-slug[href*="/films/country/"]')
            countries = []
            for country in country_elements:
                country_name = country.get_attribute('textContent').strip()
                if country_name:
                    countries.append(country_name)
                    max_movies_5000_stats['country_counts'][country_name] += 1
            movie_data['Countries'] = countries
        except Exception:
            pass

    def save_max_movies_5000_results(self):
        """Save results for MAX_MOVIES_5000."""
        
        # Save movie data in chunks
        num_chunks = (len(max_movies_5000_stats['film_data']) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for i in range(num_chunks):
            start_idx = i * CHUNK_SIZE
            end_idx = min((i + 1) * CHUNK_SIZE, len(max_movies_5000_stats['film_data']))
            chunk_df = pd.DataFrame(max_movies_5000_stats['film_data'][start_idx:end_idx])
            chunk_df = chunk_df[['Title', 'Year', 'tmdbID', 'Link']]
            output_path = os.path.join(BASE_DIR, f'popular_filtered_movie_titles{i+1}.csv')
            chunk_df.to_csv(output_path, index=False, encoding='utf-8')

        def get_ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return str(n) + suffix

        current_date = datetime.now()
        formatted_date = current_date.strftime('%B ') + get_ordinal(current_date.day) + f", {current_date.year}"

        # Save statistics for this rating
        stats_path = os.path.join(BASE_DIR, f'popular_filtered_titles.txt')
        
        with open(stats_path, mode='w', encoding='utf-8') as file:
            # Write header
            file.write(f"<strong>The Top {len(max_movies_5000_stats['film_data'])} Most Popular Narrative Feature Films on Letterboxd.</strong>\n\n")
            file.write(f"<strong>Last updated: {formatted_date}</strong>\n\n")
            file.write("<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly!</a>\n\n")
            
            # Write eligibility criteria
            file.write("<strong>Film eligibility criteria:</strong>\n")
            file.write("-- Must have a minimum of 1,000 reviews on Letterboxd.\n")
            file.write("-- Cannot be a short film (minimum 40 minutes).\n")
            file.write("-- Cannot be a television miniseries.\n")
            file.write("-- Cannot be a compilation of short serials.\n")
            file.write("-- Cannot be a documentary.\n")
            file.write("-- Cannot be a non-narrative project (paint drying for 10 hours, a timelapse of the construction of a building, abstract images, etc).\n")
            file.write("-- Cannot be a recording of a live performance (stand-up specials, recordings of live theater, concert films, etc).\n")
            file.write("-- Cannot be a television special episode, though feature film spin-offs from television shows are allowed.\n")
            file.write("-- Feature film spin-offs from television shows must contain original material, not just recap or compilation of existing material.\n")
            file.write("-- Entries that have scores inflated because they share a name with a popular television show are removed, as I notice them.\n\n")

            # Mapping for display names
            category_display_names = {
                'director_counts': 'directors',
                'actor_counts': 'actors',
                'decade_counts': 'decades',
                'genre_counts': 'genres',
                'studio_counts': 'studios',
                'language_counts': 'languages',
                'country_counts': 'countries'
            }

            # Write top 10 statistics for this category
            for category_name, counts in max_movies_5000_stats.items():
                if category_name != 'film_data':
                    display_name = category_display_names.get(category_name, category_name.replace('_counts', ''))
                    file.write(f"<strong>The ten most appearing {display_name}:</strong>\n")
                    sorted_items = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
                    for item, count in sorted_items:
                        file.write(f"{item}: {count}\n")
                    file.write("\n")
            file.write("<strong>If you notice any movies you believe should/should not be included just let me know!</strong>")

    def save_continent_results(self):
        """Save results for each continent."""
        category_display_names = {
            'director_counts': 'directors',
            'actor_counts': 'actors',
            'decade_counts': 'decades',
            'genre_counts': 'genres',
            'studio_counts': 'studios',
            'language_counts': 'languages',
            'country_counts': 'countries'
        }

        def get_ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return str(n) + suffix

        current_date = datetime.now()
        formatted_date = current_date.strftime('%B ') + get_ordinal(current_date.day) + f", {current_date.year}"

        for continent in CONTINENTS_COUNTRIES.keys():
            continent_data = continent_stats[continent]['film_data']
            if continent_data:
                # Determine the max limit based on the continent
                max_limit = (
                    MAX_MOVIES_AFRICA if continent == 'Africa' else
                    MAX_MOVIES_OCEANIA if continent == 'Oceania' else
                    MAX_MOVIES_SOUTH_AMERICA if continent == 'South America' else
                    MAX_MOVIES_CONTINENT
                )
                # Limit to top results
                top_data = continent_data[:int(max_limit)]  # Ensure it does not exceed the max
                if top_data:
                    # Save movie data in chunks
                    num_chunks = (len(top_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
                    for i in range(num_chunks):
                        start_idx = i * CHUNK_SIZE
                        end_idx = min((i + 1) * CHUNK_SIZE, len(top_data))
                        chunk_df = pd.DataFrame(top_data[start_idx:end_idx])
                        chunk_df = chunk_df[['Title', 'Year', 'tmdbID']]
                        output_path = os.path.join(BASE_DIR, f'{continent.replace(" ", "_").lower()}_pop_movies.csv')
                        chunk_df.to_csv(output_path, index=False, encoding='utf-8')

                    # Save statistics for this continent
                    stats_path = os.path.join(BASE_DIR, f'stats_{continent.replace(" ", "_").lower()}_pop_movies.txt')
                    with open(stats_path, mode='w', encoding='utf-8') as file:
                        file.write(f"<strong>The Top {len(top_data)} Most Popular Films from {'Australia' if continent == 'Oceania' else continent}</strong>\n\n")
                        file.write(f"<strong>Last updated: {formatted_date}</strong>\n\n")
                        file.write("<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>\n\n")
                        file.write("<strong>Film eligibility criteria:</strong>\n")
                        file.write("-- Must have a minimum of 1,000 reviews on Letterboxd.\n")
                        file.write("-- Cannot be a short film (minimum 40 minutes).\n")
                        file.write("-- Cannot be a television miniseries.\n")
                        file.write("-- Cannot be a compilation of short serials.\n")
                        file.write("-- Cannot be a documentary.\n")
                        file.write("-- Cannot be a non-narrative project (paint drying for 10 hours, a timelapse of the construction of a building, abstract images, etc).\n")
                        file.write("-- Cannot be a recording of a live performance (stand-up specials, recordings of live theater, concert films, etc).\n")
                        file.write("-- Cannot be a television special episode, though feature film spin-offs from television shows are allowed.\n")
                        file.write("-- Feature film spin-offs from television shows must contain original material, not just recap or compilation of existing material.\n")
                        file.write("-- Entries that have scores inflated because they share a name with a popular television show are removed, as I notice them.\n\n")

                        # Write top 10 statistics for this continent
                        for category_name in category_display_names.keys():  # Use the same order as defined in the dictionary
                            if category_name in continent_stats[continent]:  # Only process if the category exists
                                counts = continent_stats[continent][category_name]
                                display_name = category_display_names.get(category_name, category_name.replace('_', ' '))
                                file.write(f"<strong>The ten most appearing {display_name}:</strong>\n")
                                for item, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]:
                                    file.write(f"{item}: {count}\n")
                                file.write("\n")
                        file.write("<strong>If you notice any movies you believe should/should not be included just let me know!</strong>")

                    # Ensure we only save up to MAX_MOVIES_CONTINENT in the film data
                    continent_stats[continent]['film_data'] = continent_stats[continent]['film_data'][:MAX_MOVIES_CONTINENT]

    def save_results(self):
        """Save all results to files"""
        
        # Track movies by title
        title_to_movies = defaultdict(list)
        
        # Add approved movies
        for movie in self.processor.film_data:
            # Only add if not already in the list with the same tmdbID
            if not any(m['tmdb_id'] == movie['tmdbID'] for m in title_to_movies[movie['Title'].lower()]):
                title_to_movies[movie['Title'].lower()].append({
                    'title': movie['Title'],
                    'year': movie['Year'],
                    'tmdb_id': movie['tmdbID'],
                    'status': 'Approved'
                })
        
        # Add rejected movies
        for movie in self.processor.rejected_data:
            if len(movie) >= 3:  # Ensure we have at least title, year, and reason
                # Only add if not already in the list with the same tmdbID
                if not any(m['tmdb_id'] == movie[2] for m in title_to_movies[movie[0].lower()]):
                    title_to_movies[movie[0].lower()].append({
                        'title': movie[0],
                        'year': movie[1],
                        'tmdb_id': movie[2] if len(movie) > 2 else 'N/A',
                        'status': f'Rejected: {movie[3]}' if len(movie) > 3 else 'Rejected'
                    })

        # Save unfiltered approved data (append mode)
        approved_path = os.path.join(BASE_DIR, 'unfiltered_approved.csv')
        with open(approved_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header if file is empty
            if file.tell() == 0:
                writer.writerow(['Title', 'Year', 'Blank', 'URL', '5000 Pop'])
            for movie in self.processor.unfiltered_approved:
                # Ensure we have at least title, year, and URL
                if len(movie) >= 4:
                    writer.writerow([movie[0], movie[1], '', movie[3], '5000 Pop'])
                else:
                    print_to_csv(f"Warning: Movie data incomplete for {movie[0] if movie else 'Unknown'}")

        # Save unfiltered denied data (append mode)
        denied_path = os.path.join(BASE_DIR, 'unfiltered_denied.csv')
        with open(denied_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header if file is empty
            if file.tell() == 0:
                writer.writerow(['Title', 'Year', 'Blank', 'URL', '5000 Pop'])
            for movie in self.processor.unfiltered_denied:
                if len(movie) >= 4:
                    writer.writerow([movie[0], movie[1], '', movie[3], '5000 Pop'])
                else:
                    print_to_csv(f"Warning: Movie data incomplete for {movie[0] if movie else 'Unknown'}")

        # Save MPAA results
        self.save_mpaa_results()

        # Save runtime results
        self.save_runtime_results()

        # Save continent results
        self.save_continent_results()

        # Save unknown continent films
        self.save_unknown_continent_films()

        # Save MAX_MOVIES_5000 results
        self.save_max_movies_5000_results()

    def save_mpaa_results(self):
        """Save MPAA rating results to CSV and text files."""
        for rating in mpaa_stats:
            # Get the top movies for this rating
            top_data = mpaa_stats[rating]['film_data']
            if not top_data:
                continue
            
            # Determine the maximum limit for this rating
            max_limit = MAX_MOVIES_MPAA
            if rating == 'G':
                max_limit = MAX_MOVIES_G
            elif rating == 'NC-17':
                max_limit = MAX_MOVIES_NC17

            # Limit to top entries
            top_data = top_data[:max_limit]

            # Save movie data in chunks
            for i in range(0, len(top_data), CHUNK_SIZE):
                chunk = top_data[i:i + CHUNK_SIZE]
                with open(f'Outputs/{rating.upper()}_pop_movies.csv', mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Write headers if file is empty
                    if file.tell() == 0:
                        writer.writerow(['Title', 'Year', 'tmdbID'])
                    for movie in chunk:
                        writer.writerow([movie['Title'], movie['Year'], movie['tmdbID']])

            def get_ordinal(n):
                if 10 <= n % 100 <= 20:
                    suffix = 'th'
                else:
                    suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
                return str(n) + suffix

            current_date = datetime.now()
            formatted_date = current_date.strftime('%B ') + get_ordinal(current_date.day) + f", {current_date.year}"

            # Write statistics to text file
            with open(f'Outputs/stats_{rating.upper()}_pop_movies.txt', 'w', encoding='utf-8') as f:
                f.write(f"<strong>The Top {len(top_data)} Most Popular {rating} Rated Movies On Letterboxd</strong>\n\n")
                f.write("<strong>Rating defined by MPAA. Films released before November 1, 1968 are not eligible as they predate the current MPAA rating system. (Unless there was a subsequent re-rating.)</strong>\n\n")
                f.write(f"<strong>Last updated: {formatted_date}</strong>\n\n")
                f.write("<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>\n\n")
                f.write("<strong>Film eligibility criteria:</strong>\n")
                f.write("-- Must have a minimum of 1,000 reviews on Letterboxd.\n")
                f.write("-- Cannot be a short film (minimum 40 minutes).\n")
                f.write("-- Cannot be a television miniseries.\n")
                f.write("-- Cannot be a compilation of short serials.\n")
                f.write("-- Cannot be a documentary.\n")
                f.write("-- Cannot be a non-narrative project (paint drying for 10 hours, a timelapse of the construction of a building, abstract images, etc).\n")
                f.write("-- Cannot be a recording of a live performance (stand-up specials, recordings of live theater, concert films, etc).\n")
                f.write("-- Cannot be a television special episode, though feature film spin-offs from television shows are allowed.\n")
                f.write("-- Feature film spin-offs from television shows must contain original material, not just recap or compilation of existing material.\n")
                f.write("-- Entries that have scores inflated because they share a name with a popular television show are removed, as I notice them.\n\n")

                # Write statistics for each category
                category_display_names = {
                    'director_counts': 'directors',
                    'actor_counts': 'actors',
                    'decade_counts': 'decades',
                    'genre_counts': 'genres',
                    'studio_counts': 'studios',
                    'language_counts': 'languages',
                    'country_counts': 'countries'
                }

                for category_name, counts in mpaa_stats[rating].items():
                    if category_name != 'film_data':
                        # Use the mapping for display names
                        display_name = category_display_names.get(category_name, category_name.replace('_', ' '))
                        f.write(f"<strong>The ten most appearing {display_name}:</strong>\n")
                        for item, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]:
                            f.write(f"{item}: {count}\n")
                        f.write("\n")
                f.write("<strong>If you notice any movies you believe should/should not be included just let me know!</strong>")

    def save_runtime_results(self):
        """Save results for each runtime category."""
        for category in RUNTIME_CATEGORIES.keys():
            category_data = runtime_stats[category]['film_data']
            if category_data:
                # Determine the max limit based on the category
                max_limit = (
                    MAX_180 if category == '180_Minutes_or_Greater' else
                    MAX_240 if category == '240_Minutes_or_Greater' else
                    MAX_MOVIES_RUNTIME
                )
                # Limit to top results
                top_data = category_data[:int(max_limit)]  # Ensure it does not exceed the max
                # Save movie data in chunks
                num_chunks = (len(top_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
                for i in range(num_chunks):
                    start_idx = i * CHUNK_SIZE
                    end_idx = min((i + 1) * CHUNK_SIZE, len(top_data))
                    chunk_df = pd.DataFrame(top_data[start_idx:end_idx])
                    chunk_df = chunk_df[['Title', 'Year', 'tmdbID']]
                    output_path = os.path.join(BASE_DIR, f'{category}_pop_movies.csv')
                    chunk_df.to_csv(output_path, index=False, encoding='utf-8')

                def get_ordinal(n):
                    if 10 <= n % 100 <= 20:
                        suffix = 'th'
                    else:
                        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
                    return str(n) + suffix

                current_date = datetime.now()
                formatted_date = current_date.strftime('%B ') + get_ordinal(current_date.day) + f", {current_date.year}"

                # Save statistics for this category
                stats_path = os.path.join(BASE_DIR, f'stats_{category}_pop_movies.txt')
                with open(stats_path, mode='w', encoding='utf-8') as file:
                    # Format the category name for display
                    display_category = category.replace('_', ' ').replace('Minutes', 'minutes')
                    file.write(f"<strong>The Top {len(top_data)} Most Popular {display_category} Movies On Letterboxd</strong>\n\n")
                    file.write(f"<strong>Runtime defined as {display_category}.</strong>\n\n")
                    file.write(f"<strong>Last updated: {formatted_date}</strong>\n\n")
                    file.write("<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>\n\n")
                    file.write("<strong>Film eligibility criteria:</strong>\n")
                    file.write("-- Must have a minimum of 1,000 reviews on Letterboxd.\n")
                    file.write("-- Cannot be a short film (minimum 40 minutes).\n")
                    file.write("-- Cannot be a television miniseries.\n")
                    file.write("-- Cannot be a compilation of short serials.\n")
                    file.write("-- Cannot be a documentary.\n")
                    file.write("-- Cannot be a non-narrative project (paint drying for 10 hours, a timelapse of the construction of a building, abstract images, etc).\n")
                    file.write("-- Cannot be a recording of a live performance (stand-up specials, recordings of live theater, concert films, etc).\n")
                    file.write("-- Cannot be a television special episode, though feature film spin-offs from television shows are allowed.\n")
                    file.write("-- Feature film spin-offs from television shows must contain original material, not just recap or compilation of existing material.\n")
                    file.write("-- Entries that have scores inflated because they share a name with a popular television show are removed, as I notice them.\n\n")

                    # Write statistics for each category
                    category_display_names = {
                        'director_counts': 'directors',
                        'actor_counts': 'actors',
                        'decade_counts': 'decades',
                        'genre_counts': 'genres',
                        'studio_counts': 'studios',
                        'language_counts': 'languages',
                        'country_counts': 'countries'
                    }

                    for category_name, counts in runtime_stats[category].items():
                        if category_name != 'film_data':
                            # Use the mapping for display names
                            display_name = category_display_names.get(category_name, category_name.replace('_', ' '))
                            file.write(f"<strong>The ten most appearing {display_name}:</strong>\n")
                            for item, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]:
                                file.write(f"{item}: {count}\n")
                            file.write("\n")
                    file.write("<strong>If you notice any movies you believe should/should not be included just let me know!</strong>")

    def save_unknown_continent_films(self):
        """Save list of films with unknown countries to a file."""
        if unmapped_countries:
            with open('Outputs/unknown_countries.txt', 'w', encoding='utf-8') as f:
                f.write("Countries found in movies that are not mapped to any continent:\n\n")
                for country in sorted(unmapped_countries):
                    f.write(f"{country}")
                    # Add movie information if available
                    if hasattr(self, 'unmapped_countries_movies') and country in self.unmapped_countries_movies:
                        movies = self.unmapped_countries_movies[country]
                        if movies:
                            # Show first movie URL as reference
                            first_movie = movies[0]
                            f.write(f" (from: {first_movie['title']} ({first_movie['year']}) - {first_movie['url']})")
                    f.write("\n")

    def log_error_to_csv(self, error_message: str):
        """Log error messages to update_results.csv."""
        error_path = os.path.join(BASE_DIR, 'update_results.csv')
        with open(error_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Error Type', 'Error Message'])
            writer.writerow([type(error_message).__name__, error_message])  # Write the error type and message

    def update_statistics_for_movie(self, film_title: str, release_year: str, tmdb_id: str, driver, film_url: str = None):
        """Update statistics for the given movie."""
        try:
            # Get movie data from whitelist
            movie_data, _ = self.processor.get_whitelist_data(film_title, release_year, film_url)
            if not movie_data:
                return None

            # Only update whitelist if the movie is already in it
            if self.processor.is_whitelisted(film_title, release_year):
                if self.processor.update_whitelist(film_title, release_year, movie_data, film_url):
                    print_to_csv(f"📝 Successfully updated whitelist data for {film_title}")
                    # Process through all output channels
                    self.processor.process_whitelist_info(movie_data, film_url)
                    
                    self.valid_movies_count += 1
                    print_to_csv(f"✅ Processed whitelist data for {film_title} ({self.valid_movies_count}/{MAX_MOVIES})")
                    return movie_data

        except Exception as e:
            print_to_csv(f"Error in update_statistics_for_movie: {str(e)}")
            return None
    
def main():
    start_time = time.time()
    try:
        scraper = LetterboxdScraper()
        scraper.scrape_movies()
        scraper.save_results()

        # Format final statistics
        print_to_csv(f"\n{'Final Statistics':=^100}")
        print_to_csv(f"{'Total movies scraped:':<30} {scraper.total_titles:>10}")
        print_to_csv(f"{'Total accepted:':<30} {scraper.valid_movies_count:>10}")
        print_to_csv(f"{'Total rejected:':<30} {scraper.rejected_movies_count:>10}")  # Use counter instead of len(rejected_data)
        print_to_csv(f"{'Total unfiltered approved:':<30} {len(scraper.processor.unfiltered_approved):>10}")
        print_to_csv(f"{'Total unfiltered denied:':<30} {len(scraper.processor.unfiltered_denied):>10}")

        # Format execution time
        execution_time = time.time() - start_time
        print_to_csv(f"\n{'Execution Summary':=^100}")
        print_to_csv(f"Total execution time: {format_time(execution_time)}")
        print_to_csv(f"Average processing speed: {scraper.valid_movies_count / execution_time:.2f} movies/second")

    except Exception as e:
        print_to_csv(f"\n{'Error':=^100}")
        print_to_csv(f"❌ An error occurred during execution: {e}")
    finally:
        if 'scraper' in locals():
            try:
                scraper.driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()