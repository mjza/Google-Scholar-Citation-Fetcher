from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
import bibtexparser
import csv
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Specify input and output files
input_file = 'input.bib'
output_file = 'citations_papers.csv'

# Path to your browser driver
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')  # Loaded from .env file

def extract_titles_from_bib(file_path):
    """Extract titles and IDs from the given .bib file."""
    with open(file_path, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    entries = [(entry.get('ID', f'article_{i}'), entry['title']) 
               for i, entry in enumerate(bib_database.entries) if 'title' in entry]
    return entries

def wait_for_user_to_solve_captcha(driver):
    """Detect and wait for the user to solve the CAPTCHA."""
    try:
        # Check if CAPTCHA form is present
        captcha_form = driver.find_element(By.ID, 'gs_captcha_f')
        print("\nCAPTCHA detected. Please solve the CAPTCHA in the browser.")
        print("After solving, press Enter here to continue...")
        input()
    except NoSuchElementException:
        # No CAPTCHA detected
        pass

def search_google_scholar(driver, title):
    """Search Google Scholar for the title and return total citation count."""
    try:
        # Open Google Scholar
        driver.get('https://scholar.google.com')

        # Find the search bar and enter the title
        search_box = driver.find_element(By.NAME, 'q')
        search_box.clear()
        search_box.send_keys(title)
        search_box.send_keys(Keys.RETURN)

        # Wait for CAPTCHA resolution, if required
        wait_for_user_to_solve_captcha(driver)

        # Wait for the results to load
        time.sleep(3)

        # Extract all "Cited by" counts
        try:
            citation_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/scholar?cites=') and starts-with(text(), 'Cited by')]")
            citation_count = sum(int(citation.text.split("Cited by ")[-1]) for citation in citation_elements)
            return citation_count
        except NoSuchElementException:
            print(f"Citations not found for title: {title}")
            return "Not found"
    except Exception as e:
        print(f"Error searching for title '{title}': {e}")
        return "Not found"

def main(input_file, output_file):
    print(f"Reading titles from {input_file}...")
    entries = extract_titles_from_bib(input_file)

    # Set up Selenium WebDriver
    print(f"Setting up the browser... {CHROMEDRIVER_PATH}")
    service = Service(CHROMEDRIVER_PATH)  # Use Service to specify the driver path
    driver = webdriver.Chrome(service=service)  # Pass the Service object
    driver.maximize_window()

    results = []
    print("Fetching citation counts from Google Scholar...\n")

    for index, (article_id, title) in enumerate(entries):
        print(f"Searching for title: {title}")
        citations = search_google_scholar(driver, title)
        print(f"Article ID: {article_id}\nTitle: {title}\nCitations: {citations}\n")
        results.append((article_id, title, citations))
        time.sleep(5)  # Delay to avoid triggering bot detection

        # Save progress after each entry
        with open(output_file, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Article ID', 'Title', 'Citations'])
            writer.writerows(results)

    # Close the browser
    driver.quit()
    print(f"Citation counts saved to '{output_file}'.")

if __name__ == "__main__":
    main(input_file, output_file)