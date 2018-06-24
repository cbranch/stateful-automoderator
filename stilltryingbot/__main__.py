#!/usr/bin/python
import re
import sqlite3
import sys
import time
from collections import namedtuple
from datetime import datetime
from string import Template

import praw
import yaml
from dateutil.relativedelta import *
import dateutil.parser

duration_re = re.compile(r'((?P<months>\d+?) ?months?)? *((?P<weeks>\d+?) ?weeks?)? *((?P<days>\d+?) ?days?)?')
def parse_duration(duration):
    parts = duration_re.match(duration)
    if not parts:
        return
    parts = parts.groupdict()
    return relativedelta(months=int(parts['months'] or '0'), weeks=int(parts['weeks'] or '0'), days=int(parts['days'] or '0'))

Post = namedtuple('Post', ['id', 'date', 'reddit_id'])
def get_saved_post_data(db):
    c = db.cursor()
    for row in c.execute('SELECT post_id, post_date, reddit_post_id FROM posts'):
        yield Post(row[0], dateutil.parser.parse(row[1]), row[2])

def save_post_data(db, post):
    c = db.cursor()
    c.execute("""INSERT OR REPLACE INTO posts (post_id, post_date, reddit_post_id)
               VALUES (?, ?, ?)""", (post.id, post.date.isoformat(), post.reddit_id))
    db.commit()

template_re = re.compile(r'{{(\w+)\s+([^}]+)}}')
def render_template_expression(matchobj):
    if matchobj.group(1) == "date":
        return time.strftime(matchobj.group(2))
    else:
        return matchobj.group(0)

def render_template(text):
    return template_re.sub(render_template_expression, text)

db = sqlite3.connect('posts.db')

if len(sys.argv) > 1 and sys.argv[1] == "--create":
    c = db.cursor()
    c.execute("""CREATE TABLE posts
                 (post_id TEXT PRIMARY KEY, post_date TEXT, reddit_post_id TEXT)""")
    db.commit()
    sys.exit(0)

dry_run = False
if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
    dry_run = True

reddit = praw.Reddit('bot1')

subreddit = reddit.subreddit("stilltrying")

current_time = datetime.now()

config_items = list(yaml.load_all(subreddit.wiki['stilltryingbot-config'].content_md))

for config in config_items:
    posts = list(get_saved_post_data(db))
    posts_by_id = {post.id: post for post in posts}
    next_post_time = datetime.strptime(config['first'], "%B %d, %Y %H:%M")
    repeat = parse_duration(config['repeat'])
    post = posts_by_id.get(config['id'])
    if post:
        while next_post_time < post.date:
            next_post_time += repeat
    if next_post_time > current_time:
        if dry_run:
            print "Not posting %s until %s" % (config['id'], next_post_time)
        continue
    post_template_data = {x['id']: "/" for x in config_items}
    post_template_data.update((post.id, "https://reddit.com/comments/%s/" % post.reddit_id) for post in posts)
    text = Template(config['text']).substitute(post_template_data)
    print "Submitting post %s" % (config['id'])
    if dry_run:
        print "I would submit the text: ", text
    else:
        reddit_post = subreddit.submit(title=render_template(config['title']), selftext=text, send_replies=False)
        reddit_post.mod.distinguish()
        if config.get('sticky', False):
            reddit_post.mod.sticky()
        save_post_data(db, Post(config['id'], current_time, reddit_post.id))
        print "Saved, post is %s" % reddit_post.id
