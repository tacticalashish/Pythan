import requests
from bs4 import BeautifulSoup
import pyodbc
from datetime import datetime

# === SQL Server Connection ===
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=NASolution;"
    "UID=sa;"
    "PWD=123456;"
)
cursor = conn.cursor()

# === Base URL of news site ===
base_url = "https://timesofindia.indiatimes.com"

# === Request HTML page ===
url = "https://timesofindia.indiatimes.com/tech"  # example listing page
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# === Loop through news articles ===
articles = soup.select("div.story-box.clearfix")

for article in articles:
    title_tag = article.select_one("h4 a")
    if not title_tag:
        continue

    title = title_tag.text.strip()
    slug = title_tag['href']
    full_url = base_url + slug

    img_tag = article.select_one("div.image img")
    image_url = img_tag['src'] if img_tag else None

    desc_tag = article.select_one("p")
    short_desc = desc_tag.text.strip() if desc_tag else None

    time_tag = article.select_one("time")
    published_date = None
    if time_tag and time_tag.has_attr("datetime"):
        published_date = datetime.strptime(time_tag["datetime"], "%b %d, %Y, %I:%M %p IST")

    # === Fetch full article content ===
    full_response = requests.get(full_url)
    full_soup = BeautifulSoup(full_response.text, 'html.parser')
    full_content_tag = full_soup.find("div", {"class": "Normal"})
    full_description = ""
    if full_content_tag:
        full_description = full_content_tag.get_text(separator="\n").strip()

    # === Insert into SQL ===
    cursor.execute("""
        INSERT INTO Tbl_News
        (Title, Slug, ShortDescription, FullDescription, ImageUrl, Category, PublishedDate, IsPublished, IsActive)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        slug,
        short_desc,
        full_description,
        image_url,
        'IT',  # or another category
        published_date,
        1,
        1
    ))

    conn.commit()
    print(f"Inserted: {title}")

conn.close()
print("✅ All news inserted successfully.")
