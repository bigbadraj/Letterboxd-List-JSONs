import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pandas as pd
import re
import os
import platform
import glob
import pyautogui
from tqdm import tqdm
import csv
from datetime import datetime
import logging
import traceback
from credentials_loader import load_credentials

# Configure logging to only show the message after - INFO -
logging.basicConfig(level=logging.INFO, format='%(message)s')

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
base_dir = paths['base_dir']

# Define a custom print function
def log_and_print(message: str):
    """Prints a message to the terminal and appends it to All_Outputs.csv."""
    print(message)  # Print to terminal
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'All_Outputs.csv'), mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([message])  # Write the message as a new row

def update_letterboxd_lists():
    # Load credentials
    credentials = load_credentials()
    
    # User credentials and file paths
    username = credentials['LETTERBOXD_USERNAME']
    password = credentials['LETTERBOXD_PASSWORD']
    output_csv_path = os.path.join(output_dir, 'update_results.csv')
    base_folder_path = output_dir

    # Dictionary of lists to update
    lists_to_update_easy = {
        "top_250_action_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-action-narrative-feature/edit/",
        "top_250_adventure_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-adventure-narrative/edit/",
        "top_250_animation_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-animation-narrative/edit/",
        "top_250_comedy_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-comedy-narrative-feature/edit/",
        "top_250_crime_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-crime-narrative-feature/edit/",
        "top_250_drama_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-drama-narrative-feature/edit/",
        "top_250_family_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-family-narrative-feature/edit/",
        "top_250_fantasy_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-fantasy-narrative-feature/edit/",
        "top_250_history_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-history-narrative-feature/edit/",
        "top_250_horror_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-horror-narrative-feature/edit/",
        "top_250_music_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-music-narrative-feature/edit/",
        "top_250_mystery_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-mystery-narrative-feature/edit/",
        "top_250_romance_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-romance-narrative-feature/edit/",
        "top_250_science-fiction_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-science-fiction-narrative/edit/",
        "top_250_thriller_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-thriller-narrative/edit/",
        "top_250_western_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-western-narrative-feature/edit/",
        "top_250_war_rating": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-war-narrative-feature/edit/",
        "G_top_movies": "https://letterboxd.com/bigbadraj/list/top-100-g-rated-narrative-feature-films/edit/",
        "PG_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-pg-rated-narrative-feature-films/edit/",
        "PG-13_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-pg-13-rated-narrative-feature-films/edit/",
        "R_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-r-rated-narrative-feature-films/edit/",
        "NC-17_top_movies": "https://letterboxd.com/bigbadraj/list/top-20-nc-17-rated-narrative-feature-films/edit/",
        "NR_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-nr-rated-narrative-feature-films/edit/",
        "north_america_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-north-american-narrative/edit/",
        "south_america_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-south-american-narrative/edit/",
        "europe_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-european-narrative/edit/",
        "asia_top_movies": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-asian-narrative-feature/edit/",
        "africa_top_movies": "https://letterboxd.com/bigbadraj/list/top-100-highest-rated-african-narrative-feature/edit/",
        "oceania_top_movies": "https://letterboxd.com/bigbadraj/list/top-75-highest-rated-australian-narrative/edit/",
        "90_Minutes_or_Less_top_movies": "https://letterboxd.com/bigbadraj/list/the-top-250-highest-rated-films-of-90-minutes/edit/",
        "120_Minutes_or_Less_top_movies": "https://letterboxd.com/bigbadraj/list/the-top-250-highest-rated-films-of-120-minutes/edit/",
        "180_Minutes_or_Greater_top_movies": "https://letterboxd.com/bigbadraj/list/the-top-150-highest-rated-films-of-180-minutes/edit/",
        "240_Minutes_or_Greater_top_movies": "https://letterboxd.com/bigbadraj/list/the-top-20-highest-rated-films-of-240-minutes/edit/",
        "top_250_action_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-action-narrative-feature/edit/",
        "top_250_adventure_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-adventure-narrative/edit/",
        "top_250_animation_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-animation-narrative/edit/",
        "top_250_comedy_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-comedy-narrative-feature/edit/",
        "top_250_crime_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-crime-narrative-feature/edit/",
        "top_250_drama_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-drama-narrative-feature/edit/",
        "top_250_family_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-family-narrative-feature/edit/",
        "top_250_fantasy_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-fantasy-narrative-feature/edit/",
        "top_250_history_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-history-narrative-feature/edit/",
        "top_250_horror_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-horror-narrative-feature/edit/",
        "top_250_music_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-music-narrative-feature/edit/",
        "top_250_mystery_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-mystery-narrative-feature/edit/",
        "top_250_romance_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-romance-narrative-feature/edit/",
        "top_250_science-fiction_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-science-fiction-narrative/edit/",
        "top_250_thriller_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-thriller-narrative-feature/edit/",
        "top_250_western_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-western-narrative-feature/edit/",
        "top_250_war_popular": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-war-narrative-feature/edit/",
        "G_pop_movies": "https://letterboxd.com/bigbadraj/list/top-200-most-popular-g-rated-narrative-feature/edit/",
        "PG_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-pg-rated-narrative-feature/edit/",
        "PG-13_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-pg-13-rated-narrative/edit/",
        "R_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-r-rated-narrative-feature/edit/",
        "NC-17_pop_movies": "https://letterboxd.com/bigbadraj/list/top-25-most-popular-nc-17-rated-narrative/edit/",
        "NR_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-nr-rated-narrative-feature/edit/",
        "north_america_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-north-american-narrative/edit/",
        "south_america_pop_movies": "https://letterboxd.com/bigbadraj/list/top-100-most-popular-south-american-narrative/edit/",
        "europe_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-european-narrative-feature/edit/",
        "asia_pop_movies": "https://letterboxd.com/bigbadraj/list/top-250-most-popular-asian-narrative-feature/edit/",
        "africa_pop_movies": "https://letterboxd.com/bigbadraj/list/top-20-most-popular-african-narrative-feature/edit/",
        "oceania_pop_movies": "https://letterboxd.com/bigbadraj/list/top-150-most-popular-australian-narrative/edit/",
        "90_Minutes_or_Less_pop_movies": "https://letterboxd.com/bigbadraj/list/the-top-250-most-popular-films-of-90-minutes/edit/",
        "120_Minutes_or_Less_pop_movies": "https://letterboxd.com/bigbadraj/list/the-top-250-most-popular-films-of-120-minutes/edit/",
        "180_Minutes_or_Greater_pop_movies": "https://letterboxd.com/bigbadraj/list/the-top-75-most-popular-films-of-180-minutes/edit/",
        "240_Minutes_or_Greater_pop_movies": "https://letterboxd.com/bigbadraj/list/the-top-5-most-popular-films-of-240-minutes/edit/",
    }

    # Dictionary of lists to update with specific descriptions
    lists_with_descriptions = {
        "film_titles": {
            "url": "https://letterboxd.com/bigbadraj/list/top-250-highest-rated-things-on-letterboxd/edit/",
            "description": "Minimum 1,000 reviews. Otherwise, anything on Letterboxd is eligible.\n\nLast Updated: {date}\n\n<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>"
        },
        "stand_up_comedy": {
            "url": "https://letterboxd.com/bigbadraj/list/top-100-highest-rated-stand-up-comedy-specials/edit/",
            "description": "Minimum 1,000 reviews.\n\nLast Updated: {date}\n\n<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>\n\n<a href=https://letterboxd.com/asset/list/stand-up-comedy-a-comprehensive-list/> Based off of this list of Stand-Up Comedy Specials </a>"
        },
        "box_office_real": {
            "url": "https://letterboxd.com/bigbadraj/list/top-250-highest-grossing-movies-of-all-time-1/edit/",
            "description": "According to Box Office Mojo.\n\nLast Updated: {date}\n\n<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>"
        },
        "box_office_inflated": {
            "url": "https://letterboxd.com/bigbadraj/list/top-250-highest-grossing-domestic-movies/edit/",
            "description": "According to Box Office Mojo.\n\nLast Updated: {date}\n\n<a href=https://letterboxd.com/bigbadraj/list/the-official-list-index/> Check out more of the lists I update regularly! </a>"
        }
    }

    # Handle special lists
    special_lists = {
        "rating_filtered_movie_titles1": {
            "url": "https://letterboxd.com/bigbadraj/list/top-2500-highest-rated-narrative-feature/edit/",
            "csv_file_name_1": "rating_filtered_movie_titles1.csv",
            "csv_file_name_2": "rating_filtered_movie_titles2.csv",
            "csv_file_name_3": "rating_filtered_movie_titles3.csv"
        },
        "popular_filtered_movie_titles1": {
            "url": "https://letterboxd.com/bigbadraj/list/top-2500-most-popular-narrative-feature-films/edit/",
            "csv_file_name_1": "popular_filtered_movie_titles1.csv",
            "csv_file_name_2": "popular_filtered_movie_titles2.csv",
            "csv_file_name_3": "popular_filtered_movie_titles3.csv"
        }
    }

    # Initialize the Firefox driver
    driver = webdriver.Firefox()

    try:
        log_and_print("✅ Navigating to Letterboxd homepage.")
        driver.get("https://letterboxd.com/")
        time.sleep(2)

        log_and_print("✅ Clicking on the 'Sign in' button.")
        sign_in_button = driver.find_element(By.CSS_SELECTOR, ".sign-in-menu a")
        sign_in_button.click()
        time.sleep(1)

        log_and_print("✅ Entering username and password.")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)

        # Loop through each list to update
        results = []
        for list_name, edit_url in lists_to_update_easy.items():
            log_and_print(f"✅ Updating list: {list_name}")
            
            # Initialize a flag to track errors
            has_error = False

            try:
                # Navigate to the list edit page
                driver.get(edit_url)
                time.sleep(2)

                # Step 1: Click the Import button
                log_and_print("✅ Clicking the Import button.")
                import_button = driver.find_element(By.CSS_SELECTOR, ".list-import-link")
                import_button.click()
                time.sleep(2)

                # Step 2: Select the correct CSV file
                csv_file_name = f"{list_name}.csv"

                log_and_print(f"✅ Selecting CSV file: {csv_file_name}")
                time.sleep(1)

                # Use Alt + D to focus on the address bar of the file dialog
                pyautogui.hotkey('alt', 'd')
                time.sleep(1)

                # Type the path to the Outputs folder
                pyautogui.typewrite(output_dir, interval=0.1)
                pyautogui.press('enter')  # Navigate to the Outputs folder
                time.sleep(1) 

                # Click into the search field of the Outputs folder
                pyautogui.click(x=300, y=200)  
                time.sleep(1) 

                # Select the correct CSV file
                pyautogui.typewrite(csv_file_name, interval=0.1) 
                time.sleep(1)  
                pyautogui.press('enter')

                time.sleep(2)  

                # Step 3: Attempt to find and copy the associated txt file
                file_found = False
                attempts = 0
                max_attempts = 3

                while not file_found and attempts < max_attempts:
                    # Use glob to find files that include the list_name
                    matching_files = glob.glob(os.path.join(base_folder_path, f"stats_{list_name}*.txt"))

                    if matching_files:
                        # If it finds any matching files, read the first one (or handle as needed)
                        with open(matching_files[0], 'r', encoding='utf-8') as txt_file:
                            file_contents = txt_file.read()
                        log_and_print(f"✅ Copied contents from {matching_files[0]}.")
                        file_found = True
                    else:
                        log_and_print(f"No matching text files found for {list_name}. Attempting again.")
                        # Simulate typing the text file name to find it again
                        pyautogui.click(x=300, y=200)
                        time.sleep(1)
                        pyautogui.typewrite(f"{list_name}*.txt", interval=0.1)  
                        time.sleep(1)
                        pyautogui.press('enter')

                        time.sleep(1)  
                        attempts += 1  

                if not file_found:
                    log_and_print(f"❌ Failed to find any matching text files for {list_name} after {max_attempts} attempts.")
                    has_error = True  

                time.sleep(15)  

                # Step 4: Click the "Hide Successful Matches" button
                try:
                    hide_successful_matches_handle = driver.find_element(By.CSS_SELECTOR, ".import-toggle .handle")
                    hide_successful_matches_handle.click()
                    log_and_print("✅ Clicked the 'Hide Successful Matches' handle.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the handle: {str(e)}")

                time.sleep(5)  

                # Step 5: Click the "Replace existing list with imported films" checkbox
                try:
                    replace_substitute = driver.find_element(By.CSS_SELECTOR, "label[for='replace-original'] .substitute")
                    replace_substitute.click()
                    log_and_print("✅ Clicked the 'Replace existing list with imported films' substitute icon.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the substitute icon: {str(e)}")

                time.sleep(1)  

                # Step 6: Click the "Add films to list" button
                log_and_print("✅ Clicking the 'Add films to list' button.")
                add_films_button = driver.find_element(By.CSS_SELECTOR, ".add-import-films-to-list")
                add_films_button.click()
                time.sleep(5)  

                # Step 7: Replace the existing list description with the copied text file contents
                if 'file_contents' in locals():
                    description_field = driver.find_element(By.CSS_SELECTOR, "textarea[name='notes']")  

                    try:
                        description_field.clear()  
                        description_field.send_keys(file_contents)  
                        log_and_print("✅ Successfully added text using send_keys.")
                    except Exception as e:
                        log_and_print(f"❌ Failed to add text using send_keys: {str(e)}")

                # Step 8: Save the changes
                time.sleep(1)
                log_and_print("✅ Saving the changes.")
                driver.find_element(By.ID, "list-edit-save").click()
                time.sleep(7)  

                # Log success or failure based on the error flag
                if has_error:
                    results.append({
                        'list_name': list_name,
                        'status': 'Failed to update: Missing text file'
                    })
                else:
                    results.append({
                        'list_name': list_name,
                        'status': 'Successfully updated'
                    })
                log_and_print(f"✅ Successfully updated list: {list_name}")

            except Exception as e:
                log_and_print(f"❌ Failed to update list: {list_name}. Error: {str(e)}")
                results.append({
                    'list_name': list_name,
                    'status': f'Failed to update: {str(e)}'
                })
                continue  

        # Handle lists with specific descriptions
        for list_name, details in lists_with_descriptions.items():
            log_and_print(f"✅ Updating list: {list_name}")

            # Initialize a flag to track errors
            has_error = False

            try:
                # Navigate to the list edit page
                driver.get(details["url"])
                time.sleep(2) 

                # Step 1: Click the Import button
                log_and_print("✅ Clicking the Import button.")
                import_button = driver.find_element(By.CSS_SELECTOR, ".list-import-link")
                import_button.click()
                time.sleep(2)  

                # Step 2: Select the correct CSV file
                csv_file_name = f"{list_name}.csv"  

                log_and_print(f"✅ Selecting CSV file: {csv_file_name}")
                time.sleep(1) 

                # Use Alt + D to focus on the address bar of the file dialog
                pyautogui.hotkey('alt', 'd')
                time.sleep(1) 

                # Type the path to the Outputs folder
                pyautogui.typewrite(output_dir, interval=0.1)
                pyautogui.press('enter')  
                time.sleep(1)  

                # Click into the search field of the Outputs folder
                pyautogui.click(x=300, y=200)  
                time.sleep(1) 

                # Select the correct CSV file
                pyautogui.typewrite(csv_file_name, interval=0.1) 
                time.sleep(1) 
                pyautogui.press('enter')  
                time.sleep(30)  

                # Step 4: Click the "Hide Successful Matches" button
                try:
                    hide_successful_matches_handle = driver.find_element(By.CSS_SELECTOR, ".import-toggle .handle")
                    hide_successful_matches_handle.click()
                    log_and_print("✅ Clicked the 'Hide Successful Matches' handle.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the handle: {str(e)}")

                time.sleep(7)

                # Step 5: Click the "Replace existing list with imported films" checkbox
                try:
                    replace_substitute = driver.find_element(By.CSS_SELECTOR, "label[for='replace-original'] .substitute")
                    replace_substitute.click()
                    log_and_print("✅ Clicked the 'Replace existing list with imported films' substitute icon.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the substitute icon: {str(e)}")
                    
                time.sleep(1) 

                # Step 6: Click the "Add films to list" button
                log_and_print("✅ Clicking the 'Add films to list' button.")
                add_films_button = driver.find_element(By.CSS_SELECTOR, ".add-import-films-to-list")
                add_films_button.click()
                time.sleep(5)  

                # Step 7: Replace the existing list description with the new description
                current_date = time.strftime("%m/%d/%Y")  
                description = details["description"].format(date=current_date)  

                description_field = driver.find_element(By.CSS_SELECTOR, "textarea[name='notes']")  

                try:
                    description_field.clear()  
                    description_field.send_keys(description) 
                    log_and_print("✅ Successfully added text using send_keys.")
                except Exception as e:
                    log_and_print(f"❌ Failed to add text using send_keys: {str(e)}")

                # Step 8: Save the changes
                time.sleep(1)
                log_and_print("✅ Saving the changes.")
                driver.find_element(By.ID, "list-edit-save").click()
                time.sleep(7)  

                # Log success or failure based on the error flag
                if has_error:
                    results.append({
                        'list_name': list_name,
                        'status': 'Failed to update: Missing text file'
                    })
                else:
                    results.append({
                        'list_name': list_name,
                        'status': 'Successfully updated'
                    })
                log_and_print(f"✅ Successfully updated list: {list_name}")

            except Exception as e:
                log_and_print(f"❌ Failed to update list: {list_name}. Error: {str(e)}")
                results.append({
                    'list_name': list_name,
                    'status': f'Failed to update: {str(e)}'
                })
                continue  

        # Handle special lists
        for list_name, details in special_lists.items():
            log_and_print(f"✅ Updating special list: {list_name}")

            try:
                # Navigate to the list edit page
                driver.get(details["url"])
                time.sleep(2)  

                # Step 1: Click the Import button
                log_and_print("✅ Clicking the Import button.")
                import_button = driver.find_element(By.CSS_SELECTOR, ".list-import-link")
                import_button.click()
                time.sleep(2)  

                # Step 2: Import the first CSV file
                log_and_print("✅ Importing the first CSV file.")
                csv_file_name = details["csv_file_name_1"] 
                log_and_print(f"✅ Selecting CSV file: {csv_file_name}")
                time.sleep(1)  

                # Use Alt + D to focus on the address bar of the file dialog
                pyautogui.hotkey('alt', 'd')
                time.sleep(1) 

                # Type the path to the Outputs folder
                pyautogui.typewrite(output_dir, interval=0.1)
                pyautogui.press('enter')  
                time.sleep(1)  

                # Click into the search field of the Outputs folder
                pyautogui.click(x=300, y=200)  
                time.sleep(1)  

                # Select the correct CSV file
                pyautogui.typewrite(csv_file_name, interval=0.1) 
                time.sleep(1)  
                pyautogui.press('enter')  

                time.sleep(30)  

                # Attempt to find and copy the associated txt file
                file_found = False
                attempts = 0
                max_attempts = 3  

                while not file_found and attempts < max_attempts:
                    # Use glob to find files that start with the first 15 characters of list_name and end with .txt
                    matching_files = glob.glob(os.path.join(base_folder_path, f"{list_name[:15]}*.txt"))

                    if matching_files:
                        # If it finds matching files, read the first one (or handle as needed)
                        with open(matching_files[0], 'r', encoding='utf-8') as txt_file:
                            file_contents = txt_file.read()
                        log_and_print(f"✅ Copied contents from {matching_files[0]}.")
                        file_found = True
                    else:
                        log_and_print(f"No matching text files found for {list_name}. Attempting again.")
                        pyautogui.click(x=300, y=200)  
                        time.sleep(1)  
                        pyautogui.typewrite(f"{list_name[:15]}*.txt", interval=0.1) 
                        time.sleep(1) 
                        pyautogui.press('enter')  

                        time.sleep(1)  
                        attempts += 1  

                # Step 3: Click the "Hide Successful Matches" button
                try:
                    hide_successful_matches_handle = driver.find_element(By.CSS_SELECTOR, ".import-toggle .handle")
                    hide_successful_matches_handle.click()
                    log_and_print("✅ Clicked the 'Hide Successful Matches' handle.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the handle: {str(e)}")

                time.sleep(7)  
                
                # Step 4: Click the "Replace existing list with imported films" checkbox
                try:
                    replace_substitute = driver.find_element(By.CSS_SELECTOR, "label[for='replace-original'] .substitute")
                    replace_substitute.click()
                    log_and_print("✅ Clicked the 'Replace existing list with imported films' substitute icon.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the substitute icon: {str(e)}")
                
                time.sleep(1)  

                # Step 5: Click the "Add films to list" button
                log_and_print("✅ Clicking the 'Add films to list' button.")
                add_films_button = driver.find_element(By.CSS_SELECTOR, ".add-import-films-to-list")
                add_films_button.click()
                time.sleep(5)  

                # Step 6: Replace the existing list description with the copied text file contents
                if 'file_contents' in locals():
                    description_field = driver.find_element(By.CSS_SELECTOR, "textarea[name='notes']") 

                    try:
                        description_field.clear()  
                        description_field.send_keys(file_contents) 
                        log_and_print("✅ Successfully added text using send_keys.")
                    except Exception as e:
                        log_and_print(f"❌ Failed to add text using send_keys: {str(e)}")

                # Step 7: Save the changes for the first import
                time.sleep(15)
                log_and_print("✅ Saving the changes for the first import.");
                driver.find_element(By.ID, "list-edit-save").click()
                time.sleep(15)  

                # Step 8: Click the Import button again
                log_and_print("✅ Clicking the Import button for the second time.")
                import_button = driver.find_element(By.CSS_SELECTOR, ".list-import-link")
                import_button.click()
                time.sleep(2)  

                # Step 9: Import the second CSV file
                log_and_print("✅ Importing the second CSV file.")
                csv_file_name = details["csv_file_name_2"] 
                log_and_print(f"✅ Selecting CSV file: {csv_file_name}")
                time.sleep(1)  

                # Use Alt + D to focus on the address bar of the file dialog
                pyautogui.hotkey('alt', 'd')
                time.sleep(1) 

                # Type the path to the Outputs folder
                pyautogui.typewrite(output_dir, interval=0.1)
                pyautogui.press('enter')  
                time.sleep(1)  

                # Click into the search field of the Outputs folder
                pyautogui.click(x=300, y=200)  
                time.sleep(1)  

                # Select the correct CSV file
                pyautogui.typewrite(csv_file_name, interval=0.1) 
                time.sleep(1)  
                pyautogui.press('enter')  

                time.sleep(30)  

                # Step 10: Click the "Hide Successful Matches" button again
                try:
                    hide_successful_matches_handle = driver.find_element(By.CSS_SELECTOR, ".import-toggle .handle")
                    hide_successful_matches_handle.click()
                    log_and_print("✅ Clicked the 'Hide Successful Matches' handle.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the handle: {str(e)}")

                time.sleep(7)

                # Step 11: Click the "Add films to list" button again
                log_and_print("✅ Clicking the 'Add films to list' button.")
                add_films_button = driver.find_element(By.CSS_SELECTOR, ".add-import-films-to-list")
                add_films_button.click()
                time.sleep(5)   

                # Step 12: Save the changes for the second import
                time.sleep(1)
                log_and_print("✅ Saving the changes for the second import.")
                driver.find_element(By.ID, "list-edit-save").click()
                time.sleep(25)  

                # Step 13: Click the Import button for the third time
                log_and_print("✅ Clicking the Import button for the third time.")
                import_button = driver.find_element(By.CSS_SELECTOR, ".list-import-link")
                import_button.click()
                time.sleep(2)  

                # Step 14: Import the second CSV file
                log_and_print("✅ Importing the third CSV file.")
                csv_file_name = details["csv_file_name_3"] 
                log_and_print(f"✅ Selecting CSV file: {csv_file_name}")
                time.sleep(1)  

                # Use Alt + D to focus on the address bar of the file dialog
                pyautogui.hotkey('alt', 'd')
                time.sleep(1) 

                # Type the path to the Outputs folder
                pyautogui.typewrite(output_dir, interval=0.1)
                pyautogui.press('enter')  
                time.sleep(1)  

                # Click into the search field of the Outputs folder
                pyautogui.click(x=300, y=200)  
                time.sleep(1)  

                # Select the correct CSV file
                pyautogui.typewrite(csv_file_name, interval=0.1) 
                time.sleep(1)  
                pyautogui.press('enter')  

                time.sleep(30)  

                # Step 15: Click the "Hide Successful Matches" button again
                try:
                    hide_successful_matches_handle = driver.find_element(By.CSS_SELECTOR, ".import-toggle .handle")
                    hide_successful_matches_handle.click()
                    log_and_print("✅ Clicked the 'Hide Successful Matches' handle.")
                except Exception as e:
                    log_and_print(f"❌ Failed to click the handle: {str(e)}")

                time.sleep(7)

                # Step 16: Click the "Add films to list" button again
                log_and_print("✅ Clicking the 'Add films to list' button.")
                add_films_button = driver.find_element(By.CSS_SELECTOR, ".add-import-films-to-list")
                add_films_button.click()
                time.sleep(5)   

                # Step 17: Save the changes for the third import
                time.sleep(1)
                log_and_print("✅ Saving the changes for the third import.")
                driver.find_element(By.ID, "list-edit-save").click()
                time.sleep(15)   

                log_and_print(f"✅ Successfully updated special list: {list_name}")
                # Append success result for special list
                results.append({
                    'list_name': list_name,
                    'status': 'Successfully updated'
                })

            except Exception as e:
                log_and_print(f"❌ Failed to update special list: {list_name}. Error: {str(e)}")
                # Append failure result for special list
                results.append({
                    'list_name': list_name,
                    'status': f'Failed to update: {str(e)}'
                })
                continue  

    except Exception as e:
        log_and_print(f"❌ Failed to update list: {list_name}. Error: {str(e)}")
        log_and_print(traceback.format_exc())  
        results.append({
            'list_name': list_name,
            'status': f'Failed to update: {str(e)}'
        })

    finally:
        # Output the results to a CSV file
        log_and_print("✅ Outputting results to CSV file.")
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv_path, index=False, mode='a', header=not os.path.exists(output_csv_path)) 

        # Close the browser
        time.sleep(5)
        log_and_print("✅ Closing the browser.")
        driver.quit()

# Example usage
update_letterboxd_lists()