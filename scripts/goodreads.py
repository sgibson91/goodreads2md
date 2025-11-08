import os
import platform
import re
import string
import tempfile
from datetime import datetime as dt
from pathlib import Path

import feedparser
import jinja2


def remove_punctuation(input_string):
    regex_pattern = f"[{re.escape(string.punctuation)}]"
    return re.sub(regex_pattern, "", input_string)


def get_subtitle(title):
    return title.split(":")[1].strip()


def get_series_info(title):
    match = re.fullmatch(r".+ \(((.+?),? #(\d+))\)", title)
    series_name = remove_punctuation(match.group(2))

    return (
        "(" + match.group(1) + ")",
        series_name.strip(),
        match.group(3),
    )


def get_clean_book_info(book_title):
    if ("(" in book_title) and ("#" in book_title):
        series, series_name, series_num = get_series_info(book_title)
        book_title = book_title.replace(series, "")
    else:
        series = series_name = series_num = ""

    if ":" in book_title:
        subtitle = get_subtitle(book_title)
        book_title = book_title.replace(subtitle, "")
    else:
        subtitle = ""

    book_title = remove_punctuation(book_title)
    return book_title.strip(), subtitle, series_name, series_num


def get_clean_shelf(shelf):
    if shelf.startswith("to-read-"):
        shelf = "to-read"
    elif shelf.startswith("read-"):
        shelf = "read"
    return shelf


def generate_metadata(entry):
    status = get_clean_shelf(shelf)
    title, subtitle, series, series_num = get_clean_book_info(entry.title)

    try:
        read_at = dt.strptime(entry.user_read_at, "%a, %d %b %Y %H:%M:%S %z")
        read_at = read_at.strftime("%Y-%m-%d")
    except ValueError:
        read_at = ""

    metadata_vars = {
        "authors": [entry.author_name],
        "book_id": entry.book_id,
        "cover_url": entry.book_large_image_url,
        "date-last-read": read_at,
        "format": [
            fmt.replace("format-", "")
            for fmt in entry.user_shelves.split(", ")
            if fmt.startswith("format")
        ],
        "genre": "non-fiction" if "non-fiction" in entry.user_shelves else "fiction",
        "owned": "true" if "owned" in entry.user_shelves else "false",
        "rating": int(entry.user_rating) if int(entry.user_rating) > 0 else "",
        "re-read": "true" if "re-read" in entry.user_shelves else "false",
        "series-name": series,
        "series-number": series_num,
        "status": status,
        "subtitle": subtitle,
    }

    return title, metadata_vars


# Set paths
ROOT = Path(__file__).parent.parent
TMP_DIR = Path(
    "/tmp" if platform.system() == "Darwin" else tempfile.gettempdir()
).joinpath("books")

if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# Read in the template file with Jinja
with open(ROOT.joinpath("templates", "template-book.md")) as f:
    template = jinja2.Template(f.read())

# Read in Goodreads shelves to query
with open(ROOT.joinpath("resources", "goodreads-shelves.txt")) as f:
    shelves = [line.strip("\n") for line in f.readlines()]

CI = os.getenv("CI", False)
if not CI:
    from dotenv import load_dotenv

    load_dotenv()

# Read in necessary environment variables
GOODREADS_RSS_KEY = os.getenv("GOODREADS_RSS_KEY")
GOODREADS_USER_ID = os.getenv("GOODREADS_USER_ID")

# Construct Goodreads RSS base URL
gr_rss_base_url = f"https://www.goodreads.com/review/list_rss/{GOODREADS_USER_ID}?key={GOODREADS_RSS_KEY}&shelf="

# Retrieve all the books in the Goodreads RSS feeds for each shelf
for shelf in shelves:
    feed = feedparser.parse(gr_rss_base_url + shelf)
    for entry in feed.entries:
        title, metadata = generate_metadata(entry)

        markdown = template.render(**metadata)
        with open(TMP_DIR.joinpath(f"{title}.md"), "w") as f:
            f.write(markdown)
