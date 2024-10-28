import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()


def format_results(organic_results):

        result_strings = []
        for result in organic_results:
            title = result.get('title', 'No Title')
            link = result.get('link', '#')
            snippet = result.get('snippet', 'No snippet available.')
            result_strings.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
        
        return '\n'.join(result_strings)


def format_scraped_content(scraped_results: List[Dict[str, Any]]) -> str:
    """
    Format the scraped content into a readable string.

    Args:
        scraped_results (List[Dict[str, Any]]): A list of dictionaries containing scraped content.
            Each dictionary should have the following structure:
            {
                'url': str,
                'title': str,
                'content': str,
                'status': str
            }

    Returns:
        str: A formatted string containing the scraped content.
    """
    formatted_results = []
    for result in scraped_results:
        url = result.get('url', 'No URL')
        title = result.get('title', 'No Title')
        content = result.get('content', 'No content available.')
        status = result.get('status', 'Unknown')

        formatted_result = f"URL: {url}\nTitle: {title}\nStatus: {status}\nContent: {content}\n"
        formatted_results.append(formatted_result)

    return '\n---\n'.join(formatted_results)


def serpapi_search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Perform a web search using SerpAPI based on the provided query.

    Args:
        query (str): The search query string.
        num_results (int, optional): The number of search results to return. Defaults to 10.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing search results.
                              Each dictionary represents a search result with keys like
                              'title', 'link', 'snippet', etc.

    Raises:
        ValueError: If the SerpAPI key is not found in environment variables.
        Exception: For any other errors that occur during the API call.
    """
    # Retrieve the SerpAPI key from environment variables
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SerpAPI key not found. Please set the SERPAPI_API_KEY environment variable.")

    try:
        # Set up the search parameters
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": num_results
        }

        # Perform the search
        search = GoogleSearch(params)
        results = search.get_dict()

        # Extract and return the organic search results
        organic_results = results.get("organic_results", [])
        return format_results(organic_results)

    except Exception as e:
        # Log the error (you might want to use a proper logging system)
        print(f"An error occurred during the SerpAPI search: {str(e)}")
        # Re-raise the exception or return an empty list, depending on your error handling strategy
        raise



def scrape_url(url: str) -> str:
    """
    Scrape the content from a given URL.

    Args:
        url (str): The URL to scrape.

    Returns:
        Dict[str, Any]: A dictionary containing the scraped content and metadata.
            {
                'url': str,
                'title': str,
                'content': str,
                'status': str
            }
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the title and content
        title = soup.title.string if soup.title else "No title found"
        content = ' '.join([p.get_text() for p in soup.find_all('p')])

        return format_scraped_content([{
            'url': url,
            'title': title,
            'content': content,
            'status': 'success'
        }])

    except requests.RequestException as e:
        return {
            'url': url,
            'title': "Error",
            'content': f"Failed to scrape the URL: {str(e)}",
            'status': 'error'
        }
    
if __name__ == "__main__":
    # url = "https://www.techtarget.com/whatis/definition/large-language-model-LLM"
    url = "https://www.cloudflare.com/learning/ai/what-is-large-language-model/"
    result = scrape_url(url)
    print(result)