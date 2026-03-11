import json
import os
import uuid
from datetime import datetime, timedelta

QUEUE_FILE = 'queue.json'
HISTORY_FILE = 'history.json'

def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def add_to_queue(tweet_text, source_url, article_title, q_type='auto'):
    """
    Adds a tweet to the queue.
    q_type='auto': 10-minute automatic wait (scheduled_for).
    q_type='manual': 4-hour review pool (expires_at, no automatic posting).
    """
    queue = load_data(QUEUE_FILE)
    
    now = datetime.now()
    
    # Calculate scheduling/expiration
    if q_type == 'auto':
        # 10 minutes from now
        scheduled_for = (now + timedelta(minutes=10)).isoformat()
        expires_at = (now + timedelta(hours=1)).isoformat() # Backup expiry
    else:
        # Manual review pool - expires in 4 hours
        scheduled_for = None
        expires_at = (now + timedelta(hours=4)).isoformat()

    item = {
        "id": str(uuid.uuid4())[:8],
        "tweet_text": tweet_text,
        "source_url": source_url,
        "article_title": article_title,
        "created_at": now.isoformat(),
        "scheduled_for": scheduled_for,
        "expires_at": expires_at,
        "type": q_type,
        "status": "pending"
    }
    
    queue.append(item)
    save_data(QUEUE_FILE, queue)
    return item

def get_due_tweets():
    """Returns only 'auto' tweets that have passed their scheduled_for time."""
    queue = load_data(QUEUE_FILE)
    now = datetime.now().isoformat()
    return [i for i in queue if i.get('type') == 'auto' and i.get('scheduled_for') and i['scheduled_for'] <= now]

def remove_from_queue(tweet_id):
    queue = load_data(QUEUE_FILE)
    new_queue = [i for i in queue if i['id'] != tweet_id]
    save_data(QUEUE_FILE, new_queue)
    return len(queue) > len(new_queue)

def move_to_history(tweet_id, posted_tweet_url):
    queue = load_data(QUEUE_FILE)
    history = load_data(HISTORY_FILE)
    
    tweet = next((i for i in queue if i['id'] == tweet_id), None)
    if not tweet:
        return False
        
    # Update tweet details
    tweet['status'] = 'posted'
    tweet['posted_at'] = datetime.now().isoformat()
    tweet['posted_tweet_url'] = posted_tweet_url
    
    # Add to beginning of history and keep last 50
    history.insert(0, tweet)
    history = history[:50]
    
    # Remove from queue
    new_queue = [i for i in queue if i['id'] != tweet_id]
    
    save_data(QUEUE_FILE, new_queue)
    save_data(HISTORY_FILE, history)
    return True

def cleanup_expired_items():
    """Removes any items that have passed their expires_at time."""
    queue = load_data(QUEUE_FILE)
    now = datetime.now().isoformat()
    
    new_queue = [i for i in queue if i.get('expires_at', '') > now]
    if len(new_queue) < len(queue):
        print(f"Cleaned up {len(queue) - len(new_queue)} expired items.")
        save_data(QUEUE_FILE, new_queue)
        return True
    return False
