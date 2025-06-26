import requests

def get_posts(subreddit: str, limit: int = 100) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}.json?limit={limit}"
    response = requests.get(url, headers={'User-agent': 'genindex'})
    res = response.json()

    posts = []
    for post in res['data']['children']:
        if not post['data']['stickied']:
            title = post['data']['title']
            content = post['data']['selftext']
            text = f"{title}\n\n{content}"
            posts.append({
                'id': post['data']['id'],
                'url': f"https://www.reddit.com{post['data']['permalink']}",
                'title': title,
                'content': content,
                'text': text,
            })
            
    return posts