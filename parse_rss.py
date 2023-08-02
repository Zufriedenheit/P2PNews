import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import os
import feedparser
import time

def fetch_website(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise ValueError(f"Failed to fetch website. Status code: {response.status_code}")

def create_atom_feed(existing_entries, new_entries):
    fg = FeedGenerator()
    fg.title("P2P Empire")
    fg.link(href="https://p2pempire.com/en/newsfeed", rel="alternate")
    fg.language("en")
    fg.id('https://p2pempire.com/en/newsfeed')

    all_entries = existing_entries + new_entries
    entry_ids = set()  # To store unique entry IDs

    for entry in all_entries:
        # Convert the date to UTC
        utc_date = entry['date'].astimezone(pytz.utc)
        
        # Use a combination of the title and date as the unique identifier
        entry_id = f"{entry['title']} - {utc_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        
        # Check if the entry ID already exists
        if entry_id not in entry_ids:
            fe = fg.add_entry()
            fe.title(entry['title'])
            fe.link(href=entry['link'])

            # Ensure date is in the correct format and timezone (UTC)
            fe.published(utc_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            
            fe.description(entry['paragraph'])
            fe.id(entry_id)

            entry_ids.add(entry_id)  # Add the entry ID to the set to avoid duplicates
    
    return fg


def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    news_boxes = soup.find_all('div', class_='news-box-wrapper')

    entries = []
    for box in news_boxes:
        date_str = box.find('div', class_='news-date').span.text.strip()
        title = box.find('h2').text.strip()
        paragraph = box.find('p').text.strip()
        link = box.find('a', href=True)['href']
        date = datetime.strptime(date_str, "%d. %B %Y")
        date = date.replace(tzinfo=pytz.utc)

        entries.append({
            'date': date,
            'date_str': date_str,
            'title': title,
            'paragraph': paragraph,
            'link': link,
        })
    return entries

def read_existing_entries(feed_file_path):
    if os.path.exists(feed_file_path):
        feed = feedparser.parse(feed_file_path)
        return [{
            'date': datetime(*entry['published_parsed'][:6]).replace(tzinfo=pytz.utc),
            'date_str': datetime.utcfromtimestamp(time.mktime(entry['published_parsed'])).strftime("%d. %B %Y"),
            'title': entry['title'],
            'paragraph': entry['summary'],
            'link': entry['link']
        } for entry in feed.entries]
    else:
        return []

def main():
    url = 'https://p2pempire.com/en/newsfeed'
    html_content = fetch_website(url)
    new_entries = parse_html(html_content)

    feed_file_path = "P2PEmpire.xml"
    existing_entries = read_existing_entries(feed_file_path)

    atom_feed = create_atom_feed(existing_entries, new_entries)
    atom_feed.atom_file(feed_file_path, pretty=True)

if __name__ == '__main__':
    main()
