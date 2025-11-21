# scc_web_scraper.py - Complete All-in-One Solution with SQL Server
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, select
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime
import time
import logging
import sys
import re
import random
import urllib.parse

# ==================== DATABASE SETUP (SQLAlchemy 2.0 + SQL Server) ====================
Base = declarative_base()

class QuestionAnswer(Base):
    __tablename__ = 'questions_answers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source_url = Column(String(500))
    category = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuestionAnswer(question='{self.question[:50]}...')>"

# ==================== WEB SCRAPER CLASS ====================
class SCCWebScraper:
    def __init__(self, database_url=None):
        self.setup_logging()
        self.setup_database(database_url)
        self.setup_session()
        self.logger.info("SCC Web Scraper initialized successfully")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scc_scraping.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self, database_url):
        """Setup SQL Server database connection"""
        try:
            # Use provided database URL or create default for SQL Server
            if database_url is None:
                # SQL Server connection string for your database
                database_url = "mssql+pyodbc://sa:123456@./MCQ?driver=ODBC+Driver+17+for+SQL+Server"
            
            self.engine = create_engine(database_url)
            
            # Test connection
            with self.engine.connect() as conn:
                self.logger.info("✅ Successfully connected to SQL Server database")
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            self.logger.info("✅ Database tables verified/created")
            
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            self.logger.info("💡 Troubleshooting tips:")
            self.logger.info("1. Make sure SQL Server is running")
            self.logger.info("2. Check if ODBC Driver 17 for SQL Server is installed")
            self.logger.info("3. Verify username/password and database name")
            raise
    
    def setup_session(self):
        """Setup requests session with headers"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_website(self, url, selectors=None):
        """
        Main method to scrape questions and answers from a URL
        
        Args:
            url: Website URL to scrape
            selectors: Custom CSS selectors for the website
        """
        self.logger.info(f"🔍 Scraping: {url}")
        
        try:
            # Fetch the webpage
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try different scraping strategies
            strategies = [
                self.strategy_container_based,
                self.strategy_heading_based,
                self.strategy_definition_list,
                self.strategy_table_based
            ]
            
            all_qa_data = []
            for strategy in strategies:
                qa_data = strategy(soup, selectors or {}, url)
                if qa_data:
                    all_qa_data.extend(qa_data)
                    self.logger.info(f"Strategy {strategy.__name__} found {len(qa_data)} Q&A pairs")
            
            # Remove duplicates
            unique_qa_data = self.remove_duplicates(all_qa_data)
            self.logger.info(f"✅ Total unique Q&A pairs found: {len(unique_qa_data)}")
            
            return unique_qa_data
            
        except requests.RequestException as e:
            self.logger.error(f"❌ Network error scraping {url}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Unexpected error scraping {url}: {e}")
            return []
    
    def strategy_container_based(self, soup, selectors, url):
        """Strategy 1: Look for containers that hold Q&A pairs"""
        qa_data = []
        
        # Common container patterns for Q&A
        container_selectors = [
            '.faq-item', '.qa-item', '.question-answer', '.faq',
            '.accordion-item', '.card', '.panel', 
            '[class*="faq"]', '[class*="question"]', '[class*="qa"]',
            'div.faq > div', 'li.faq', '.faq li'
        ]
        
        for selector in container_selectors:
            containers = soup.select(selector)
            if containers:
                self.logger.info(f"Found {len(containers)} containers with selector: {selector}")
                
                for container in containers:
                    qa_pair = self.extract_from_container(container)
                    if qa_pair:
                        qa_pair.update({
                            'source_url': url,
                            'category': self.detect_category(url, qa_pair['question'])
                        })
                        qa_data.append(qa_pair)
                break  # Use first successful selector
        
        return qa_data
    
    def strategy_heading_based(self, soup, selectors, url):
        """Strategy 2: Look for question headings with subsequent answers"""
        qa_data = []
        
        # Look for potential question elements
        question_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
        
        for q_elem in question_elements:
            question_text = self.clean_text(q_elem.get_text())
            
            if self.is_question(question_text):
                answer_elem = self.find_answer_after_question(q_elem)
                if answer_elem:
                    answer_text = self.clean_text(answer_elem.get_text())
                    
                    if self.is_valid_qa_pair(question_text, answer_text):
                        qa_data.append({
                            'question': question_text,
                            'answer': answer_text,
                            'source_url': url,
                            'category': self.detect_category(url, question_text)
                        })
        
        return qa_data
    
    def strategy_definition_list(self, soup, selectors, url):
        """Strategy 3: Look for definition lists (dt/dd elements)"""
        qa_data = []
        
        # Check for definition lists (common for Q&A)
        dl_elements = soup.find_all('dl')
        
        for dl in dl_elements:
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            
            for i in range(min(len(dts), len(dds))):
                question_text = self.clean_text(dts[i].get_text())
                answer_text = self.clean_text(dds[i].get_text())
                
                if self.is_valid_qa_pair(question_text, answer_text):
                    qa_data.append({
                        'question': question_text,
                        'answer': answer_text,
                        'source_url': url,
                        'category': self.detect_category(url, question_text)
                    })
        
        return qa_data
    
    def strategy_table_based(self, soup, selectors, url):
        """Strategy 4: Look for Q&A in tables"""
        qa_data = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    question_text = self.clean_text(cells[0].get_text())
                    answer_text = self.clean_text(cells[1].get_text())
                    
                    if self.is_valid_qa_pair(question_text, answer_text):
                        qa_data.append({
                            'question': question_text,
                            'answer': answer_text,
                            'source_url': url,
                            'category': self.detect_category(url, question_text)
                        })
        
        return qa_data
    
    def extract_from_container(self, container):
        """Extract Q&A from a container element"""
        try:
            # Try to find question (usually bold, strong, or heading)
            question_elem = (
                container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or
                container.find(['strong', 'b']) or
                container.find(class_=re.compile('question|title|heading', re.I))
            )
            
            if not question_elem:
                return None
            
            question_text = self.clean_text(question_elem.get_text())
            
            # Find answer (remove question element and get remaining text)
            question_elem.extract() if question_elem else None
            answer_text = self.clean_text(container.get_text())
            
            if self.is_valid_qa_pair(question_text, answer_text):
                return {
                    'question': question_text,
                    'answer': answer_text
                }
                
        except Exception as e:
            self.logger.debug(f"Error extracting from container: {e}")
        
        return None
    
    def find_answer_after_question(self, question_elem):
        """Find the answer element after a question element"""
        current = question_elem.next_sibling
        
        while current:
            if hasattr(current, 'name') and current.name in ['p', 'div', 'span', 'li', 'dd']:
                text_content = self.clean_text(current.get_text())
                if len(text_content) > 10:  # Minimum answer length
                    return current
            elif hasattr(current, 'strip') and current.strip():
                text_content = self.clean_text(str(current))
                if len(text_content) > 10:
                    return current
            
            # Also check children of next elements
            if hasattr(current, 'find_all'):
                children = current.find_all(['p', 'div', 'span'])
                for child in children:
                    text_content = self.clean_text(child.get_text())
                    if len(text_content) > 10:
                        return child
            
            current = current.next_sibling
        
        return None
    
    def is_question(self, text):
        """Check if text looks like a question"""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower().strip()
        
        # Question indicators
        question_words = ['what', 'why', 'how', 'when', 'where', 'which', 'who', 'whom', 'whose']
        question_phrases = ['can you', 'could you', 'would you', 'should i', 'is it', 'are you']
        
        has_question_word = any(word in text_lower for word in question_words)
        has_question_phrase = any(phrase in text_lower for phrase in question_phrases)
        ends_with_question_mark = text_lower.endswith('?')
        starts_with_question = any(text_lower.startswith(word) for word in question_words)
        
        return ends_with_question_mark or has_question_word or has_question_phrase or starts_with_question
    
    def is_valid_qa_pair(self, question, answer):
        """Validate if this is a proper Q&A pair"""
        return (
            question and answer and
            len(question) >= 10 and
            len(answer) >= 20 and
            question != answer and
            not question.startswith('http') and
            not answer.startswith('http')
        )
    
    def detect_category(self, url, question):
        """Detect category from URL or question content"""
        url_lower = url.lower()
        question_lower = question.lower()
        
        categories = {
            'Contract Law': ['contract', 'agreement', 'lease', 'offer', 'acceptance', 'consideration'],
            'Constitutional Law': ['constitution', 'fundamental', 'rights', 'article', 'amendment'],
            'Criminal Law': ['criminal', 'penal', 'offense', 'crime', 'arrest', 'bail'],
            'Civil Law': ['civil', 'tort', 'negligence', 'damages', 'compensation'],
            'Property Law': ['property', 'land', 'real estate', 'ownership', 'possession'],
            'Labor Law': ['labor', 'employment', 'worker', 'wages', 'termination'],
            'Family Law': ['marriage', 'divorce', 'custody', 'adoption', 'maintenance'],
            'Tax Law': ['tax', 'income tax', 'gst', 'assessment', 'deduction']
        }
        
        for category, keywords in categories.items():
            if any(keyword in url_lower for keyword in keywords) or any(keyword in question_lower for keyword in keywords):
                return category
        
        return 'General Law'
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace, newlines, tabs
        text = re.sub(r'\s+', ' ', text)
        
        # Remove specific unwanted characters but keep basic punctuation
        text = re.sub(r'[\r\n\t]+', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def remove_duplicates(self, qa_list):
        """Remove duplicate Q&A pairs"""
        seen = set()
        unique_list = []
        
        for qa in qa_list:
            # Create a signature based on first 50 chars of question
            signature = qa['question'][:50].lower()
            if signature not in seen:
                seen.add(signature)
                unique_list.append(qa)
        
        return unique_list
    
    def save_to_database(self, questions_data):
        """Save scraped data to SQL Server database"""
        if not questions_data:
            self.logger.warning("No data to save to database")
            return 0
        
        saved_count = 0
        session = Session(self.engine)
        
        try:
            for data in questions_data:
                # Check if similar question already exists
                stmt = select(QuestionAnswer).where(
                    QuestionAnswer.question.ilike(f"%{data['question'][:30]}%")
                )
                existing = session.scalar(stmt)
                
                if not existing:
                    qa = QuestionAnswer(
                        question=data['question'],
                        answer=data['answer'],
                        source_url=data['source_url'],
                        category=data.get('category', 'General Law')
                    )
                    session.add(qa)
                    saved_count += 1
            
            session.commit()
            self.logger.info(f"💾 Saved {saved_count} new records to SQL Server database")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"❌ Error saving to database: {e}")
            saved_count = 0
        finally:
            session.close()
        
        return saved_count
    
    def get_existing_urls(self):
        """Get list of already scraped URLs"""
        session = Session(self.engine)
        try:
            stmt = select(QuestionAnswer.source_url).distinct()
            result = session.execute(stmt)
            urls = [row[0] for row in result if row[0]]
            return set(urls)
        except Exception as e:
            self.logger.error(f"Error getting existing URLs: {e}")
            return set()
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()
        self.logger.info("Database connection closed")

# ==================== MAIN FUNCTIONS ====================
def run_scraper():
    """Main function to run the SCC scraper"""
    
    # REPLACE THESE WITH ACTUAL SCC WEBSITE URLs
    scc_urls = [
        'https://www.jagranjosh.com/articles/ssc-cgl-exam-most-repetitive-questions-from-general-knowledge-1491297614-1',  # Supreme Court of India FAQ
        'https://greendotinternationalschool.com/blog/top-50-gk-questions-with-answers-for-students/',  
       
    ]
    
    # Initialize scraper with SQL Server connection
    scraper = SCCWebScraper()
    
    try:
        total_saved = 0
        existing_urls = scraper.get_existing_urls()
        
        for url in scc_urls:
            if url in existing_urls:
                scraper.logger.info(f"⏭️ URL already scraped: {url}")
                continue
            
            # Scrape the website
            qa_data = scraper.scrape_website(url)
            
            # Save to database
            if qa_data:
                saved_count = scraper.save_to_database(qa_data)
                total_saved += saved_count
            else:
                scraper.logger.warning(f"⚠️ No Q&A data found at: {url}")
            
            # Respectful delay between requests
            time.sleep(random.uniform(2, 5))
        
        scraper.logger.info(f"🎉 Scraping completed! Total new records saved: {total_saved}")
        
        # Display database statistics
        display_database_stats(scraper)
        
    except Exception as e:
        scraper.logger.error(f"💥 Scraping failed: {e}")
    
    finally:
        scraper.close()

def display_database_stats(scraper):
    """Display database statistics"""
    session = Session(scraper.engine)
    try:
        # Total records
        total_records = session.query(QuestionAnswer).count()
        print(f"\n{'='*50}")
        print(f"📊 SQL SERVER DATABASE STATISTICS")
        print(f"{'='*50}")
        print(f"Database: MCQ")
        print(f"Table: questions_answers")
        print(f"Total Q&A records: {total_records}")
        
        # Records by category
        category_stats = session.query(
            QuestionAnswer.category,
            func.count(QuestionAnswer.id)
        ).group_by(QuestionAnswer.category).all()
        
        print(f"\n📁 Records by Category:")
        for category, count in category_stats:
            print(f"  {category}: {count}")
        
        # Records by source
        source_stats = session.query(
            QuestionAnswer.source_url,
            func.count(QuestionAnswer.id)
        ).group_by(QuestionAnswer.source_url).all()
        
        print(f"\n🌐 Records by Source:")
        for source, count in source_stats[:5]:  # Show top 5
            domain = source.split('//')[-1].split('/')[0] if source else 'Unknown'
            print(f"  {domain}: {count}")
        
        # Show sample records
        sample_records = session.query(QuestionAnswer).limit(3).all()
        print(f"\n📝 Sample Records:")
        for i, record in enumerate(sample_records, 1):
            print(f"\n  {i}. Question: {record.question[:80]}...")
            print(f"     Answer: {record.answer[:80]}...")
            print(f"     Category: {record.category}")
            
    except Exception as e:
        print(f"Error displaying statistics: {e}")
    finally:
        session.close()

def search_database():
    """Search the database for specific questions"""
    scraper = SCCWebScraper()
    
    try:
        while True:
            print(f"\n{'='*50}")
            print(f"🔍 SEARCH DATABASE")
            print(f"{'='*50}")
            search_term = input("Enter search term (or 'quit' to exit): ").strip()
            
            if search_term.lower() == 'quit':
                break
            
            if not search_term:
                continue
            
            session = Session(scraper.engine)
            try:
                # Search in questions and answers
                results = session.query(QuestionAnswer).filter(
                    QuestionAnswer.question.ilike(f'%{search_term}%') |
                    QuestionAnswer.answer.ilike(f'%{search_term}%')
                ).all()
                
                print(f"\n📖 Found {len(results)} results for '{search_term}':")
                
                for i, result in enumerate(results, 1):
                    print(f"\n--- Result {i} ---")
                    print(f"Question: {result.question}")
                    print(f"Answer: {result.answer[:200]}...")
                    print(f"Category: {result.category}")
                    print(f"Source: {result.source_url}")
                    print(f"Added: {result.created_at.date()}")
                    
            finally:
                session.close()
                
    finally:
        scraper.close()

def test_database_connection():
    """Test SQL Server database connection"""
    print("🔧 Testing SQL Server connection...")
    try:
        scraper = SCCWebScraper()
        print("✅ Database connection successful!")
        
        # Test basic operations
        session = Session(scraper.engine)
        count = session.query(QuestionAnswer).count()
        print(f"✅ Table access successful! Current records: {count}")
        session.close()
        scraper.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting steps:")
        print("1. Make sure SQL Server is running")
        print("2. Install ODBC Driver 17 for SQL Server")
        print("3. Check if database 'MCQ' exists")
        print("4. Verify username 'sa' and password '123456'")
        print("5. Check if SQL Server allows mixed authentication")
        return False

# ==================== COMMAND LINE INTERFACE ====================
if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"🏛️  SCC QUESTION-ANSWER WEB SCRAPER (SQL SERVER)")
    print(f"{'='*60}")
    print(f"📊 Database: MCQ | Server: . | User: sa")
    print(f"{'='*60}")
    
    # First test database connection
    if not test_database_connection():
        print("❌ Cannot continue without database connection.")
        sys.exit(1)
    
    while True:
        print(f"\nOptions:")
        print(f"1. Run Scraper")
        print(f"2. Search Database")
        print(f"3. View Statistics")
        print(f"4. Test Connection")
        print(f"5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print(f"\n🚀 Starting web scraper...")
            run_scraper()
        elif choice == '2':
            search_database()
        elif choice == '3':
            scraper = SCCWebScraper()
            display_database_stats(scraper)
            scraper.close()
        elif choice == '4':
            test_database_connection()
        elif choice == '5':
            print(f"👋 Thank you for using SCC Web Scraper!")
            break
        else:
            print(f"❌ Invalid choice. Please try again.")