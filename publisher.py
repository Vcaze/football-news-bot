import os
import tweepy
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

def get_twitter_client():
    """Authenticates and returns a Tweepy v2 Client."""
    api_key = os.getenv("TWITTER_CONSUMER_KEY")
    api_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("WARNING: Twitter API keys are missing from environment.")
        return None

    try:
        # We use the v2 API Client for posting tweets
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        return client
    except Exception as e:
        print(f"Error authenticating with Twitter: {e}")
        return None

def post_tweet(text, link):
    """
    Posts a tweet to X using the authenticated client.
    Appends the link to the end of the generated text.
    """
    client = get_twitter_client()
    
    # Combine text and link
    final_tweet_text = f"{text}\n\n{link}"
    
    if client is None:
        print("ERROR: Cannot post tweet because Twitter client is not authenticated (keys missing or invalid).")
        return None

    try:
        # Posting to X
        print(f"Attempting to post tweet: {final_tweet_text[:50]}...")
        response = client.create_tweet(text=final_tweet_text)
        
        if not response or not response.data:
            print(f"Failed to post: No data returned in response. Response: {response}")
            return None
            
        tweet_id = response.data['id']
        print(f"Successfully posted tweet! ID: {tweet_id}")
        
        # Construct the URL
        tweet_url = f"https://twitter.com/anyuser/status/{tweet_id}"
        return tweet_url
    except Exception as e:
        print(f"Failed to post tweet due to exception: {e}")
        return None

if __name__ == "__main__":
    # Test publishing (This will do a dry run if keys aren't set)
    print("Testing publisher...")
    test_text = "🚨 Breaking: This is a test tweet from our new bot! #Test"
    test_link = "http://example.com/breaking-test"
    result = post_tweet(test_text, test_link)
    print(f"Result URL: {result}")
