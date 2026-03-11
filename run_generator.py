import sys
from fetcher import fetch_latest_news
from generator import generate_tweet, score_article, IMPORTANCE_THRESHOLD
from queue_manager import add_to_queue
from github_notifier import notify_via_issue

# Max tweets to queue in a single run (hard cap to avoid spam)
MAX_TWEETS_PER_RUN = 5

def main():
    print("Starting Generator Job...")

    # Fetch the top 15 recent articles to score (cast a wide net)
    articles = fetch_latest_news(max_articles=15)

    if not articles:
        print("No new articles found. Exiting.")
        sys.exit(0)

    print(f"Fetched {len(articles)} new articles. Now scoring for importance...")
    
    queued_count = 0
    
    for article in articles:
        if queued_count >= MAX_TWEETS_PER_RUN:
            print(f"Reached max tweets per run ({MAX_TWEETS_PER_RUN}). Stopping.")
            break

        title = article['title']
        summary = article['summary']

        # 1. Score the article for importance
        score = score_article(title, summary)
        print(f"  Score {score}/10 -> {title[:60]}...")

        # 2. Skip if below the importance threshold
        if score < IMPORTANCE_THRESHOLD:
            print(f"  → Skipped (score {score} < threshold {IMPORTANCE_THRESHOLD})")
            continue

        # 3. Generate tweet text
        tweet_text = generate_tweet(title, summary)

        # 4. Add to the 10-minute queue
        queued_item = add_to_queue(tweet_text, article['source_url'], title)

        # 5. Send email notification via GitHub Issue
        notify_via_issue(
            tweet_text=tweet_text,
            source_url=article['source_url'],
            scheduled_time=queued_item['scheduled_for'],
            tweet_id=queued_item['id']
        )

        queued_count += 1
        print(f"  → Queued! ({queued_count} so far)")

    if queued_count == 0:
        print("No articles were important enough to tweet this hour.")
    else:
        print(f"\nGenerator Job complete. {queued_count} tweet(s) queued.")

if __name__ == "__main__":
    main()
