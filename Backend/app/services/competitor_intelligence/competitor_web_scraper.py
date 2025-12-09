"""
Web Scraper Service for Competitor Data Extraction
Scrapes competitor websites to extract features, pricing, and other relevant data
Supports multiple strategies: requests → Selenium → API fallback
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class CompetitorWebScraper:
    """Service for scraping competitor websites with multiple fallback strategies"""
    
    def __init__(self):
        self.timeout = 15.0
        # Multiple user agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.current_ua_index = 0
        self._selenium_available = None
    
    def _is_selenium_available(self) -> bool:
        """Check if Selenium is available"""
        if self._selenium_available is not None:
            return self._selenium_available
        
        try:
            from selenium import webdriver
            self._selenium_available = True
            return True
        except ImportError:
            self._selenium_available = False
            return False
    
    async def scrape_competitor_data(
        self,
        url: str,
        competitor_name: str
    ) -> Dict[str, Any]:
        """
        Scrape competitor website and extract structured data with multiple fallback strategies
        
        Args:
            url: Competitor website URL
            competitor_name: Name of the competitor
            
        Returns:
            Dictionary with extracted data
        """
        logger.info(f"Scraping {competitor_name}: {url}")
        
        # Strategy 1: Try direct scraping with rotating user agents
        for attempt in range(len(self.user_agents)):
            try:
                headers = {
                    'User-Agent': self.user_agents[self.current_ua_index],
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
                
                # Rotate user agent for next request
                self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
                
                if response.status_code == 200:
                    # Parse HTML
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract text content
                    text_content = self._extract_text_content(soup)
                    
                    # Check if we got meaningful content
                    if len(text_content.strip()) < 100:
                        logger.warning(f"Insufficient content from {url}, trying alternative URL")
                        # Try alternative URL (homepage)
                        alt_url = self._get_alternative_url(url)
                        if alt_url != url:
                            return await self.scrape_competitor_data(alt_url, competitor_name)
                        raise Exception("Insufficient content extracted")
                    
                    # Extract structured data using LLM
                    extracted_data = await self._extract_with_llm(
                        text_content=text_content,
                        competitor_name=competitor_name,
                        url=url
                    )
                    
                    # Add metadata
                    extracted_data['scraped_url'] = url
                    extracted_data['scrape_success'] = True
                    
                    logger.info(f"Successfully scraped {competitor_name}")
                    return extracted_data
                
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url}, trying next user agent...")
                    continue
                    
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url}, trying next user agent...")
                continue
                
            except requests.exceptions.RequestException as e:
                if attempt < len(self.user_agents) - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}), trying next user agent...")
                    continue
                else:
                    logger.error(f"All scraping attempts failed for {url}: {str(e)}")
                    break
        
        # Strategy 2: Try Selenium (if available)
        if self._is_selenium_available():
            try:
                logger.info(f"Trying Selenium for {url}")
                return await self._scrape_with_selenium(url, competitor_name)
            except Exception as e:
                logger.error(f"Selenium scraping failed: {str(e)}")
        
        # Strategy 3: Try alternative URL (homepage)
        try:
            alt_url = self._get_alternative_url(url)
            if alt_url != url:
                logger.info(f"Trying alternative URL: {alt_url}")
                return await self._scrape_with_simple_request(alt_url, competitor_name)
        except Exception as e:
            logger.error(f"Alternative URL scraping failed: {str(e)}")
        
        # All strategies failed
        logger.error(f"Failed to scrape {url} after all attempts")
        return {
            'scraped_url': url,
            'scrape_success': False,
            'error': 'All scraping strategies failed',
            'features': [],
            'pricing': None,
            'target_audience': None,
            'key_benefits': [],
            'product_type': None
        }
    
    def _get_alternative_url(self, url: str) -> str:
        """
        Get alternative URL (homepage) if specific page fails
        """
        try:
            parsed = urlparse(url)
            # Return just the domain homepage
            return f"{parsed.scheme}://{parsed.netloc}"
        except:
            return url
    
    async def _scrape_with_selenium(
        self,
        url: str,
        competitor_name: str
    ) -> Dict[str, Any]:
        """
        Scrape using Selenium (bypasses most anti-bot protection)
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Setup headless Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={self.user_agents[0]}')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Get page source
                page_source = driver.page_source
                driver.quit()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                text_content = self._extract_text_content(soup)
                
                if len(text_content.strip()) < 100:
                    raise Exception("Insufficient content")
                
                # Extract with LLM
                extracted_data = await self._extract_with_llm(
                    text_content=text_content,
                    competitor_name=competitor_name,
                    url=url
                )
                
                extracted_data['scraped_url'] = url
                extracted_data['scrape_success'] = True
                extracted_data['scrape_method'] = 'selenium'
                
                return extracted_data
                
            except Exception as e:
                driver.quit()
                raise e
                
        except Exception as e:
            raise Exception(f"Selenium scraping failed: {str(e)}")
    
    async def _scrape_with_simple_request(
        self,
        url: str,
        competitor_name: str
    ) -> Dict[str, Any]:
        """
        Simple scraping without complex headers
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = self._extract_text_content(soup)
            
            if len(text_content.strip()) < 100:
                raise Exception("Insufficient content")
            
            extracted_data = await self._extract_with_llm(
                text_content=text_content,
                competitor_name=competitor_name,
                url=url
            )
            
            extracted_data['scraped_url'] = url
            extracted_data['scrape_success'] = True
            
            return extracted_data
            
        except Exception as e:
            raise Exception(f"Simple scraping failed: {str(e)}")
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract relevant text content from HTML
        Focus on main content, features, pricing sections
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = []
        
        # Look for common content containers
        content_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '#content', '.main-content',
            '.features', '.pricing', '.benefits',
            'section'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 50:  # Only include substantial content
                    main_content.append(text)
        
        # If no main content found, get all text
        if not main_content:
            main_content = [soup.get_text(separator=' ', strip=True)]
        
        # Combine and limit length
        full_text = ' '.join(main_content)
        
        # Clean up whitespace
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # Limit to first 3000 characters for LLM processing
        return full_text[:3000]
    
    async def _extract_with_llm(
        self,
        text_content: str,
        competitor_name: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Use LLM to extract structured data from scraped text
        """
        try:
            # Get API keys
            api_keys = self._get_api_keys()
            
            if not api_keys:
                logger.warning("No API keys available for LLM extraction")
                return self._fallback_extraction(text_content)
            
            # Create extraction prompt
            prompt = f"""
You are a data extraction expert. Extract structured information about this competitor product from their website content.

COMPETITOR: {competitor_name}
URL: {url}

WEBSITE CONTENT:
{text_content}

Extract the following information in JSON format:

1. **features**: List of 3-8 key features/capabilities (be specific, not generic)
2. **pricing**: Pricing information (e.g., "Free", "$9/month", "Starting at $49", "Enterprise pricing", "Contact for pricing")
3. **target_audience**: Who is this product for? (e.g., "Small businesses", "Developers", "Enterprise teams")
4. **key_benefits**: List of 2-5 main benefits/value propositions
5. **product_type**: Type of product (e.g., "SaaS", "Mobile App", "Desktop Software", "Open Source")

IMPORTANT:
- Only extract information that is clearly stated in the content
- If information is not found, use null or empty array
- Be concise and specific
- Focus on unique features, not generic ones

Return ONLY valid JSON in this exact format:
{{
    "features": ["feature1", "feature2", ...],
    "pricing": "pricing info or null",
    "target_audience": "audience description or null",
    "key_benefits": ["benefit1", "benefit2", ...],
    "product_type": "type or null"
}}
"""
            
            # Call LLM
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            model = "google/gemma-3-27b-it:free"
            
            for api_key in api_keys:
                try:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a data extraction expert. Extract structured product information and return only valid JSON."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                    
                    response = requests.post(api_url, headers=headers, json=payload, timeout=20)
                    
                    if response.status_code == 200:
                        output = response.json()["choices"][0]["message"]["content"].strip()
                        
                        # Try to parse JSON
                        try:
                            # Remove markdown code blocks if present
                            output = re.sub(r'```json\s*', '', output)
                            output = re.sub(r'```\s*$', '', output)
                            
                            data = json.loads(output)
                            
                            # Validate structure
                            if isinstance(data.get('features'), list):
                                logger.info(f"Successfully extracted data for {competitor_name}")
                                return data
                        except json.JSONDecodeError:
                            # Try to extract JSON from output
                            json_match = re.search(r'\{.*\}', output, re.DOTALL)
                            if json_match:
                                data = json.loads(json_match.group())
                                return data
                    
                except Exception as e:
                    logger.error(f"LLM extraction failed with key: {str(e)}")
                    continue
            
            # If all API keys failed, use fallback
            return self._fallback_extraction(text_content)
            
        except Exception as e:
            logger.error(f"LLM extraction error: {str(e)}")
            return self._fallback_extraction(text_content)
    
    def _fallback_extraction(self, text_content: str) -> Dict[str, Any]:
        """
        Fallback extraction using simple text analysis
        """
        text_lower = text_content.lower()
        
        # Try to find pricing
        pricing = None
        pricing_patterns = [
            r'\$\d+(?:\.\d{2})?(?:/month|/mo|/year|/yr)?',
            r'free',
            r'starting at \$\d+',
            r'contact (?:us )?for pricing'
        ]
        
        for pattern in pricing_patterns:
            match = re.search(pattern, text_lower)
            if match:
                pricing = match.group()
                break
        
        # Extract potential features (sentences with action words)
        feature_keywords = ['track', 'manage', 'create', 'automate', 'integrate', 'analyze', 'monitor', 'schedule']
        features = []
        
        sentences = text_content.split('.')
        for sentence in sentences[:20]:  # Check first 20 sentences
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in feature_keywords):
                if 10 < len(sentence) < 100:  # Reasonable length
                    features.append(sentence.strip())
                    if len(features) >= 5:
                        break
        
        return {
            'features': features[:5],
            'pricing': pricing,
            'target_audience': None,
            'key_benefits': [],
            'product_type': None,
            'extraction_method': 'fallback'
        }
    
    def _get_api_keys(self) -> List[str]:
        """Get OpenRouter API keys"""
        keys = []
        primary_key = os.getenv("OPENROUTER_API_KEY")
        if primary_key and "your-api-key-here" not in primary_key.lower():
            keys.append(primary_key)
        
        for i in range(2, 6):
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if key and "your-api-key-here" not in key.lower():
                keys.append(key)
        
        return keys


# Singleton instance
_web_scraper_service = None


def get_web_scraper() -> CompetitorWebScraper:
    """Get singleton instance of CompetitorWebScraper"""
    global _web_scraper_service
    if _web_scraper_service is None:
        _web_scraper_service = CompetitorWebScraper()
    return _web_scraper_service
