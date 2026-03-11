import sys
from queue_manager import get_due_tweets, move_to_history
from publisher import post_tweet

def main():
    print("Starting Publisher Job...")
    
    # 1. Get all tweets where current_time >= scheduled_time
    due_tweets = get_due_tweets()
    
    if not due_tweets:
        print("No tweets are due for posting. Exiting.")
        sys.exit(0)
        
    print(f"Found {len(due_tweets)} tweet(s) due for posting.")
    
    # 2. Process each due tweet
    for item in due_tweets:
        print(f"\nProcessing Tweet ID: {item['id']}")
        
        # 3. Post to Twitter
        tweet_url = post_tweet(item['tweet_text'], item['source_url'])
        
        # 4. If successful (or dry-run successful), move to history
        if tweet_url:
            move_to_history(item['id'], tweet_url)
        else:
            print(f"Failed to post Tweet ID: {item['id']}. Leaving in queue.")

    print("\nPublisher Job completed.")

if __name__ == "__main__":
    main()
