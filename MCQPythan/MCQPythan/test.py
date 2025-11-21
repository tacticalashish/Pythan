import time
import traceback
import pyodbc
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==============================
# Configuration
# ==============================
HEADLESS = False  # Set True to run without opening the browser window
WAIT_TIMEOUT = 20  # seconds for explicit waits
RETRY_DELAY = 3  # seconds to wait before retrying page load or next page

# ==============================
# Database Connection
# ==============================
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=MCQ;"
    "UID=sa;"
    "PWD=123456;"
)
cursor = conn.cursor()

def insert_question(category, subject, course, question, optionA, optionB, optionC, optionD, answer):
    try:
        cursor.execute("""
            INSERT INTO SSC_MCQ_Questions
            (Categoery, Subject, Course, Question, OptionA, OptionB, OptionC, OptionD, Answer, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (category, subject, course, question, optionA, optionB, optionC, optionD, answer))
        conn.commit()
    except Exception as e:
        print(f"❌ DB Insert error: {e}\n{traceback.format_exc()}")

def get_category_subject_from_url(url: str):
    path = urlparse(url).path.strip("/").lower()
    parts = path.split('/')
    if len(parts) >= 2:
        subject = parts[0].replace("-", " ").title()
        category = parts[1].replace("-", " ").title()
    else:
        subject = "General"
        category = path.replace("-", " ").title()
    return category, subject

def create_driver():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_section(start_url):
    category_name, subject_name = get_category_subject_from_url(start_url)
    course_name = "SSC"  # Fixed course

   # print(f"\n📌 Starting category: {category_name} | Subject: {subject_name} | Course: {course_name}")

    driver = create_driver()
    try:
        driver.get(start_url)
        page_num = 1

        while True:
            print(f"\n📄 Scraping {category_name} | Page {page_num}")

            try:
                WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.question.single-question"))
                )
            except Exception as e:
                print(f"⚠️ Timeout waiting for questions on page {page_num}: {e}")
                break

            questions = driver.find_elements(By.CSS_SELECTOR, "article.question.single-question")
            if not questions:
                print("⚠️ No questions found, ending scrape for this category.")
                break

            for idx, q in enumerate(questions, start=1):
                try:
                    question_text = q.find_element(By.CSS_SELECTOR, "div.question-main").text.strip()

                    # FIXED OPTION EXTRACTION
                    option_ps = q.find_elements(By.CSS_SELECTOR, "div.form-inputs.clearfix.question-options > p")
                    optionA = option_ps[0].find_elements(By.TAG_NAME, "label")[1].text.strip()
                    optionB = option_ps[1].find_elements(By.TAG_NAME, "label")[1].text.strip()
                    optionC = option_ps[2].find_elements(By.TAG_NAME, "label")[1].text.strip()
                    optionD = option_ps[3].find_elements(By.TAG_NAME, "label")[1].text.strip()

                    answer_value = q.find_element(By.CSS_SELECTOR, "input[type='hidden']").get_attribute("value")
                    answer_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
                    answer_letter = answer_map.get(answer_value, "Unknown")

                    insert_question(category_name, subject_name, course_name, question_text, optionA, optionB, optionC, optionD, answer_letter)
                    print(f"✅ [{category_name}] Q{idx} Inserted: {question_text[:60]}...")
                except Exception as e:
                    print(f"❌ Error processing question {idx} on page {page_num}: {e}")
                    #print(traceback.format_exc())

            try:
                next_link = driver.find_element(By.CSS_SELECTOR, "a.nextpostslink")
                next_url = next_link.get_attribute("href")
                if not next_url:
                    print("🚀 No more pages found, finishing category.")
                    break

                driver.get(next_url)
                page_num += 1
                time.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"🚀 Finished scraping category '{category_name}' or next page not found: {e}")
                break

    except Exception as e:
        print(f"❌ Unexpected error scraping {category_name}: {e}")
        #print(traceback.format_exc())
    finally:
        driver.quit()

urls = [
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?page=10",                               
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-compound-interest/?section=2&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-ages/?page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-calendar/?page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-clock/?page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=2&page=10",
       
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-area/?section=3&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-volume-and-surface-area/?section=2&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-numbers/?section=2&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-problems-on-h.c.f-and-l.c.m/?section=2&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-decimal-fraction/?section=2&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=2&page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-simplification/?section=3&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-square-root-and-cube-root/?section=2&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=2&page=10",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-surds-and-indices/?section=3&page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-chain-rule/?page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-pipes-and-cistern/?page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-boats-and-streams/?page=10",

       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=2",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=3",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=4",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=5",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=6",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=7",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=8",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=9",
       "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-logarithm/?page=10",
       
]

if __name__ == "__main__":
    for url in urls:
        scrape_section(url)

    cursor.close()
    conn.close()
