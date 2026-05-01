import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

class URLParser:
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        # Basic regex for URLs
        url_pattern = re.compile(r'https?://[^\s]+')
        return url_pattern.findall(text)

    @staticmethod
    def parse_github(url: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return f"Failed to fetch GitHub: HTTP {response.status_code}"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            bio = soup.find('div', {'class': 'p-note user-profile-bio'})
            bio_text = bio.text.strip() if bio else "No bio found."
            
            repos = soup.find_all('span', {'class': 'repo'})
            repo_names = [r.text for r in repos][:10] # Top repos
            
            summary = f"GitHub Profile: {bio_text}\nPinned/Popular Repositories: {', '.join(repo_names)}"
            return summary
        except Exception as e:
            logger.error(f"Error parsing GitHub URL {url}: {e}")
            return ""

    @staticmethod
    def parse_linkedin(url: str) -> str:
        try:
            # LinkedIn typically requires authentication, doing best-effort public text scrape
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return "LinkedIn profile could not be completely scraped due to access restrictions."
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else ""
            meta_desc = soup.find("meta", {"name": "description"})
            desc_content = meta_desc["content"] if meta_desc else ""
            
            summary = f"LinkedIn Page Title: {title}\nSummary: {desc_content}"
            return summary
        except Exception as e:
            logger.error(f"Error parsing LinkedIn URL {url}: {e}")
            return "Error extracting LinkedIn data."

    @staticmethod
    def parse(url: str) -> str:
        if "github.com" in url:
            return URLParser.parse_github(url)
        elif "linkedin.com" in url:
            return URLParser.parse_linkedin(url)
        else:
            return f"No specialized parser for {url}."
