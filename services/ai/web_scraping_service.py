import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path

from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance

logger = get_logger(__name__)

@dataclass
class ScrapedArticle:
    """Data class for scraped article information"""
    title: str
    content: str
    url: str
    source: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None
    language: str = "ar"
    scraped_at: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()

class WebScrapingService:
    """
    Web scraping service for Syrian news agencies and government websites.
    
    Supports:
    - SANA (Syrian Arab News Agency)
    - Halab Today
    - Syria TV
    - Syrian government websites
    - Rate limiting and respectful scraping
    - Content deduplication
    - Arabic content processing
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 2.0  # seconds between requests
        self.max_retries = 3
        self.timeout = 30
        self.max_concurrent_requests = 5
        self.scraped_urls: Set[str] = set()
        self.last_request_time = 0
        
        # Syrian news sources configuration
        self.news_sources = {
            "sana": {
                "base_url": "https://www.sana.sy",
                "article_selector": "article, .news-item, .post",
                "title_selector": "h1, h2, .title, .headline",
                "content_selector": ".content, .article-content, .post-content, .text",
                "date_selector": ".date, .published, time",
                "author_selector": ".author, .byline",
                "category_selector": ".category, .section",
                "language": "ar"
            },
            "halab_today": {
                "base_url": "https://halabtoday.tv",
                "article_selector": "article, .news-item, .post",
                "title_selector": "h1, h2, .title, .headline",
                "content_selector": ".content, .article-content, .post-content, .text",
                "date_selector": ".date, .published, time",
                "author_selector": ".author, .byline",
                "category_selector": ".category, .section",
                "language": "ar"
            },
            "syria_tv": {
                "base_url": "https://www.syria.tv",
                "article_selector": "article, .news-item, .post",
                "title_selector": "h1, h2, .title, .headline",
                "content_selector": ".content, .article-content, .post-content, .text",
                "date_selector": ".date, .published, time",
                "author_selector": ".author, .byline",
                "category_selector": ".category, .section",
                "language": "ar"
            },
            "government": {
                "base_url": "https://www.egov.sy",
                "article_selector": "article, .news-item, .announcement",
                "title_selector": "h1, h2, .title, .headline",
                "content_selector": ".content, .article-content, .announcement-content",
                "date_selector": ".date, .published, time",
                "author_selector": ".author, .byline",
                "category_selector": ".category, .section",
                "language": "ar"
            }
        }
        
        # Headers to mimic a real browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Content filters for quality
        self.min_content_length = 100
        self.max_content_length = 50000
        self.blocked_words = ["advertisement", "ad", "sponsored", "cookie", "privacy policy"]
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
        
    async def initialize(self):
        """Initialize the scraping service"""
        log_function_entry(logger, "initialize")
        start_time = time.time()
        
        try:
            connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            duration = time.time() - start_time
            log_performance(logger, "Web scraping service initialization", duration)
            log_function_exit(logger, "initialize", duration=duration)
            
            logger.info("✅ Web scraping service initialized successfully")
            
        except Exception as e:
            duration = time.time() - start_time
            log_function_exit(logger, "initialize", duration=duration)
            logger.error(f"❌ Failed to initialize web scraping service: {e}")
            raise
            
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            logger.info("🧹 Web scraping service cleaned up")
            
    async def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    async def scrape_news_sources(self, sources: List[str] = None, max_articles: int = 50) -> Dict[str, Any]:
        """
        Scrape multiple news sources for recent articles.
        
        Args:
            sources: List of source names to scrape (default: all sources)
            max_articles: Maximum number of articles to scrape per source
            
        Returns:
            Dictionary with scraping results and articles
        """
        log_function_entry(logger, "scrape_news_sources", sources=sources, max_articles=max_articles)
        start_time = time.time()
        
        if not self.session:
            await self.initialize()
            
        if sources is None:
            sources = list(self.news_sources.keys())
            
        results = {
            "status": "success",
            "total_articles": 0,
            "sources_scraped": [],
            "articles": [],
            "errors": []
        }
        
        try:
            # Scrape each source
            for source_name in sources:
                if source_name not in self.news_sources:
                    results["errors"].append(f"Unknown source: {source_name}")
                    continue
                    
                source_config = self.news_sources[source_name]
                logger.info(f"🔍 Scraping {source_name} from {source_config['base_url']}")
                
                try:
                    source_articles = await self._scrape_source(
                        source_name, 
                        source_config, 
                        max_articles
                    )
                    
                    results["articles"].extend(source_articles)
                    results["total_articles"] += len(source_articles)
                    results["sources_scraped"].append({
                        "source": source_name,
                        "articles_count": len(source_articles),
                        "url": source_config["base_url"]
                    })
                    
                    logger.info(f"✅ Scraped {len(source_articles)} articles from {source_name}")
                    
                except Exception as e:
                    error_msg = f"Failed to scrape {source_name}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    
                # Rate limiting between sources
                await self._rate_limit()
                
            duration = time.time() - start_time
            log_performance(logger, "News sources scraping", duration, 
                          total_articles=results["total_articles"], 
                          sources_count=len(results["sources_scraped"]))
            log_function_exit(logger, "scrape_news_sources", result=results, duration=duration)
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            log_function_exit(logger, "scrape_news_sources", duration=duration)
            logger.error(f"❌ News scraping failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "total_articles": 0,
                "sources_scraped": [],
                "articles": [],
                "errors": [str(e)]
            }
            
    async def _scrape_source(self, source_name: str, source_config: Dict, max_articles: int) -> List[ScrapedArticle]:
        """Scrape a single news source"""
        articles = []
        
        try:
            # Get the main page
            main_page_url = source_config["base_url"]
            main_page_content = await self._fetch_page(main_page_url)
            
            if not main_page_content:
                return articles
                
            # Parse the main page
            soup = BeautifulSoup(main_page_content, 'html.parser')
            
            # Find article links
            article_links = self._extract_article_links(soup, source_config)
            
            # Limit the number of articles to process
            article_links = article_links[:max_articles]
            
            # Scrape each article
            for link in article_links:
                try:
                    article = await self._scrape_article(link, source_name, source_config)
                    if article:
                        articles.append(article)
                        
                    # Rate limiting between articles
                    await self._rate_limit()
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape article {link}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scrape source {source_name}: {e}")
            
        return articles
        
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page with retries"""
        for attempt in range(self.max_retries):
            try:
                await self._rate_limit()
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    elif response.status == 404:
                        logger.warning(f"Page not found: {url}")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1} for {url}: {e}")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
        return None
        
    def _extract_article_links(self, soup: BeautifulSoup, source_config: Dict) -> List[str]:
        """Extract article links from the main page"""
        links = []
        base_url = source_config["base_url"]
        
        # Find all links that might be articles
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            elif not href.startswith('http'):
                href = urljoin(base_url, href)
                
            # Check if this looks like an article link
            if self._is_article_link(href, source_config):
                links.append(href)
                
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
                
        return unique_links
        
    def _is_article_link(self, url: str, source_config: Dict) -> bool:
        """Check if a URL looks like an article link"""
        # Skip if already scraped
        if url in self.scraped_urls:
            return False
            
        # Check if URL is from the same domain
        parsed_url = urlparse(url)
        parsed_base = urlparse(source_config["base_url"])
        
        if parsed_url.netloc != parsed_base.netloc:
            return False
            
        # Check for article-like patterns in the URL
        article_patterns = [
            r'/news/', r'/article/', r'/post/', r'/story/',
            r'/arabic/', r'/ar/', r'/en/',
            r'\d{4}/\d{2}/\d{2}',  # Date patterns
            r'\d+$'  # Ends with number
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
                
        return False
        
    async def _scrape_article(self, url: str, source_name: str, source_config: Dict) -> Optional[ScrapedArticle]:
        """Scrape a single article"""
        try:
            content = await self._fetch_page(url)
            if not content:
                return None
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract article data
            title = self._extract_title(soup, source_config["title_selector"])
            article_content = self._extract_content(soup, source_config["content_selector"])
            published_date = self._extract_date(soup, source_config["date_selector"])
            author = self._extract_author(soup, source_config["author_selector"])
            category = self._extract_category(soup, source_config["category_selector"])
            
            # Validate content quality
            if not self._is_valid_article(title, article_content):
                return None
                
            # Clean and process content
            title = self._clean_text(title)
            article_content = self._clean_text(article_content)
            
            # Extract tags/keywords
            tags = self._extract_tags(soup, title, article_content)
            
            # Create article object
            article = ScrapedArticle(
                title=title,
                content=article_content,
                url=url,
                source=source_name,
                published_date=published_date,
                author=author,
                category=category,
                tags=tags,
                language=source_config["language"]
            )
            
            # Mark as scraped
            self.scraped_urls.add(url)
            
            return article
            
        except Exception as e:
            logger.warning(f"Failed to scrape article {url}: {e}")
            return None
            
    def _extract_title(self, soup: BeautifulSoup, selector: str) -> str:
        """Extract article title"""
        for sel in selector.split(', '):
            element = soup.select_one(sel.strip())
            if element:
                return element.get_text(strip=True)
        return ""
        
    def _extract_content(self, soup: BeautifulSoup, selector: str) -> str:
        """Extract article content"""
        content_parts = []
        
        for sel in selector.split(', '):
            elements = soup.select(sel.strip())
            for element in elements:
                # Remove script and style elements
                for script in element(["script", "style"]):
                    script.decompose()
                    
                text = element.get_text(separator=' ', strip=True)
                if text:
                    content_parts.append(text)
                    
        return ' '.join(content_parts)
        
    def _extract_date(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract publication date"""
        for sel in selector.split(', '):
            element = soup.select_one(sel.strip())
            if element:
                # Try to get datetime attribute first
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    return datetime_attr
                    
                # Otherwise get text content
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
        
    def _extract_author(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract article author"""
        for sel in selector.split(', '):
            element = soup.select_one(sel.strip())
            if element:
                return element.get_text(strip=True)
        return None
        
    def _extract_category(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract article category"""
        for sel in selector.split(', '):
            element = soup.select_one(sel.strip())
            if element:
                return element.get_text(strip=True)
        return None
        
    def _extract_tags(self, soup: BeautifulSoup, title: str, content: str) -> List[str]:
        """Extract tags/keywords from article"""
        tags = []
        
        # Look for tag elements
        tag_elements = soup.find_all(['a', 'span', 'div'], class_=re.compile(r'tag|keyword|category'))
        for element in tag_elements:
            tag_text = element.get_text(strip=True)
            if tag_text and len(tag_text) > 2:
                tags.append(tag_text)
                
        # Extract keywords from title and content
        text = f"{title} {content}"
        keywords = self._extract_keywords(text)
        tags.extend(keywords)
        
        # Remove duplicates and limit
        return list(set(tags))[:10]
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using simple heuristics"""
        # Common Arabic keywords related to Syria
        arabic_keywords = [
            "سوريا", "دمشق", "حلب", "حمص", "حماة", "اللاذقية", "طرطوس",
            "الحكومة", "الرئيس", "الوزارة", "البرلمان", "الجيش", "الاقتصاد",
            "التعليم", "الصحة", "البنية التحتية", "السياحة", "الزراعة",
            "النفط", "الغاز", "التجارة", "الاستثمار", "التنمية"
        ]
        
        found_keywords = []
        for keyword in arabic_keywords:
            if keyword in text:
                found_keywords.append(keyword)
                
        return found_keywords
        
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove blocked words
        for word in self.blocked_words:
            text = re.sub(re.escape(word), '', text, flags=re.IGNORECASE)
            
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        
        return text.strip()
        
    def _is_valid_article(self, title: str, content: str) -> bool:
        """Check if article content is valid and of good quality"""
        if not title or not content:
            return False
            
        if len(content) < self.min_content_length:
            return False
            
        if len(content) > self.max_content_length:
            return False
            
        # Check for blocked content
        text_lower = (title + " " + content).lower()
        for word in self.blocked_words:
            if word in text_lower:
                return False
                
        return True
        
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about scraping activity"""
        return {
            "total_urls_scraped": len(self.scraped_urls),
            "scraped_urls": list(self.scraped_urls),
            "rate_limit_delay": self.rate_limit_delay,
            "max_concurrent_requests": self.max_concurrent_requests,
            "available_sources": list(self.news_sources.keys())
        }
        
    async def clear_scraped_urls(self):
        """Clear the list of scraped URLs"""
        self.scraped_urls.clear()
        logger.info("🧹 Cleared scraped URLs cache")

# Global web scraping service instance
web_scraping_service = WebScrapingService()
