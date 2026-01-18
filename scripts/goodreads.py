import logging
import os
import re
import string
from datetime import datetime as dt
from io import StringIO
from pathlib import Path

import feedparser
import jinja2
import yaml
from html_to_markdown import convert

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="/var/log/goodreads2md.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

vals = {
    "true": True,
    "false": False,
}


def read_frontmatter(lines):
    """
    Read YAML frontmatter from a Markdown file.
    YAML must be fenced with `---`.
    """
    if not lines or not lines[0].strip() == "---":
        return None  # no frontmatter

    yaml_lines = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        yaml_lines.append(line)

    return yaml.safe_load("".join(yaml_lines))


def dict_diff(a, b):
    """Establish the differences between two dictionaries."""
    a = {k.replace("-", "_"): v for k, v in a.items()}
    b = {k.replace("-", "_"): v for k, v in b.items()}

    a = {
        k: (vals[v] if isinstance(v, str) and (v in vals) else v) for k, v in a.items()
    }
    b = {
        k: (vals[v] if isinstance(v, str) and (v in vals) else v) for k, v in b.items()
    }

    keys_a = set(a)
    keys_b = set(b)

    only_in_a = keys_a - keys_b
    only_in_b = keys_b - keys_a

    different_values = {
        key: (a[key], b[key]) for key in keys_a & keys_b if a[key] != b[key]
    }

    return {
        "only_in_a": {k: a[k] for k in only_in_a},
        "only_in_b": {k: b[k] for k in only_in_b},
        "different_values": different_values,
    }


def remove_punctuation(input_string):
    """Replace punctuation in a string with an empty char"""
    input_string = input_string.replace("&", "and")
    regex_pattern = f"[{re.escape(string.punctuation.replace(" - ", " "))}’]"
    return re.sub(regex_pattern, "", input_string)


def get_subtitle(title):
    """Extract a subtitle from a book's title"""
    return title.split(":")[1].strip()


def get_series_info(title):
    """Extract book series info from a title string."""
    patterns = [
        r".+ \(((.+?),? #(\d+))\)",  # Single entry (e.g., #3)
        r".+ \(((.+?),? #(\d+[-\.]\d+))\)",  # Omnibus or novella (e.g., #1-3, #0.1)
        r".+ \(((.+?),? #(\d+\.\d+-\d+))\)",  # Omnibus with novella (e.g., #0.1-4)
    ]

    for pattern in patterns:
        match = re.fullmatch(pattern, title)
        if match:
            series = f"({match.group(1).strip()})"
            series_name = remove_punctuation(match.group(2)).strip()
            series_num = match.group(3).strip()
            return series, series_name, series_num

    # No match found
    return "", "", ""


def get_clean_book_info(book_title):
    """Extract title, subtitle, and series and ensure it's filesystem safe"""
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
    """Ensure shelves map to correct status"""
    if shelf.startswith("to-read-"):
        shelf = "to-read"
    elif shelf.startswith("read-"):
        shelf = "read"
    return shelf


def generate_metadata(entry):
    """Generate book metadata from Goodreads entry"""
    status = get_clean_shelf(shelf)
    title, subtitle, series, series_num = get_clean_book_info(entry.title)

    try:
        read_at = dt.strptime(entry.user_read_at, "%a, %d %b %Y %H:%M:%S %z")
        read_at = read_at.strftime("%Y-%m-%d")
    except ValueError:
        read_at = ""

    metadata_vars = {
        "author": [entry.author_name],
        "book_id": entry.book_id,
        "book_description": convert(entry.book_description),
        "cover": entry.book_large_image_url,
        "date_last_read": read_at,
        "format": [
            fmt.strip().replace("format-", "")
            for fmt in entry.user_shelves.split(",")
            if fmt.strip().startswith("format")
        ],
        "genre": "non-fiction" if "non-fiction" in entry.user_shelves else "fiction",
        "owned": "true" if "owned" in entry.user_shelves else "false",
        "rating": int(entry.user_rating) if int(entry.user_rating) > 0 else "",
        "re_read": "true" if "re-read" in entry.user_shelves else "false",
        "series_name": series,
        "series_number": series_num,
        "status": status,
        "subtitle": subtitle,
        "updated": dt.now().strftime("%Y-%m-%dT%H:%M"),
    }

    return title, metadata_vars


# Set paths
ROOT = Path(__file__).parent.parent
DEST_DIR = Path("~/Google Drive/My Drive/devault/Atlas/Notes/Vaults/Library")
DEST_DIR = DEST_DIR.expanduser()

# Read in the template files with Jinja
with open(ROOT.joinpath("templates", "template-book-new.md")) as f:
    new_template = jinja2.Template(f.read())

with open(ROOT.joinpath("templates", "template-book-update.md")) as f:
    update_template = jinja2.Template(f.read())

# Read in Goodreads shelves to query
with open(ROOT.joinpath("resources", "goodreads-shelves.txt")) as f:
    shelves = [line.strip("\n") for line in f.readlines()]

# Decide where env vars are being pulled from
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
    logger.info(f"Reading shelf: {shelf}")

    feed = feedparser.parse(gr_rss_base_url + shelf)
    for entry in feed.entries:
        title, metadata = generate_metadata(entry)
        filepath = DEST_DIR.joinpath(f"{title}.md")

        if filepath.exists():
            # Update an existing Markdown file
            with open(filepath) as f:
                current = read_frontmatter(f.readlines())

            dict_diffs = dict_diff(current, metadata)
            if dict_diffs["different_values"]:
                logger.info(f"Updating file: {filepath}")
                for k, v in dict_diffs["different_values"].items():
                    current[k] = v[1]

                stream = StringIO()
                yaml.dump(current, stream)

                metadata = {
                    "yaml": stream.getvalue(),
                    "book_description": metadata["book_description"],
                }
                markdown = update_template.render(**metadata)

                with open(filepath, "w") as f:
                    f.write(markdown)
            else:
                # Nothing to update
                continue

        else:
            # Write a Markdown file for the current book
            markdown = new_template.render(**metadata)
            with open(filepath, "w") as f:
                f.write(markdown)
