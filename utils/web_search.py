"""
Web search functionality for legal research.

This module provides search capabilities to find relevant legal articles,
checklists, and resources to enhance playbook generation.

Supports multiple search backends:
- Google Custom Search API (if configured)
- DuckDuckGo HTML scraping (free fallback)
"""
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import time


def search_legal_resources(
    agreement_type: str,
    api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None,
    max_results: int = 10,
    custom_instructions: str = ""
) -> List[Dict[str, str]]:
    """
    Search for legal resources related to the agreement type.
    
    Uses Google Custom Search API if configured, otherwise falls back to DuckDuckGo.
    
    Args:
        agreement_type: Type of agreement (e.g., "SaaS Agreement", "MSA")
        api_key: Google API key (optional, defaults to env var)
        search_engine_id: Google Custom Search Engine ID (optional, defaults to env var)
        max_results: Maximum number of results to return per query
        custom_instructions: User's custom search instructions for specific resources
    
    Returns:
        List of search results with title, snippet, link, and display_link
    """
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    # Use Google if configured, otherwise use DuckDuckGo
    if api_key and search_engine_id:
        return _search_with_google(agreement_type, api_key, search_engine_id, max_results, custom_instructions)
    else:
        return _search_with_duckduckgo(agreement_type, max_results, custom_instructions)


def _search_with_google(
    agreement_type: str,
    api_key: str,
    search_engine_id: str,
    max_results: int = 10,
    custom_instructions: str = ""
) -> List[Dict[str, str]]:
    """
    Search using Google Custom Search API.
    
    Args:
        agreement_type: Type of agreement
        api_key: Google API key
        search_engine_id: Google Custom Search Engine ID
        max_results: Maximum number of results to return
        custom_instructions: Custom search instructions from user
    
    Returns:
        List of search results
    """
    
    # Build search queries based on custom instructions or defaults
    if custom_instructions:
        # Parse custom instructions and create targeted queries
        search_queries = _build_custom_queries(agreement_type, custom_instructions)
    else:
        # Define default search queries for different types of legal resources
        search_queries = [
            f"{agreement_type} checklist",
            f"{agreement_type} legal review guide",
            f"{agreement_type} negotiation best practices",
            f"{agreement_type} key terms"
        ]
    
    all_results = []
    seen_urls = set()
    
    for query in search_queries:
        try:
            results = _perform_google_search(
                query=query,
                api_key=api_key,
                search_engine_id=search_engine_id,
                num_results=max_results // len(search_queries)
            )
            
            # Deduplicate results
            for result in results:
                if result['link'] not in seen_urls:
                    seen_urls.add(result['link'])
                    all_results.append(result)
                    
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            continue
    
    return all_results[:max_results]


def _perform_google_search(
    query: str,
    api_key: str,
    search_engine_id: str,
    num_results: int = 3
) -> List[Dict[str, str]]:
    """
    Perform a single Google Custom Search query.
    
    Args:
        query: Search query string
        api_key: Google API key
        search_engine_id: Google Custom Search Engine ID
        num_results: Number of results to return
    
    Returns:
        List of search results
    """
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'num': min(num_results, 10)  # Google API max is 10 per request
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    results = []
    for item in data.get('items', []):
        results.append({
            'title': item.get('title', ''),
            'snippet': item.get('snippet', ''),
            'link': item.get('link', ''),
            'display_link': item.get('displayLink', '')
        })
    
    return results


def _build_custom_queries(agreement_type: str, custom_instructions: str) -> List[str]:
    """
    Build search queries based on custom user instructions.
    
    Args:
        agreement_type: Type of agreement
        custom_instructions: User's custom search instructions
    
    Returns:
        List of search query strings
    """
    queries = []
    
    # Split instructions into sentences or key phrases
    # Look for comma-separated items or sentence boundaries
    instructions_parts = re.split(r'[,;.]', custom_instructions)
    
    for part in instructions_parts:
        part = part.strip()
        if part and len(part) > 10:  # Skip very short fragments
            # Combine with agreement type if not already mentioned
            if agreement_type.lower() not in part.lower():
                queries.append(f"{agreement_type} {part}")
            else:
                queries.append(part)
    
    # If we got no valid queries from parsing, use the full instruction
    if not queries:
        queries.append(f"{agreement_type} {custom_instructions}")
    
    # Limit to 4 queries max to avoid too many API calls
    return queries[:4]


def _search_with_duckduckgo(
    agreement_type: str,
    max_results: int = 10,
    custom_instructions: str = ""
) -> List[Dict[str, str]]:
    """
    Search using DuckDuckGo HTML scraping (free, no API key required).
    
    Args:
        agreement_type: Type of agreement
        max_results: Maximum number of results to return
        custom_instructions: Custom search instructions from user
    
    Returns:
        List of search results
    """
    # Build search queries based on custom instructions or defaults
    if custom_instructions:
        search_queries = _build_custom_queries(agreement_type, custom_instructions)
    else:
        # Define default search queries for different types of legal resources
        search_queries = [
            f"{agreement_type} checklist",
            f"{agreement_type} legal review guide",
            f"{agreement_type} negotiation best practices",
            f"{agreement_type} key terms"
        ]
    
    all_results = []
    seen_urls = set()
    
    for query in search_queries:
        try:
            results = _perform_duckduckgo_search(
                query=query,
                num_results=max_results // len(search_queries)
            )
            
            # Deduplicate results
            for result in results:
                if result['link'] not in seen_urls:
                    seen_urls.add(result['link'])
                    all_results.append(result)
            
            # Rate limiting to be respectful
            time.sleep(1)
                    
        except Exception as e:
            print(f"Error searching DuckDuckGo for '{query}': {e}")
            continue
    
    return all_results[:max_results]


def _perform_duckduckgo_search(
    query: str,
    num_results: int = 3
) -> List[Dict[str, str]]:
    """
    Perform a single DuckDuckGo search by scraping HTML results.
    
    Args:
        query: Search query string
        num_results: Number of results to return
    
    Returns:
        List of search results
    """
    url = "https://html.duckduckgo.com/html/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    data = {
        'q': query,
        'kl': 'us-en'  # Region
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        result_divs = soup.find_all('div', class_='result')
        
        for result_div in result_divs[:num_results]:
            try:
                # Extract title and link
                title_tag = result_div.find('a', class_='result__a')
                if not title_tag:
                    continue
                
                title = title_tag.get_text().strip()
                link = title_tag.get('href', '')
                
                # Extract snippet
                snippet_tag = result_div.find('a', class_='result__snippet')
                snippet = snippet_tag.get_text().strip() if snippet_tag else ''
                
                # Extract display URL
                url_tag = result_div.find('a', class_='result__url')
                display_link = url_tag.get_text().strip() if url_tag else ''
                
                # Clean up display link
                if display_link:
                    display_link = display_link.replace(' : ', '/').strip()
                
                if link and title:
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'link': link,
                        'display_link': display_link or link
                    })
                    
            except Exception as e:
                print(f"Error parsing DuckDuckGo result: {e}")
                continue
        
        return results
        
    except Exception as e:
        print(f"Error performing DuckDuckGo search: {e}")
        return []


def fetch_webpage_content(url: str, max_length: int = 5000) -> Dict[str, str]:
    """
    Fetch and extract main content from a webpage.
    
    Args:
        url: URL of the webpage to fetch
        max_length: Maximum length of text to extract (in characters)
    
    Returns:
        Dictionary with 'url', 'title', 'content', and 'error' keys
    """
    result = {
        'url': url,
        'title': '',
        'content': '',
        'error': None
    }
    
    try:
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text().strip()
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            script.decompose()
        
        # Try to find main content area
        main_content = None
        for tag in ['article', 'main', 'div[role="main"]']:
            main_content = soup.find(tag)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Extract text
            text = main_content.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            result['content'] = text
        else:
            result['error'] = "Could not extract content from page"
            
    except requests.Timeout:
        result['error'] = "Request timed out"
    except requests.RequestException as e:
        result['error'] = f"Failed to fetch page: {str(e)}"
    except Exception as e:
        result['error'] = f"Error processing page: {str(e)}"
    
    return result


def fetch_multiple_urls(urls: List[str], max_length: int = 5000) -> List[Dict[str, str]]:
    """
    Fetch content from multiple URLs.
    
    Args:
        urls: List of URLs to fetch
        max_length: Maximum length of text to extract per URL
    
    Returns:
        List of results from fetch_webpage_content
    """
    results = []
    for url in urls:
        result = fetch_webpage_content(url, max_length)
        results.append(result)
    
    return results


def format_web_resources_for_ai(web_resources: List[Dict[str, str]]) -> str:
    """
    Format fetched web resources into a string for AI analysis.
    
    Args:
        web_resources: List of web resource dictionaries with title, url, content
    
    Returns:
        Formatted string for inclusion in AI prompts
    """
    if not web_resources:
        return ""
    
    formatted = "\n\n===== ADDITIONAL LEGAL RESOURCES =====\n\n"
    formatted += "The following legal resources were researched and selected for context:\n\n"
    
    for idx, resource in enumerate(web_resources, 1):
        if resource.get('error'):
            continue
            
        formatted += f"--- Resource {idx}: {resource.get('title', 'Untitled')} ---\n"
        formatted += f"Source: {resource.get('url', 'Unknown')}\n\n"
        formatted += resource.get('content', '')[:3000]  # Limit each resource
        formatted += "\n\n"
    
    formatted += "===== END ADDITIONAL RESOURCES =====\n\n"
    formatted += "Please consider these resources when analyzing the contract and generating the playbook.\n\n"
    
    return formatted