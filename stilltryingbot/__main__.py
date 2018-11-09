#!/usr/bin/python
import argparse
import praw
import sys
import yaml
from datetime import datetime
from string import Template

from db import Post, PostDB
from duration import parse_duration
from template import render_template

def run_scheduler(db, praw_id, subreddit_name, wiki_config_page, dry_run=False):
    reddit = praw.Reddit(praw_id)
    subreddit = reddit.subreddit(subreddit_name)
    wiki_config = subreddit.wiki[wiki_config_page].content_md

    config_items = list(yaml.load_all(wiki_config))

    current_time = datetime.now()

    for config in config_items:
        posts = list(db.get_saved_post_data())
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
            db.save_post_data( Post(config['id'], current_time, reddit_post.id))
            print "Saved, post is %s" % reddit_post.id

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", help="Show the actions that would be performed without doing them", action="store_true")
parser.add_argument("--create", help="Create the database for the first run", action="store_true")
parser.add_argument("--db", help="File used for the post database")
parser.add_argument("--praw-id", help="Select the PRAW account ID to use")
parser.add_argument("--subreddit", help="The subreddit to post to")
parser.add_argument("--wiki-page", help="The wiki page on the subreddit that specifies the post configuration")
args = parser.parse_args()

db = PostDB(args.db)

if args.create:
    db.create()
    sys.exit(0)

run_scheduler(db, args.praw_id, args.subreddit, args.wiki_page, args.dry_run)
