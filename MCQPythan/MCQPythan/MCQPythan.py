import time
import pyodbc
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

def insert_question(category, question, optionA, optionB, optionC, optionD, answer):
    cursor.execute("""
        INSERT INTO SSC_MCQ_Questions (Categoery, Question, OptionA, OptionB, OptionC, OptionD, Answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (category, question, optionA, optionB, optionC, optionD, answer))
    conn.commit()

def get_category_from_url(url: str) -> str:
    """Extract a readable category name from the URL."""
    path = urlparse(url).path.strip("/")
    if path.startswith("quizbase/"):
        category = path.replace("quizbase/", "").replace("-", " ").title()
    else:
        category = path.replace("-", " ").title()
    return category

# ==============================
# Scraper for a single quiz section
# ==============================
def scrape_section(start_url):
    category_name = get_category_from_url(start_url)
    print(f"\n📌 Starting category: {category_name}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(start_url)

    page_num = 1
    while True:
        print(f"\n📄 Scraping {category_name} | Page {page_num}")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.wp_quiz_question.testclass"))
            )
        except:
            print(f"⚠️ No questions found on {category_name}.")
            break

        questions = driver.find_elements(By.CSS_SELECTOR, "div.wp_quiz_question.testclass")
        if not questions:
            break

        for q in questions:
            # ---- QUESTION TEXT ----
            try:
                question_number = q.find_element(By.CSS_SELECTOR, "span.quesno").text.strip()
            except:
                question_number = ""
            question_text = q.text.replace(question_number, "").strip()

            # ---- OPTIONS ----
            options_container = q.find_element(
                By.XPATH, "following-sibling::div[contains(@class,'wp_quiz_question_options')]"
            )
            options_text = options_container.get_attribute("innerText").strip().split("\n")
            optionA = options_text[0] if len(options_text) > 0 else None
            optionB = options_text[1] if len(options_text) > 1 else None
            optionC = options_text[2] if len(options_text) > 2 else None
            optionD = options_text[3] if len(options_text) > 3 else None

            # ---- ANSWER ----
            try:
                answer_div = q.find_element(
                    By.XPATH, "following-sibling::div[contains(@class,'ques_answer')]"
                )
                answer = answer_div.get_attribute("innerText").strip()
            except:
                answer = None

            insert_question(category_name, question_text, optionA, optionB, optionC, optionD, answer)
            print(f"✅ [{category_name}] Inserted: {question_text[:60]}...")

        # ---- NEXT PAGE ----
        try:
            next_link = driver.find_element(By.CSS_SELECTOR, "a.nextpostslink")
            next_url = next_link.get_attribute("href")
            driver.get(next_url)
            page_num += 1
            time.sleep(2)
        except:
            print(f"🚀 Finished category: {category_name}")
            break

    driver.quit()

# ==============================
# URLs to Scrape
# ==============================
urls = [
    # "https://www.gktoday.in/quizbase/modern-indian-history-freedom-struggle",
    # "https://www.gktoday.in/quizbase/modern-indian-history-freedom-struggle?pageno=5",
    # "https://www.gktoday.in/quizbase/modern-indian-history-freedom-struggle?pageno=4",
    # "https://www.gktoday.in/quizbase/modern-indian-history-freedom-struggle?pageno=3",
    # "https://www.gktoday.in/quizbase/modern-indian-history-freedom-struggle?pageno=2",
    # "https://www.gktoday.in/quizbase/modern-indian-history-freedom-struggle?pageno=1",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=2",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=3",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=4",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=5",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=6",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=7",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=8",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=9",
    "https://www.examveda.com/arithmetic-ability/practice-mcq-question-on-average/?page=10"
]

# ==============================
# Run Scraper
# ==============================
if __name__ == "__main__":
    for url in urls:
        scrape_section(url)

    cursor.close()
    conn.close()
