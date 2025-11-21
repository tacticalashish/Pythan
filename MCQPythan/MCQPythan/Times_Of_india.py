import requests
from bs4 import BeautifulSoup
import pyodbc
import time
from datetime import datetime
import re

# ==========================================
# CONFIGURATION
# ==========================================

BASE_URL = "https://economictimes.indiatimes.com"
MAIN_URL = "https://economictimes.indiatimes.com/tech/it/articlelist/78570530.cms?from=mdr"

# SQL SERVER CONNECTION (UPDATE THIS)
CONN = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=NASolution;"
    "UID=sa;"
    "PWD=123456;"
)
CURSOR = CONN.cursor()


# ==========================================
# FETCH FULL ARTICLE
# ==========================================

def clean_text(text: str) -> str:
    """Remove junk lines like 'Catch all the Technology News...' etc."""
    if not text:
        return ""

    # Remove boilerplate lines
    text = re.sub(r"\(Catch all.*?Economic Times\.\).*?(\.\.\.|more)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(ETtech|AI Investments|Precedents Increasingly Regular)\b", "", text, flags=re.IGNORECASE)

    # Remove extra whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def get_full_article(url):
    """Scrape the full article page and return complete description, author, and meta info."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # --- Full content from article body ---
        content_div = soup.find("div", class_=re.compile(r'contentDivWrapper'))
        full_text = ""
        if content_div:
            # Extract all text including <p>, <strong>, and <br>
            paragraphs = []
            for elem in content_div.descendants:
                if elem.name in ["p", "strong"]:
                    paragraphs.append(elem.get_text(" ", strip=True))
                elif isinstance(elem, str):
                    text = elem.strip()
                    if text:
                        paragraphs.append(text)
            full_text = "\n".join(paragraphs)
            full_text = clean_text(full_text)

        # --- Author ---
        author_tag = soup.select_one("span.authDetail a, div.author")
        author = author_tag.get_text(strip=True) if author_tag else None

        # --- Meta Info ---
        meta_title = soup.title.string.strip() if soup.title else ""
        meta_desc_tag = soup.find("meta", {"name": "description"})
        meta_key_tag = soup.find("meta", {"name": "keywords"})
        meta_desc = meta_desc_tag["content"].strip() if meta_desc_tag else ""
        meta_keys = meta_key_tag["content"].strip() if meta_key_tag else ""

        return {
            "FullDescription": full_text,
            "Author": author,
            "MetaTitle": meta_title,
            "MetaDescription": meta_desc,
            "MetaKeywords": meta_keys
        }

    except Exception as e:
        print(f"⚠️ Error scraping full article: {e}")
        return None


# ==========================================
# SCRAPE MAIN PAGE
# ==========================================

def scrape_and_insert_news():
    """Scrape main list and insert full data into SQL Server."""
    res = requests.get(MAIN_URL, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        print("❌ Failed to open main page")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select("div.story-box.clearfix")
    print(f"🔍 Found {len(articles)} articles")

    for idx, article in enumerate(articles, start=1):
        try:
            a_tag = article.select_one("h4 a")
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            slug = a_tag["href"]
            url = slug if slug.startswith("http") else BASE_URL + slug

            desc_tag = article.select_one("p")
            short_desc = desc_tag.get_text(strip=True) if desc_tag else ""

            img_tag = article.select_one("div.image img")
            image_url = img_tag.get("data-src") or img_tag.get("src") if img_tag else None

            time_tag = article.select_one("time")
            published_date = time_tag.get("datetime") if time_tag else None

            # Fetch full description
            full_article = get_full_article(url)
            if not full_article:
                continue

            # Skip if full text is empty
            if not full_article["FullDescription"].strip():
                print(f"⚠️ Skipping empty article: {title}")
                continue

            # Insert into database
            CURSOR.execute("""
                INSERT INTO Tbl_News
                (Title, Slug, ShortDescription, FullDescription, Author, Category,
                 ImageUrl, MetaTitle, MetaDescription, MetaKeywords,
                 PublishedDate, UpdatedDate, IsPublished, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                slug,
                short_desc,
                full_article["FullDescription"],
                full_article["Author"],
                "IT",
                image_url,
                full_article["MetaTitle"],
                full_article["MetaDescription"],
                full_article["MetaKeywords"],
                published_date,
                datetime.now(),
                1,
                1
            ))
            CONN.commit()

            print(f"✅ Inserted [{idx}] {title}")

            time.sleep(1)  # delay to avoid being blocked

        except Exception as e:
            print(f"⚠️ Error inserting article #{idx}: {e}")

    print("🎉 All news inserted successfully.")


# ==========================================
# RUN SCRIPT
# ==========================================
if __name__ == "__main__":
    scrape_and_insert_news()
    CONN.close()
