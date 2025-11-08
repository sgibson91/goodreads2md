import os

# import re
from pathlib import Path

import jinja2

# Get the path to the root of the project
ROOT = Path(__file__).parent.parent

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

# book_title = "Data Feminism"
# metadata_vars = {
#     "authors": ["Catherine D'Ignazio", "Lauren F. Klein"],
#     "book_id": "51777543",
#     "book_description": """A new way of thinking about data science and data ethics that is informed by the ideas of intersectional feminism.

# Today, data science is a form of power. It has been used to expose injustice, improve health outcomes, and topple governments. But it has also been used to discriminate, police, and surveil. This potential for good, on the one hand, and harm, on the other, makes it essential to ask: Data science by whom? Data science for whom? Data science with whose interests in mind? The narratives around big data and data science are overwhelmingly white, male, and techno-heroic. In Data Feminism, Catherine D'Ignazio and Lauren Klein present a new way of thinking about data science and data ethics—one that is informed by intersectional feminist thought.

# Illustrating data feminism in action, D'Ignazio and Klein show how challenges to the male/female binary can help challenge other hierarchical (and empirically wrong) classification systems. They explain how, for example, an understanding of emotion can expand our ideas about effective data visualization, and how the concept of invisible labor can expose the significant human efforts required by our automated systems. And they show why the data never, ever “speak for themselves.”

# Data Feminism offers strategies for data scientists seeking to learn how feminism can help them work toward justice, and for feminists who want to focus their efforts on the growing field of data science. But Data Feminism is about much more than gender. It is about power, about who has it and who doesn't, and about how those differentials of power can be challenged and changed.
#     """,
#     "cover_url": "https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/books/1572991302i/51777543.jpg",
#     "date_last_read": "2025-11-07",
#     "date_last_started": "2025-10-07",
#     "formats": ["hardback"],
#     "genre": "non-fiction",
#     "owned": "true",
#     "rating": "4",
#     "series": "",
#     "shelf": "read",
# }

# markdown = template.render(**metadata_vars)
# with open(f"{book_title}.md", "w") as f:
#     f.write(markdown)
