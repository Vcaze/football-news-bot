import feedparser
import json
import os
import hashlib
from datetime import datetime

# Default RSS feeds (can be moved to a config file later if needed)
FEEDS = [
    "https://www.skysports.com/rss/12040", # Sky Sports Football
    "http://feeds.bbci.co.uk/sport/football/rss.xml", # BBC Sport Football
    "https://www.theguardian.com/football/rss" # Guardian Football
]

def get_history():
    """Load history.json to check for already processed articles."""
    if not os.path.exists('history.json'):
        return []
    try:
        with open('history.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def get_queue():
    """Load queue.json to check for articles currently pending."""
    if not os.path.exists('queue.json'):
        return []
    try:
        with open('queue.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def is_article_processed(article_url, article_title):
    """
    Check if an article exists in either the history or the current queue.
    Checks both URL (exact match) and Title (to prevent same news from different sites).
    """
    history = get_history()
    queue = get_queue()
    
    # Normalize title for comparison (lowercase and strip)
    target_title = article_title.lower().strip()
    
    # Check history
    for item in history:
        if item.get('source_url') == article_url:
            return True
        if item.get('article_title', '').lower().strip() == target_title:
            return True
            
    # Check queue
    for item in queue:
        if item.get('source_url') == article_url:
            return True
        if item.get('article_title', '').lower().strip() == target_title:
            return True
            
    return False

def fetch_latest_news(max_articles=3):
    """
    Fetch news from the RSS feeds and return a list of UNPROCESSED articles.
    Returns up to `max_articles` to avoid spamming the queue at once.
    """
    print(f"Fetching news from {len(FEEDS)} feeds...")
    new_articles = []
    
    for feed_url in FEEDS:
        print(f"Checking feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        # Check the top 5 most recent entries from this feed
        for entry in feed.entries[:5]:
            url = entry.link
            
            # Skip if we already tweeted about this exactly (URL or similar Title)
            if is_article_processed(url, entry.title):
                continue
                
            title = entry.title
            # Some feeds put the summary in 'summary', others in 'description'
            summary = entry.get('summary', '')
            
            # Clean up empty summaries if needed
            if not summary or len(summary) < 5:
                summary = "Breaking football news."
                
            article = {
                "title": title,
                "summary": summary,
                "source_url": url,
                "fetched_at": datetime.now().isoformat()
            }
            
            new_articles.append(article)
            
            if len(new_articles) >= max_articles:
                print(f"Found {len(new_articles)} new articles. Stopping fetch.")
                return new_articles

    print(f"Found {len(new_articles)} new articles total.")
    return new_articles

if __name__ == "__main__":
    # Test fetch functionality
    print("Testing fetcher...")
    articles = fetch_latest_news()
    for idx, a in enumerate(articles):
        print(f"\nArticle {idx+1}:")
        print(f"Title: {a['title']}")
        print(f"URL: {a['source_url']}")
