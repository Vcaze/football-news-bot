import json
import os
import uuid
from datetime import datetime, timedelta

QUEUE_FILE = 'queue.json'
HISTORY_FILE = 'history.json'

def _load_json(filepath):
    """Utility to load a JSON file or return empty list if it doesn't exist."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save_json(filepath, data):
    """Utility to save data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def add_to_queue(tweet_text, source_url, article_title):
    """
    Adds a newly generated tweet to the queue, scheduled to be posted
    10 minutes from now.
    """
    queue = _load_json(QUEUE_FILE)
    
    # Calculate the exact time this should drop
    post_time = datetime.now() + timedelta(minutes=10)
    
    new_item = {
        "id": str(uuid.uuid4()),
        "tweet_text": tweet_text,
        "source_url": source_url,
        "article_title": article_title,
        "created_at": datetime.now().isoformat(),
        "scheduled_for": post_time.isoformat(),
        "status": "pending"
    }
    
    queue.append(new_item)
    _save_json(QUEUE_FILE, queue)
    print(f"Added item to queue (ID: {new_item['id']}). Scheduled for {new_item['scheduled_for']}")
    return new_item

def get_due_tweets():
    """
    Returns a list of tweets from the queue whose 'scheduled_for' time has passed
    and which haven't been cancelled.
    """
    queue = _load_json(QUEUE_FILE)
    due_tweets = []
    
    now = datetime.now()
    for item in queue:
        if item.get("status") == "pending":
            scheduled_time = datetime.fromisoformat(item["scheduled_for"])
            if now >= scheduled_time:
                due_tweets.append(item)
                
    return due_tweets

def move_to_history(tweet_id, posted_tweet_url=None):
    """
    Called after a tweet is successfully posted. Removes it from the queue
    and adds it to the history.json.
    """
    queue = _load_json(QUEUE_FILE)
    history = _load_json(HISTORY_FILE)
    
    # Find the item in the queue
    item_to_move = None
    remaining_queue = []
    
    for item in queue:
        if item["id"] == tweet_id:
            item_to_move = item
        else:
            remaining_queue.append(item)
            
    if item_to_move:
        # Update status and save to history
        item_to_move["status"] = "posted"
        item_to_move["posted_at"] = datetime.now().isoformat()
        if posted_tweet_url:
            item_to_move["posted_tweet_url"] = posted_tweet_url
            
        history.insert(0, item_to_move) # Add to top of history
        
        # Keep history file from getting infinitely large (max 50)
        history = history[:50]
        
        _save_json(QUEUE_FILE, remaining_queue)
        _save_json(HISTORY_FILE, history)
        print(f"Moved tweet {tweet_id} to history.")
        return True
    
    print(f"Error: Tweet {tweet_id} not found in queue.")
    return False

def cancel_tweet(tweet_id):
    """
    Called via the web dashboard. Removes a tweet from the queue so it is never posted.
    """
    queue = _load_json(QUEUE_FILE)
    remaining_queue = []
    found = False
    
    for item in queue:
        if item["id"] == tweet_id:
            found = True
            print(f"Tweet {tweet_id} cancelled and removed from queue.")
        else:
            remaining_queue.append(item)
            
    if found:
        _save_json(QUEUE_FILE, remaining_queue)
        return True
        
    return False

if __name__ == "__main__":
    # Test queue management
    print("Testing Queue Manager...")
    test_item = add_to_queue("This is a test tweet!", "http://example.com/test", "Test News")
    
    # Check due (should be empty since it's scheduled 10 min from now)
    due = get_due_tweets()
    print(f"Due tweets right now: {len(due)} (Expected: 0)")
    
    # Cancel it to clean up
    cancel_tweet(test_item['id'])
    
    print("Queue manager test complete.")
