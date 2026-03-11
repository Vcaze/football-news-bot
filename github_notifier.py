import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

def notify_via_issue(tweet_text, source_url, scheduled_time, tweet_id):
    """
    Creates a GitHub Issue in the repository running this action.
    This triggers GitHub's built-in email notification system.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY") # Automatically set by GitHub Actions
    
    if not token or not repo_name:
        print("[DRY RUN / ERROR] GitHub Token or Repo Name not set. Cannot create issue.")
        print(f"Would have notified about: {tweet_text}")
        return False
        
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        title = f"🕒 Queued Tweet: {tweet_text[:40]}..."
        
        body = f"""
## A new Tweet is queued to be posted!

The bot has successfully fetched news and generated a tweet. It will be posted automatically at: **{scheduled_time}** (in 10 minutes).

### The Tweet:
> {tweet_text}

**Source Article:** {source_url}

---

### Need to cancel?
If you do not want this tweet to go out, you have 10 minutes to click the **Cancel** button on your Monitoring Dashboard.

*Internal Tracking ID: {tweet_id}*
"""
        
        issue = repo.create_issue(title=title, body=body, labels=['queued'])
        print(f"Successfully created GitHub Issue #{issue.number} for notification.")
        return True
        
    except Exception as e:
        print(f"Failed to create GitHub Issue: {e}")
        return False

if __name__ == "__main__":
    print("Testing GitHub Notifier...")
    notify_via_issue("This is a test tweet!", "http://example.com/test", "12:00 PM", "test-id-123")
