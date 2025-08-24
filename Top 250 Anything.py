import time
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
import csv

# Detect operating system and set appropriate paths
def get_os_specific_paths():
    """Return OS-specific file paths."""
    system = platform.system()
    
    if system == "Windows":
        # Windows paths
        base_dir = r'C:\Users\bigba\aa Personal Projects\Letterboxd List Scraping'
        excel_path = os.path.join(base_dir, 'top_250_data.xlsx')
        output_dir = os.path.join(base_dir, 'Outputs')
    elif system == "Darwin":  # macOS
        # macOS paths
        base_dir = '/Users/calebcollins/Documents/Letterboxd List Scraping'
        excel_path = os.path.join(base_dir, 'top_250_data.xlsx')
        output_dir = os.path.join(base_dir, 'Outputs')
    
    return {
        'excel_path': excel_path,
        'output_dir': output_dir,
        'base_dir': base_dir
    }

# Get OS-specific paths
paths = get_os_specific_paths()
EXCEL_PATH = paths['excel_path']
output_dir = paths['output_dir']

# Define a custom print function
def print_to_csv(message: str):
    """Prints a message to the terminal and appends it to All_Outputs.csv."""
    print(message)  # Print to terminal
    with open(os.path.join(output_dir, 'All_Outputs.csv'), mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([message])  # Write the message as a new row

class MovieCache:
    def __init__(self):
        self.cache = None
        self.cache_lookup = {}
        self.load_cache()
    
    def load_cache(self):
        """Load the Excel cache file."""
        try:
            self.cache = pd.read_excel(EXCEL_PATH)
            # Create lookup dictionary for faster matching
            for idx, row in self.cache.iterrows():
                self.cache_lookup[row['Link']] = {
                    'Title': row['Title'],
                    'Year': row['Year'],
                    'index': idx
                }
            print_to_csv(f"📚 Loaded {len(self.cache)} movies from cache")
        except FileNotFoundError:
            print_to_csv("📚 Cache file not found. Creating new file.")
            self.cache = pd.DataFrame(columns=['Title', 'Year', 'Link'])
            self.cache.to_excel(EXCEL_PATH, index=False)
    
    def is_cached(self, film_url: str) -> bool:
        """Check if a movie is in the cache."""
        return film_url in self.cache_lookup
    
    def get_cached_data(self, film_url: str) -> dict:
        """Get cached data for a movie."""
        return self.cache_lookup.get(film_url)
    
    def update_cache(self, film_title: str, release_year: str, film_url: str):
        """Update the cache with new movie data."""
        if film_url in self.cache_lookup:
            # Update existing entry
            idx = self.cache_lookup[film_url]['index']
            self.cache.at[idx, 'Title'] = film_title
            self.cache.at[idx, 'Year'] = release_year
            print_to_csv(f"📝 Updated cache entry for {film_title} ({release_year})")
        else:
            # Add new entry
            new_row = pd.DataFrame([{
                'Title': film_title,
                'Year': release_year,
                'Link': film_url
            }])
            self.cache = pd.concat([self.cache, new_row], ignore_index=True)
            self.cache_lookup[film_url] = {
                'Title': film_title,
                'Year': release_year,
                'index': len(self.cache) - 1
            }
            print_to_csv(f"💾 Added new cache entry for {film_title} ({release_year})")
        
        # Save to Excel immediately
        self.cache.to_excel(EXCEL_PATH, index=False)

# Set up Firefox options and service
options = Options()
options.headless = False  # Set to True if you don't want the browser to open

# Initialize the Firefox driver with GeckoDriver in PATH
service = Service()
driver = webdriver.Firefox(service=service, options=options)

# Initialize movie cache
movie_cache = MovieCache()

# Base URL of the Letterboxd films page
base_url = 'https://letterboxd.com/films/by/rating/'
film_titles = []
total_titles = 0  # Counter for total titles scraped
page_number = 1  # Start at page 1

max_movies = 250
MIN_RATING_COUNT = 1000

class ProgressTracker:
    def __init__(self, total_films):
        self.total_films = total_films
        self.current_count = 0
        self.start_time = time.time()
    
    def increment(self):
        self.current_count += 1
        return self.current_count
    
    def get_elapsed_time(self):
        return time.time() - self.start_time
    
    def get_progress_stats(self):
        elapsed_time = self.get_elapsed_time()
        movies_per_second = self.current_count / elapsed_time if elapsed_time > 0 else 0
        estimated_total_time = self.total_films / movies_per_second if movies_per_second > 0 else 0
        time_remaining = estimated_total_time - elapsed_time if estimated_total_time > 0 else 0
        
        return {
            'elapsed_time': elapsed_time,
            'movies_per_second': movies_per_second,
            'time_remaining': time_remaining
        }

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Initialize progress tracker
progress_tracker = ProgressTracker(max_movies)
print_to_csv(f"\n{' Starting Film Scraping ':=^100}")

# First, collect all film URLs
print_to_csv("Collecting film URLs...")
film_urls = []
current_page = 1

while len(film_urls) < max_movies:
    url = f'{base_url}page/{current_page}/'
    print_to_csv(f'Collecting URLs from page {current_page}')
    
    # Add retry mechanism for page loading
    page_retries = 20
    for retry in range(page_retries):
        try:
            driver.get(url)
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.posteritem'))
            )
            time.sleep(random.uniform(1.0, 1.5))
            break
        except Exception as e:
            if retry == page_retries - 1:
                print_to_csv(f"❌ Failed to load page after {page_retries} attempts: {str(e)}")
                raise Exception(f"Failed to load page after {page_retries} attempts: {str(e)}")
            print_to_csv(f"Retry {retry + 1}/{page_retries} loading page {current_page}: {str(e)}")
            time.sleep(2)
    
    # Find all film containers with retry mechanism
    film_containers = []
    container_retries = 25
    for retry in range(container_retries):
        try:
            film_containers = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.posteritem'))
            )
            if len(film_containers) > 0:  # Check for any containers
                break
            else:
                print_to_csv(f"Found no containers, retrying... (Attempt {retry + 1}/{container_retries})")
                time.sleep(5)  # Wait longer between retries
                driver.refresh()  # Refresh the page
                time.sleep(2)  # Wait for refresh
        except Exception as e:
            if retry == container_retries - 1:
                print_to_csv(f"❌ Failed to find film containers after {container_retries} attempts: {str(e)}")
                raise Exception(f"Failed to find film containers after {container_retries} attempts: {str(e)}")
            print_to_csv(f"Retry {retry + 1}/{container_retries} finding film containers: {str(e)}")
            time.sleep(5)
            driver.refresh()
            time.sleep(2)
    
    for container in film_containers:
        if len(film_urls) >= max_movies:
            break
        try:
            # Look for the film link within the posteritem container
            film_link = container.find_element(By.CSS_SELECTOR, 'a[href*="/film/"]')
            film_url = film_link.get_attribute('href')
            film_urls.append(film_url)
        except Exception as e:
            print_to_csv(f"Error extracting film URL from container: {str(e)}")
            continue
    
    current_page += 1
    time.sleep(random.uniform(1.0, 1.5))

print_to_csv(f"Collected {len(film_urls)} film URLs")

# Now process each film URL
with tqdm(total=max_movies, desc="Total Progress", unit=" films") as overall_pbar:
    for film_url in film_urls:
        if total_titles >= max_movies:
            break
        
        # Check if movie is in cache
        if movie_cache.is_cached(film_url):
            cached_data = movie_cache.get_cached_data(film_url)
            film_title = cached_data['Title']
            release_year = cached_data['Year']
            print_to_csv(f"✅ Using cached data for {film_title} ({release_year})")
            
            film_titles.append({
                'Title': film_title,
                'Year': release_year
            })
            total_titles += 1
            progress_tracker.increment()
            overall_pbar.update(1)
            
            # Print progress for cached movies too
            stats = progress_tracker.get_progress_stats()
            print_to_csv(f"\n{f'Overall Progress: {total_titles}/{max_movies} films':^100}")
            print_to_csv(f"{'Elapsed Time: ' + format_time(stats['elapsed_time']) + ' | Estimated Time Remaining: ' + format_time(stats['time_remaining']):^100}")
            print_to_csv(f"{'Processing Speed: {:.2f} movies/second'.format(stats['movies_per_second']):^100}")
            continue
            
        # Add retry logic for fetching film details
        max_retries = 20
        success = False
        
        for retry in range(max_retries):
            try:
                driver.get(film_url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[property="og:title"]'))
                )
                time.sleep(random.uniform(1.0, 1.5))
                
                # Get title and year in one go from the meta title
                meta_title = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                title_content = meta_title.get_attribute('content')
                film_title = title_content.split(' (')[0]
                release_year = title_content.split('(')[-1].strip(')')
                
                # Extract rating count
                rating_count = 0
                try:
                    page_source = driver.page_source
                    match = re.search(r'ratingCount":(\d+)', page_source)
                    if match:
                        rating_count = int(match.group(1))
                except Exception as e:
                    print_to_csv(f"Error extracting rating count: {str(e)}")
                    if retry < max_retries - 1:
                        print_to_csv(f"Retrying... (Attempt {retry + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    break
                
                # Only add movies with sufficient ratings
                if rating_count >= MIN_RATING_COUNT:
                    # Update cache with new movie data
                    movie_cache.update_cache(film_title, release_year, film_url)
                    
                    film_titles.append({
                        'Title': film_title,
                        'Year': release_year
                    })
                    total_titles += 1
                    progress_tracker.increment()
                    
                    # Update the overall progress bar
                    overall_pbar.update(1)
                    
                    # Print progress every movie
                    stats = progress_tracker.get_progress_stats()
                    print_to_csv(f"\n{f'Overall Progress: {total_titles}/{max_movies} films':^100}")
                    print_to_csv(f"{'Elapsed Time: ' + format_time(stats['elapsed_time']) + ' | Estimated Time Remaining: ' + format_time(stats['time_remaining']):^100}")
                    print_to_csv(f"{'Processing Speed: {:.2f} movies/second'.format(stats['movies_per_second']):^100}")
                    print_to_csv(f"Last Scraped: {film_title} ({release_year})")
                    success = True
                    break
                else:
                    print_to_csv(f"Skipping {film_title} - insufficient ratings ({rating_count})")
                    success = True  # Mark as success since we got the data, just didn't meet criteria
                    break
                    
            except Exception as e:
                print_to_csv(f"Error processing {film_url} (attempt {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    print_to_csv(f"Retrying... (Attempt {retry + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                break

# Close the browser
driver.quit()

# Check if any titles were scraped
if film_titles:
    print_to_csv(f'{len(film_titles)} Film titles were scraped successfully:')
else:
    print_to_csv("No film titles were scraped.")

# Create a DataFrame and save to CSV if desired
df = pd.DataFrame(film_titles)
output_csv = os.path.join(output_dir, 'film_titles.csv')
df.to_csv(output_csv, index=False, encoding='utf-8')
print_to_csv("Film titles have been successfully saved to film_titles.csv.")