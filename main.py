import os
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from src.reddit import get_posts
from src.completions import get_completion
import schedule
from google import genai
import requests
import threading

# Load environment variables
load_dotenv()

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'genindex')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUBREDDIT = os.getenv('REDDIT_SUBREDDIT', 'NoStupidQuestions')
POST_LIMIT = int(os.getenv('REDDIT_POST_LIMIT', '100'))

grounding_url_lock = threading.Lock()

def get_url(uri: str) -> str:
    try:
        response = requests.get(uri, timeout=10)
        return response.url
    except Exception as e:
        print(f"Error getting URL from {uri}: {e}")
        return uri


def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )

def post_exists(conn, post_id):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM post WHERE id = %s", (post_id,))
        return cur.fetchone() is not None

def save_post(conn, post, response):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO post (id, url, title, content, text, response)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                post['id'],
                post['url'],
                post['title'],
                post['content'],
                post['text'],
                response.model_dump_json(),
            ),
        )
        
        for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
            domain = chunk.web.title
            uri = chunk.web.uri
            # url = get_url(uri)
            # TODO: get url from uri
            url = uri
            cur.execute(
                """
                INSERT INTO post_url (post_id, domain, url)
                VALUES (%s, %s, %s)
                """,
                (post['id'], domain, url),
            )
            
        for query in response.candidates[0].grounding_metadata.web_search_queries:
            cur.execute(
                """
                INSERT INTO post_query (post_id, query)
                VALUES (%s, %s)
                """,
                (post['id'], query),
            )
    conn.commit()

def process_reddit_posts():
    print("Fetching posts from Reddit...")
    try:
        posts = get_posts(SUBREDDIT, POST_LIMIT)
    except Exception as e:
        print(f"Error fetching posts from Reddit: {e}")
        return
    
    try:
        conn = get_db_conn()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error creating Gemini client: {e}")
        return
    
    new_count = 0
    for post in posts:
        if not post_exists(conn, post['id']):
            print(f"Processing post: {post['title']}")
            try:
                response = get_completion(client, post['text'])
                save_post(conn, post, response)
                new_count += 1
            except Exception as e:
                print(f"Error processing post {post['id']}: {e}")
        else:
            print(f"Skipping existing post: {post['title']}")
    conn.close()
    print(f"Done. {new_count} new posts processed.")

def update_grounding_urls():
    if not grounding_url_lock.acquire(blocking=False):
        print("Grounding URL updater is already running. Skipping this run.")
        return
    print("Starting grounding URL updater...")
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT id, url FROM post_url
                WHERE url LIKE %s
            """, ("https://vertexaisearch.cloud.google.com/grounding-api-redirect%",))
            rows = cur.fetchall()
            print(f"Found {len(rows)} URLs to update.")
            for row in rows:
                idx = row['id']
                url = row['url']
                try:
                    resolved_url = get_url(url)
                    if resolved_url != url:
                        cur.execute(
                            """
                            UPDATE post_url SET url = %s WHERE id = %s
                            """,
                            (resolved_url, idx)
                        )
                        print(f"Updated url={url} to {resolved_url}")
                except Exception as e:
                    print(f"Error updating url for post_url id={idx}: {e}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in update_grounding_urls: {e}")
    finally:
        grounding_url_lock.release()
        print("Grounding URL updater finished.")

def main():
    schedule.every(1).hours.do(process_reddit_posts)
    schedule.every(5).minutes.do(update_grounding_urls)
    print("Reddit fetcher started. Running every hour.")
    print("Grounding URL updater scheduled every 5 minutes.")
    update_grounding_urls()
    process_reddit_posts()  # Run once at startup
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()
