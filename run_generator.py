import sys
from fetcher import fetch_latest_news
from generator import generate_tweet
from queue_manager import add_to_queue
from github_notifier import notify_via_issue

def main():
    print("Starting Generator Job...")
    
    # 1. Fetch exactly 1 new, unplugged article (to avoid queuing too many at once)
    articles = fetch_latest_news(max_articles=1)
    
    if not articles:
        print("No new articles found. Exiting.")
        sys.exit(0)
        
    article = articles[0]
    print(f"Processing article: {article['title']}")
    
    # 2. Generate the Tweet text via AI
    tweet_text = generate_tweet(article['title'], article['summary'])
    
    # 3. Add it to the 10-minute queue
    queued_item = add_to_queue(tweet_text, article['source_url'], article['title'])
    
    # 4. Notify the user via email/GitHub Issue
    notify_via_issue(
        tweet_text=tweet_text,
        source_url=article['source_url'],
        scheduled_time=queued_item['scheduled_for'],
        tweet_id=queued_item['id']
    )
    
    print("Generator Job completed successfully.")

if __name__ == "__main__":
    main()
