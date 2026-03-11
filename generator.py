import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except:
    client = None

# The prompt instructions for the AI
SYSTEM_PROMPT = """
You are the social media manager for @FootballNewsC1.
Your job is to read a raw news article snippet and write an engaging, viral-style tweet about it.

RULES:
1. The tweet MUST be under 200 characters.
2. The tone should be excited, engaging, and professional.
3. Include exactly TWO relevant emojis.
4. Include exactly TWO relevant hashtags (e.g., #Football, #TransferNews, #PremierLeague).
5. Do NOT include a link or mention "Link below" - the system will add the link automatically.
6. Only output the text of the tweet, nothing else. No quotation marks.
"""

def generate_tweet(article_title, article_summary):
    """
    Takes an article title and summary, and uses OpenAI to generate a tweet.
    """
    try:
        if not client.api_key:
            print("WARNING: OPENAI_API_KEY is not set. Using a placeholder tweet for testing.")
            return f"🚨 Breaking: {article_title}! What are your thoughts on this? 👇 #Football #News"
            
        print(f"Generating tweet for: {article_title}")
        
        user_message = f"Headline: {article_title}\nSummary: {article_summary}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Fast and cheap model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7, # Slightly creative
            max_tokens=100
        )
        
        tweet_text = response.choices[0].message.content.strip()
        
        # Remove any quotes the AI might have accidentally added
        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1]
            
        return tweet_text
        
    except Exception as e:
        print(f"Error generating tweet: {e}")
        # Fallback tweet if API fails
        return f"⚽ News update: {article_title[:100]}... #FootballNews #Update"

if __name__ == "__main__":
    # Test generation
    title = "Kylian Mbappe agrees to join Real Madrid on a free transfer"
    summary = "The French superstar has finally decided his future, signing a 5-year mega deal with the Spanish giants after leaving PSG."
    
    print("Testing generator...")
    tweet = generate_tweet(title, summary)
    print("\nGenerated Tweet:")
    print("-" * 30)
    print(tweet)
    print("-" * 30)
    print(f"Length: {len(tweet)} characters (Allowed: 280)")
