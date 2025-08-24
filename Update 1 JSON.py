import requests
from bs4 import BeautifulSoup
import json
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from tqdm import tqdm
import time
from github import Github
import os
from datetime import datetime
import platform
from credentials_loader import load_credentials

# Detect operating system and set appropriate paths
def get_os_specific_paths():
    """Return OS-specific file paths."""
    system = platform.system()
    
    if system == "Windows":
        # Windows paths
        base_dir = r'C:\Users\bigba\aa Personal Projects\Letterboxd List Scraping'
        jsons_dir = os.path.join(base_dir, 'JSONs')
    elif system == "Darwin":  # macOS
        # macOS paths
        base_dir = '/Users/calebcollins/Documents/Letterboxd List Scraping'
        jsons_dir = os.path.join(base_dir, 'JSONs')
    
    return {
        'base_dir': base_dir,
        'jsons_dir': jsons_dir
    }

# Get OS-specific paths
paths = get_os_specific_paths()
jsons_dir = paths['jsons_dir']

# Thread-safe list for storing movie data
class ThreadSafeList:
    def __init__(self):
        self.items = []
        self.lock = threading.Lock()
    
    def extend(self, items):
        with self.lock:
            self.items.extend(items)
    
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
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def process_film(session, film_url, progress_tracker, list_number=None):
    retries = 3
    for attempt in range(retries):
        try:
            film_response = session.get(f"https://letterboxd.com{film_url}", timeout=10)
            film_response.raise_for_status()
            film_soup = BeautifulSoup(film_response.content, 'html.parser')
            
            og_title = film_soup.find('meta', property='og:title')
            if og_title:
                title_text = og_title['content']
                
                # Extract year and title
                year = ''
                if '(' in title_text and ')' in title_text:
                    year = title_text[title_text.rindex('(')+1:title_text.rindex(')')]
                    title = title_text[:title_text.rindex('(')].strip()
                else:
                    title = title_text
                
                film_poster_div = film_soup.find('div', class_='film-poster')
                film_id = film_poster_div.get('data-film-id') if film_poster_div else "Unknown"
                
                current = progress_tracker.increment()
                print(f"✅ {title_text} - Added ({current}/{progress_tracker.total_films})")
                return {'ListNumber': list_number, 'Title': title, 'Year': year, 'ID': film_id} if list_number is not None else {'Title': title, 'Year': year, 'ID': film_id}
            
            break
        except Exception as e:
            print(f"❌ Error processing film {film_url}, attempt {attempt + 1}/{retries}: {e}")
            sleep(1)
    return None

def process_page(session, url, max_films, progress_tracker):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Updated selector
        film_list = soup.find('ul', class_='poster-list')

        if not film_list:
            print("Film list not found on page.")
            return False, []
        
        temp_data = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            # Look for the new posteritem structure
            for li in film_list.find_all('li', class_='posteritem'):
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
                
                if not film_url:
                    print("Film URL not found for one item; skipping.")
                    continue
                
                # Get list number from the p.list-number element
                list_number_tag = li.find('p', class_='list-number')
                list_number = int(list_number_tag.text.strip()) if list_number_tag else None
                
                # Extract title and year from data attributes if available
                # The data attributes are on the inner div, not the li element
                if inner_div:
                    film_title = inner_div.get('data-item-full-display-name') or inner_div.get('data-item-name')
                else:
                    film_title = None
                
                if film_title and '(' in film_title and ')' in film_title:
                    # Extract year and title from the full display name
                    year = film_title[film_title.rindex('(')+1:film_title.rindex(')')]
                    title = film_title[:film_title.rindex('(')].strip()
                    
                    # If we have the title and year, we can skip the individual film processing
                    # and just add it directly to avoid extra API calls
                    current = progress_tracker.increment()
                    print(f"✅ {film_title} - Added ({current}/{progress_tracker.total_films})")
                    temp_data.append({'ListNumber': list_number, 'Title': title, 'Year': year, 'ID': 'Unknown'} if list_number is not None else {'Title': title, 'Year': year, 'ID': 'Unknown'})
                else:
                    # Fallback to processing individual film page
                    futures.append(executor.submit(process_film, session, film_url, progress_tracker, list_number))
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    temp_data.append(result)
                    # uncomment for more details print(f"Processed film: {result}")
        
        has_next = bool(soup.find('a', class_='next'))
        return has_next, temp_data
    except Exception as e:
        print(f"Error processing page {url}: {e}")
        return False, []

def get_list_size(session, base_url):
    try:
        response = session.get(base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get count from meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '')
            if 'A list of ' in content and ' films' in content:
                # Remove commas before converting to int
                number_str = content.split('A list of ')[1].split(' films')[0]
                return int(number_str.replace(',', ''))
        
        # Fallback to calculating from page count if meta description fails
        film_list = soup.find('ul', class_='poster-list') or \
                   soup.find('div', class_='poster-list') # Added div as fallback
        
        films_per_page = len(film_list.find_all('li', class_='posteritem')) if film_list else 0
        pagination = soup.find_all('li', class_='paginate-page')
        total_pages = int(pagination[-1].text) if pagination else 1
        
        return films_per_page * total_pages
    except Exception as e:
        print(f"Error getting list size: {e}")
        return 0

class ProgressTracker:
    def __init__(self, total_films):
        self.total_films = total_films
        self.current_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def increment(self):
        with self.lock:
            self.current_count += 1
            return self.current_count
    
    def get_elapsed_time(self):
        return time.time() - self.start_time

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

def update_github_file(filename, file_content):
    """
    Updates or creates a file in the GitHub repository.
    """
    try:
        # Load credentials
        credentials = load_credentials()
        
        # Initialize Github with your access token
        g = Github(credentials['GITHUB_API_KEY'])
        
        # Get the repository
        repo = g.get_repo("bigbadraj/Letterboxd-List-JSONs")
        
        # Get just the filename without path
        base_filename = os.path.basename(filename)
        
        try:
            # Try to get existing file
            contents = repo.get_contents(base_filename)
            # If file exists, update it
            repo.update_file(
                contents.path,
                f"Updated {base_filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                file_content,
                contents.sha
            )
            print(f"✅ Successfully updated {base_filename} on GitHub")
        except Exception:
            # If file doesn't exist, create it
            repo.create_file(
                base_filename,
                f"Added {base_filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                file_content
            )
            print(f"✅ Successfully created {base_filename} on GitHub")
            
    except Exception as e:
        print(f"❌ Error updating GitHub: {str(e)}")

def main():
    print("Choose an option:")
    print("1: Add one list (not updated)")
    print("2: Add one list (updated)")
    
    choice = input("Enter the number (1/2): ").strip()

    if choice in ["1", "2"]:
        base_url = input("Enter the Letterboxd list URL: ").strip()
        list_name = base_url.rstrip('/').split('/')[-1]
        output_json = os.path.join(jsons_dir, f'film_titles_{list_name}.json')
        
        session = create_session()
        total_films = get_list_size(session, base_url)
        progress_tracker = ProgressTracker(total_films)
        
        # Process the list with GitHub updates only for option 2
        if choice == "1":
            process_single_list(base_url, output_json, progress_tracker=progress_tracker, update_github=False)
        else:
            process_single_list(base_url, output_json, progress_tracker=progress_tracker, update_github=True)

def process_single_list(base_url, output_json, progress_tracker, max_films=None, update_github=True):
    session = create_session()
    all_data = ThreadSafeList()
    current_page = 1
    
    # Get total number of pages first
    response = session.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    pagination = soup.find_all('li', class_='paginate-page')
    total_pages = int(pagination[-1].text) if pagination else 1
    
    with tqdm(
        total=total_pages, 
        desc="Processing pages", 
        unit=" pages",
        bar_format="{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} pages"
    ) as pbar:
        while True:
            page_url = f"{base_url}page/{current_page}/" if current_page > 1 else base_url
            print(f"\n{f' Page {current_page}/{total_pages} ':=^100}")
            has_next, page_data = process_page(session, page_url, max_films, progress_tracker)
            
            if page_data:
                all_data.extend(page_data)
            
            # Calculate overall progress
            total_time = progress_tracker.get_elapsed_time()
            current_movies_per_second = progress_tracker.current_count / total_time if total_time > 0 else 0
            estimated_total_time = progress_tracker.total_films / current_movies_per_second if current_movies_per_second > 0 else 0
            time_remaining = estimated_total_time - total_time if estimated_total_time > 0 else 0
            
            print(f"{f'Overall Progress: {progress_tracker.current_count}/{progress_tracker.total_films} films':^100}")
            print(f"{f'Elapsed Time: {format_time(total_time)} | Estimated Time Remaining: {format_time(time_remaining)}':^100}")
            print(f"{f'Processing Speed: {current_movies_per_second:.2f} movies/second':^100}")
            
            pbar.update(1)
            
            if not has_next or (max_films and len(all_data) >= max_films):
                break
                
            current_page += 1
            sleep(1)

    # Before saving to JSON, sort the data if it contains ListNumber
    final_data = all_data.items
    if any('ListNumber' in item for item in final_data):
        final_data = sorted(final_data, key=lambda x: x.get('ListNumber', float('inf')))

    # Save to GitHub repository only (do not write to local file)
    json_content = json.dumps(final_data, ensure_ascii=False, indent=2)
    if update_github:
        update_github_file(output_json, json_content)
    
    print(f"\nSaved {len(all_data)} films to GitHub: {output_json}")
    print(f"Total time elapsed: {format_time(total_time)}")
    print(f"Processing speed: {current_movies_per_second:.2f} movies/second")

if __name__ == "__main__":
    main()