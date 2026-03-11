import sys
from queue_manager import get_due_tweets, move_to_history, cleanup_expired_items
from publisher import post_tweet

def main():
    print("Starting Publisher & Cleanup Job...")
    
    # 1. Cleanup expired manual review items (4h window) or auto items that somehow got lost
    cleanup_expired_items()
    
    # 2. Get all 'auto' tweets where current_time >= scheduled_time
    due_tweets = get_due_tweets()
    
    if not due_tweets:
        print("No automatic tweets are due for posting. Exiting.")
        sys.exit(0)
        
    print(f"Found {len(due_tweets)} automatic tweet(s) due for posting.")
    
    # 3. Process each due tweet
    for item in due_tweets:
        print(f"\nProcessing Tweet ID: {item['id']}")
        
        # 4. Post to Twitter
        tweet_url = post_tweet(item['tweet_text'], item['source_url'])
        
        # 5. If successful, move to history
        if tweet_url:
            move_to_history(item['id'], tweet_url)
        else:
            print(f"Failed to post Tweet ID: {item['id']}. Leaving in queue.")

    print("\nPublisher Job completed.")

if __name__ == "__main__":
    main()
