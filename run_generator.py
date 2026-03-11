import sys
from fetcher import fetch_latest_news
from generator import generate_tweet, score_article, AUTO_THRESHOLD, MANUAL_THRESHOLD
from queue_manager import add_to_queue
from github_notifier import notify_via_issue

# Max total items to process in a single run
MAX_ITEMS_PER_RUN = 5

def main():
    print("Starting Generator Job...")

    # Fetch more articles so we have a good pool for scoring
    articles = fetch_latest_news(max_articles=15)

    if not articles:
        print("No new articles found. Exiting.")
        sys.exit(0)

    print(f"Fetched {len(articles)} new articles. Scoring for importance...")
    
    queued_count = 0
    
    for article in articles:
        if queued_count >= MAX_ITEMS_PER_RUN:
            break

        title = article['title']
        summary = article['summary']

        # 1. Score the article
        score = score_article(title, summary)
        print(f"  Score {score}/10 -> {title[:60]}...")

        # 2. Determine queue type
        if score >= AUTO_THRESHOLD:
            q_type = 'auto'
            print("  → High Importance: Routing to Automatic Queue (10m)")
        elif score >= MANUAL_THRESHOLD:
            q_type = 'manual'
            print("  → Moderate Importance: Routing to Review Pool (4h)")
        else:
            print(f"  → Skipped (score {score} < {MANUAL_THRESHOLD})")
            continue

        # 3. Generate tweet text
        tweet_text = generate_tweet(title, summary)

        # 4. Add to the chosen queue type
        queued_item = add_to_queue(tweet_text, article['source_url'], title, q_type=q_type)

        # 5. Only send email for 'auto' items to avoid email spam
        if q_type == 'auto':
            notify_via_issue(
                tweet_text=tweet_text,
                source_url=article['source_url'],
                scheduled_time=queued_item['scheduled_for'],
                tweet_id=queued_item['id']
            )

        queued_count += 1
        print(f"  → Queued as {q_type.upper()}!")

    print(f"\nGenerator Job complete. {queued_count} item(s) processed.")

if __name__ == "__main__":
    main()
