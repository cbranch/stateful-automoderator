import sqlite3
import dateutil.parser
from collections import namedtuple

Post = namedtuple('Post', ['id', 'date', 'reddit_id'])

class PostDB:
    def __init__(self, db_name):
        self.db = sqlite3.connect(db_name)

    def get_saved_post_data(self):
        c = self.db.cursor()
        for row in c.execute('SELECT post_id, post_date, reddit_post_id FROM posts'):
            yield Post(row[0], dateutil.parser.parse(row[1]), row[2])

    def save_post_data(self, post):
        c = self.db.cursor()
        c.execute("""INSERT OR REPLACE INTO posts (post_id, post_date, reddit_post_id)
                VALUES (?, ?, ?)""", (post.id, post.date.isoformat(), post.reddit_id))
        self.db.commit()

    def create(self):
        c = self.db.cursor()
        c.execute("""CREATE TABLE posts
                    (post_id TEXT PRIMARY KEY, post_date TEXT, reddit_post_id TEXT)""")
        self.db.commit()
