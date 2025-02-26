import logging
import urllib

import requests
from bs4 import BeautifulSoup


def scrape_website(query):
    try:
        search_query = urllib.parse.quote(query)
        search_url = f'https://klsvdit.edu.in/?s={search_query}'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}

        response = requests.get(search_url, headers=headers)
        logging.debug(f"HTTP Status Code: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Log the HTML content to see what we're working with
            logging.debug(f"HTML Content: {soup.prettify()}")

            # More specific extraction based on observed HTML structure
            results = soup.find_all('article')  # Update this based on actual site structure
            logging.debug(f"Results found: {len(results)}")

            if results:
                extracted_texts = [result.get_text(strip=True) for result in results[:3]]
                logging.debug(f"Extracted Texts: {extracted_texts}")
                return "\n\n".join(extracted_texts)  # Limit to first 3 results

            return "No relevant information found on the website."

        elif response.status_code == 406:
            return "The website is rejecting requests. Try accessing it manually."

        return f"Failed to retrieve information (Status Code: {response.status_code})"

    except Exception as e:
        logging.error(f"Error in scrape_website: {str(e)}")
        return f"An error occurred: {str(e)}"


logging.basicConfig(level=logging.DEBUG)
