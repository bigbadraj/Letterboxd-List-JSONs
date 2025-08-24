import os
import platform

def get_os_specific_paths():
    """Return OS-specific file paths."""
    system = platform.system()
    
    if system == "Windows":
        # Windows paths
        base_dir = r'C:\Users\bigba\aa Personal Projects\Letterboxd List Scraping'
    elif system == "Darwin":  # macOS
        # macOS paths
        base_dir = '/Users/calebcollins/Documents/Letterboxd List Scraping'
    else:
        # Linux or other systems - use current directory
        base_dir = os.getcwd()
    
    return {
        'base_dir': base_dir
    }

def load_credentials():
    """Load credentials from credentials.txt file."""
    paths = get_os_specific_paths()
    credentials_file = os.path.join(paths['base_dir'], 'credentials.txt')
    
    credentials = {
        'TMDB_API_KEY': '',
        'GITHUB_API_KEY': '',
        'LETTERBOXD_USERNAME': '',
        'LETTERBOXD_PASSWORD': ''
    }
    
    try:
        with open(credentials_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in credentials:
                        credentials[key] = value
    except FileNotFoundError:
        print(f"Warning: credentials.txt not found at {credentials_file}")
    except Exception as e:
        print(f"Error reading credentials: {e}")
    
    return credentials 