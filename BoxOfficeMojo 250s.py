import requests
from bs4 import BeautifulSoup
import csv
import os
import platform

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

def scrape_movies(urls, output_filename):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_filename)

    movies = []
    movies_processed = 0

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for url in urls:
        page_movies = []
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            movie_rows = soup.select('table.mojo-body-table tr:has(td.mojo-field-type-rank)')

            for row in movie_rows:
                if movies_processed >= 250:
                    break
                
                try:
                    rank_element = row.select_one('td.mojo-field-type-rank')
                    title_element = row.select_one('td.mojo-field-type-title a')
                    year_cell = row.select_one('td.mojo-field-type-year')
                    
                    # Try to get year from link first, if not found get direct text
                    year = None
                    if year_cell:
                        year_link = year_cell.select_one('a')
                        if year_link:
                            year = year_link.text.strip()
                        else:
                            year = year_cell.text.strip()
                    
                    if not all([rank_element, title_element, year]):
                        continue
                    
                    rank = int(rank_element.text.strip())
                    title = title_element.text.strip()
                    
                    page_movies.append([rank, title, year])
                    movies_processed += 1
                    
                    if movies_processed % 10 == 0:
                        print_to_csv(f"Processed {movies_processed} movies")
                        
                except Exception as e:
                    continue

            movies.extend(page_movies)

        except Exception as e:
            print_to_csv(f"Error accessing URL {url}: {e}")
            continue

    sorted_movies = sorted(movies, key=lambda x: x[0])  # Sort by rank
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Year'])  # Removed Rank from header
            # Write rows excluding the rank
            writer.writerows([[movie[1], movie[2]] for movie in sorted_movies[:250]])  # Excluding rank
        print_to_csv(f"\nSuccessfully wrote {len(sorted_movies[:250])} movies to {output_file}")
    except Exception as e:
        print_to_csv(f"Error writing to CSV: {e}")

if __name__ == "__main__":
    # Run regular box office
    urls = [
        'https://www.boxofficemojo.com/chart/ww_top_lifetime_gross/?area=XWW',
        'https://www.boxofficemojo.com/chart/ww_top_lifetime_gross/?area=XWW&offset=200'
    ]
    output_filename = 'box_office_real.csv'
    scrape_movies(urls, output_filename)
    
    # Run inflation-adjusted box office
    urls = [
        'https://www.boxofficemojo.com/chart/top_lifetime_gross_adjusted/?adjust_gross_to=2022',
        'https://www.boxofficemojo.com/chart/top_lifetime_gross_adjusted/?adjust_gross_to=2022&offset=200'
    ]
    output_filename = 'box_office_inflated.csv'
    scrape_movies(urls, output_filename)