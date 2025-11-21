import requests
from bs4 import BeautifulSoup
import pyodbc
from datetime import datetime

# 1️⃣ SQL Server connection (update your server/database)
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=NASolution;"
    "UID=sa;"
    "PWD=123456;"
)
cursor = conn.cursor()

# 2️⃣ URL to scrape
url = "https://www.businesstoday.in/tech-today/enterprise-tech"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# 3️⃣ Utility: generate SEO slug
def generate_slug(title):
    slug = title.lower().strip().replace(" ", "-")
    for ch in ['.', ',', ':', ';', "'", '"', '&', '?', '!', '(', ')', '/', '|']:
        slug = slug.replace(ch, '')
    return slug.strip("-")

# 4️⃣ Find all article blocks
articles = soup.find_all("div", class_="Section_widget_listing_body__f9Mee")
print(f"Found {len(articles)} articles")

for article in articles:
    # Title + Link
    a_tag = article.find("a", title=True)
    if not a_tag:
        continue
    title = a_tag["title"].strip()
    link = a_tag["href"]
    if not link.startswith("http"):
        link = "https://www.businesstoday.in" + link
    slug = generate_slug(title)

    # Image
    img_tag = article.find("img")
    image_url = img_tag["src"] if img_tag else None

    # Description (first <p>)
    desc_tag = article.find("p")
    short_description = desc_tag.text.strip() if desc_tag else None

    # Published Date (in <span>)
    span_tag = article.find("span")
    published_date = datetime.now()
    if span_tag and span_tag.text.strip():
        date_text = span_tag.text.replace("Updated :", "").strip()
        try:
            published_date = datetime.strptime(date_text, "%b %d, %Y")
        except:
            pass

    # Skip duplicates
    cursor.execute("SELECT COUNT(*) FROM Tbl_News WHERE Slug = ?", (slug,))
    if cursor.fetchone()[0] > 0:
        print(f"Skipping duplicate: {slug}")
        continue

    # Insert into Tbl_News
    cursor.execute("""
        INSERT INTO Tbl_News
        (Title, Slug, ShortDescription, Content, Author, Category, Tags, ImageUrl,
         MetaTitle, MetaDescription, MetaKeywords, PublishedDate, UpdatedDate, IsPublished, IsActive)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        slug,
        short_description,
        short_description,
        "Business Today",                    # Author
        "Enterprise Tech",                   # Category
        "ai, tech, enterprise, business",    # Tags
        image_url,
        title,                               # MetaTitle
        short_description,                   # MetaDescription
        "enterprise, ai, technology, 2025",  # MetaKeywords
        published_date,
        datetime.now(),
        1,                                   # IsPublished
        1                                    # IsActive
    ))

    print(f"Inserted: {title}")

# 5️⃣ Commit and close
conn.commit()
cursor.close()
conn.close()
print("✅ Data inserted successfully!")
