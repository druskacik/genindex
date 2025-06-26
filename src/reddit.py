
import os
import praw

from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
user_agent = os.getenv("REDDIT_USER_AGENT")

reddit = praw.Reddit(
	client_id=client_id,
	client_secret=client_secret,
	user_agent=user_agent,
)

def get_posts(subreddit: str, limit: int = 100) -> list[dict]:
    posts = []
    for submission in reddit.subreddit(subreddit).hot(limit=limit):
        if not submission.stickied:
            posts.append({
                'id': submission.id,
                'url': submission.url,
                'title': submission.title,
                'content': submission.selftext,
                'text': f"{submission.title}\n\n{submission.selftext}",
            })
    return posts