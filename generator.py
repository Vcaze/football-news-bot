import os
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    _key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=_key) if _key else None
except Exception:
    client = None

# Thresholds for the dual-queue system
AUTO_THRESHOLD = 8    # 8-10 = Automatic 10-min queue
MANUAL_THRESHOLD = 6  # 6-7 = Manual review (4h window)

SYSTEM_PROMPT = """
You are the social media manager for @FootballNewsC1.
Your job is to read a raw news article snippet and write an engaging, viral-style tweet about it.

RULES:
1. The tweet MUST be under 200 characters.
2. The tone should be excited and engaging. It should be like an X account, not like it's posted by a news site.
3. Include at least TWO relevant emojis.
4. Include exactly TWO relevant hashtags (e.g., #Football, #TransferNews, #PremierLeague).
5. Do NOT include a link - the system will add the link automatically.
6. Only output the tweet text, nothing else. No quotation marks.
7. If the article is about a match result, include the score in the tweet if available.
8. If the article includes multiple news items, only focus on the most important one.
9. Adjust the urgency of the tweet based on the "Importance Score" provided (1-10). 
   - For scores 9-10, use "BREAKING" or "🚨" or "HUGE NEWS" at the start.
   - For scores 6-8, use a standard engaging tone.
"""

SCORING_PROMPT = """
You are a football news editor. Rate the newsworthiness of the following football article on a scale of 1 to 10.

Scoring guide:
- 8-10: CRITICAL (Confirmed major transfers, manager sackings, huge match results, star player injuries)
- 6-7: IMPORTANT (Solid transfer rumours, standard match results, key squad news)
- 4-5: AVERAGE (Press conference quotes, minor injuries, training updates)
- 1-3: MINOR/NONE (Youth team news, generic stats, unverified tier-3 rumours, OR non-soccer sports)

CRITICAL RULES:
1. If the article is about American Football (NFL), Rugby, or any other sport that is NOT Association Football (Soccer), you MUST give it a score of 1.
2. If the article is a "Live" report, match preview, or rolling coverage of a game, give it a maximum score of 3.
3. If it is a generic "Transfer Gossip" or roundup without a confirmed major move, give it a maximum score of 5.
4. ONLY give 8-10 for TRULY "Breaking News" (e.g., "Official: Mbappe signs", "Klopp sacked").

Reply with ONLY a single integer from 1 to 10. Nothing else.
"""

def score_article(title, summary):
    """Uses AI to score the importance of an article from 1-10."""
    if not client:
        print("No OpenAI key - defaulting to importance score of 5.")
        return 5
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SCORING_PROMPT},
                {"role": "user", "content": f"Headline: {title}\nSummary: {summary[:300]}"}
            ],
            temperature=0.1,
            max_tokens=5
        )
        score_text = response.choices[0].message.content.strip()
        # Handle cases where AI might add a period or text
        score = int(''.join(filter(str.isdigit, score_text)))
        return max(1, min(10, score))
    except Exception as e:
        print(f"Error scoring article: {e}")
        return 5

def generate_tweet(article_title, article_summary, score):
    """Takes a news article and generates an engaging tweet using OpenAI."""
    if not client:
        print("WARNING: OPENAI_API_KEY not set. Using placeholder tweet.")
        return f"🚨 Breaking: {article_title[:100]}! #Football #News"
    try:
        print(f"Generating tweet for: {article_title} (Importance Score: {score}/10)")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Importance Score: {score}/10\nHeadline: {article_title}\nSummary: {article_summary}"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        tweet_text = response.choices[0].message.content.strip()
        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1]
        return tweet_text
    except Exception as e:
        print(f"Error generating tweet: {e}")
        return f"⚽ {article_title[:120]}... #FootballNews #Update"

if __name__ == "__main__":
    title = "Kylian Mbappe agrees to join Real Madrid on a free transfer"
    summary = "The French superstar has finally decided his future, signing a 5-year mega deal with the Spanish giants after leaving PSG."
    print(f"Score: {score_article(title, summary)}/10")
    print(f"Tweet: {generate_tweet(title, summary)}")
