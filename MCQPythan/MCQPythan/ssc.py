import requests
import pdfplumber
import pyodbc
import re
from datetime import datetime
import os
import random

# ==============================
# Database Connection
# ==============================
try:
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.;"
        "DATABASE=MCQ;"
        "UID=sa;"
        "PWD=123456;"
    )
    cursor = conn.cursor()
    print("Database connection successful")
    
    # Check if Subject column exists, if not add it
    try:
        cursor.execute("SELECT Subject FROM SSC_MCQ_Questions WHERE 1=0")
    except:
        print("Adding Subject column to the table...")
        cursor.execute("ALTER TABLE SSC_MCQ_Questions ADD Subject NVARCHAR(100)")
        conn.commit()
        print("Subject column added successfully")
        
except Exception as e:
    print(f"Database connection failed: {e}")
    exit()

# ==============================
# Enhanced Question Data Generator with Realistic SSC Questions
# ==============================
def generate_question_data(num_questions=10000):  # Changed to 10,000 questions
    questions_data = []
    
    # Define subjects with their weights
    subjects_with_weights = [
        ("Quantitative Aptitude", 20),
        ("General Intelligence & Reasoning", 25),
        ("English Language", 15),
        ("General Awareness", 10),
        ("History", 10),
        ("Geography", 10),
        ("Computer Science", 5),
        ("Current Affairs", 5)
    ]
    
    # Create subject list based on weights
    subject_pool = []
    for subject, weight in subjects_with_weights:
        subject_pool.extend([subject] * weight)
    
    for i in range(1, num_questions + 1):
        subject = random.choice(subject_pool)
        difficulty = random.choice(["Easy", "Medium", "Hard"])
        
        # Ensure all generators return proper data
        if subject == "Quantitative Aptitude":
            question_data = generate_math_question(i, difficulty)
        elif subject == "General Intelligence & Reasoning":
            question_data = generate_reasoning_question(i, difficulty)
        elif subject == "English Language":
            question_data = generate_english_question(i, difficulty)
        elif subject == "History":
            question_data = generate_history_question(i, difficulty)
        elif subject == "Geography":
            question_data = generate_geography_question(i, difficulty)
        elif subject == "Computer Science":
            question_data = generate_computer_question(i, difficulty)
        elif subject == "Current Affairs":
            question_data = generate_current_affairs_question(i, difficulty)
        else:  # General Awareness
            question_data = generate_gk_question(i, difficulty)
        
        # Add subject to question data and ensure it's not None
        if question_data is not None:
            question_data['subject'] = subject
            questions_data.append(question_data)
        else:
            print(f"Warning: Question {i} returned None for subject {subject}")
    
    return questions_data

# ==============================
# COMPLETE QUESTION GENERATORS (No None returns)
# ==============================

def generate_math_question(q_id, difficulty):
    math_questions = {
       "Easy": [
            (f"Q.{q_id} What is {random.randint(100, 1000)} + {random.randint(50, 500)}?", str(random.randint(100, 1000) + random.randint(50, 500))),
            (f"Q.{q_id} Calculate: {random.randint(20, 100)} × {random.randint(5, 20)}", str(random.randint(20, 100) * random.randint(5, 20))),
            (f"Q.{q_id} Calculate: {random.randint(200, 1000)} × {random.randint(5, 20)}", str(random.randint(200, 1000) * random.randint(5, 20))),
            (f"Q.{q_id} Calculate: {random.randint(40, 900)} × {random.randint(5, 20)}", str(random.randint(40, 900) * random.randint(5, 20))),
            (f"Q.{q_id} Calculate: {random.randint(50, 200)} × {random.randint(5, 20)}", str(random.randint(50, 200) * random.randint(5, 20))),
            (f"Q.{q_id} Find 25% of 200", "50")
        ],
        "Medium": [
            (f"Q.{q_id} Solve for x: 2x + 5 = 15", "5"),
            (f"Q.{q_id} What is the area of a circle with radius 7cm? (π=22/7)", "154"),
            (f"Q.{q_id} If a train covers 300 km in 5 hours, what is its speed?", "60 km/h"),
            (f"Q.{q_id} Find simple interest on ₹1000 at 5% per annum for 2 years", "100"),
            (f"Q.{q_id} A man walks 3 km North, then 4 km East. Find the distance from starting point.", "5 km"),
            (f"Q.{q_id} What is the HCF of 36 and 48?", "12"),
            (f"Q.{q_id} What is the LCM of 12, 15, and 20?", "60"),
            (f"Q.{q_id} If 12 pens cost ₹96, what is the cost of 1 pen?", "8"),
            (f"Q.{q_id} Find the perimeter of a square with side 14 cm.", "56"),
            (f"Q.{q_id} Solve: x/3 = 6", "18"),
        ],
        "Hard": [
            (f"Q.{q_id} Find the value of sin60° × cos30°", "0.433"),
            (f"Q.{q_id} If log₁₀2 = 0.3010, what is log₁₀8?", "0.9030"),
            (f"Q.{q_id} Solve: x² - 5x + 6 = 0", "2,3"),
            (f"Q.{q_id} If a² + b² = 25 and ab = 12, find a² + b² - 2ab", "1"),
            (f"Q.{q_id} A cone has a radius 3 cm and height 4 cm. Find volume. (π=3.14)", "37.68"),
            (f"Q.{q_id} A and B together can do a work in 10 days. A alone does it in 15 days. In how many days can B do it alone?", "30"),
            (f"Q.{q_id} Solve: √(x + 9) = 5", "16"),
            (f"Q.{q_id} A boat can travel 30 km downstream in 2 hours and 18 km upstream in 3 hours. Find speed of boat in still water.", "12 km/h"),
            (f"Q.{q_id} If 5x + 3y = 30 and x + y = 6, find x and y.", "x=3, y=3"),
            (f"Q.{q_id} If x + 1/x = 5, find x² + 1/x²", "23"),
        ]
    }
    
    question_text, correct_answer = random.choice(math_questions[difficulty])
    options = generate_math_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_reasoning_question(q_id, difficulty):
    reasoning_categories = ["Analogies", "Number Series", "Coding-Decoding", "Blood Relations", "Direction Sense"]
    category = random.choice(reasoning_categories)
    
    reasoning_questions = {
        "Analogies": [
            ("Pen : Write :: Knife : ?", "Cut"),
            ("Doctor : Hospital :: Teacher : ?", "School"),
            ("Eyes : See :: Ears : ?", "Hear"),
            ("Bird : Nest :: Bee : ?", "Hive"),
            ("Fire : Heat :: Ice : ?", "Cold"),
            ("Book : Reading :: Fork : ?", "Eating"),
            ("Car : Road :: Train : ?", "Track"),
            ("Knife : Sharpness :: Pen : ?", "Ink"),
        ],
        "Number Series": [
            ("2, 6, 12, 20, ?", "30"),
            ("3, 7, 15, 31, ?", "63"),
            ("5, 10, 20, 40, ?", "80"),
            ("1, 4, 9, 16, 25, ?", "36"),
            ("21, 18, 15, 12, ?", "9"),
            ("2, 3, 5, 8, 12, 17, ?", "23"),
            ("8, 6, 9, 23, 87, ?", "445"),
        ],
        "Coding-Decoding": [
            ("If 'APPLE' is coded as 'BQQMF', how is 'ORANGE' coded?", "PSBOHF"),
            ("If 'TABLE' is coded as 'UZCMF', how is 'CHAIR' coded?", "DIBJS"),
            ("If 'DOG' is 4157, 'CAT' is 3120, then what is 'COT'?", "3170"),
            ("If 'BIRD' = 'CJSE', then 'FISH' = ?", "GJTI"),
            ("In a code, TREE is written as USFF. How is LEAF written?", "MFBG"),
        ],
        "Blood Relations": [
            ("A is B's brother. C is A's mother. How is C related to B?", "Mother"),
            ("P is the brother of Q. Q is the sister of R. R is the son of S. How is S related to P?", "Father or Mother"),
            ("M is the daughter of K. K is the wife of D. D is the father of R. How is R related to M?", "Brother"),
            ("A is the son of B. C is B's sister. D is C's mother. How is D related to A?", "Grandmother"),
            ("X is the father of Y. Y is the mother of Z. How is X related to Z?", "Grandfather"),
        ],
        "Direction Sense": [
            ("Rohan walks 10m South, then turns left and walks 25m. In which direction is he from start?", "South-East"),
            ("A person walks 5m North, turns right and walks 3m. Which direction is he facing now?", "East"),
            ("P walks 10m East, turns left and walks 10m, again turns left and walks 10m. Final direction?", "West"),
            ("She moves 12m North, then 5m East. What is her shortest distance from start?", "13m"),
            ("He walks 6m South, then 8m West. Direction from start?", "South-West"),
        ]
    }
    
    question_text, correct_answer = random.choice(reasoning_questions[category])
    question_text = f"Q.{q_id} {question_text}"
    options = generate_reasoning_options(correct_answer, category)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_english_question(q_id, difficulty):
    english_questions = {
        "Easy": [
            (f"Q.{q_id} Choose the correct synonym of 'Benevolent'", "Kind"),
            (f"Q.{q_id} What is the past tense of 'go'?", "Went"),
            (f"Q.{q_id} Identify the correct spelling:", "Beautiful"),
            (f"Q.{q_id} Fill in the blank: She ____ to school every day.", "Goes"),
            (f"Q.{q_id} Choose the antonym of 'Happy'", "Sad"),
            (f"Q.{q_id} What is the plural of 'Child'?", "Children"),
            (f"Q.{q_id} Choose the correct article: He bought ___ umbrella.", "An"),
            (f"Q.{q_id} Which word is a noun: run, blue, beauty, quickly?", "Beauty"),
        ],
        "Medium": [
            (f"Q.{q_id} Identify the error: 'Neither of the students have completed their homework'", "Have"),
            (f"Q.{q_id} What is the antonym of 'Ephemeral'?", "Permanent"),
            (f"Q.{q_id} Fill in the blank: Hardly ____ she entered when the phone rang.", "Had"),
            (f"Q.{q_id} Choose the correct passive voice: 'She writes a letter.'", "A letter is written by her."),
            (f"Q.{q_id} Spot the error: 'He did not knew the answer.'", "Knew"),
            (f"Q.{q_id} Choose the correct indirect speech: She said, 'I am tired.'", "She said that she was tired."),
            (f"Q.{q_id} Select the correct preposition: He is afraid ___ the dark.", "Of"),
            (f"Q.{q_id} Which word is closest in meaning to 'Scrutinize'?", "Examine"),
        ],
        "Hard": [
            (f"Q.{q_id} 'Procrustean' means:", "Enforcing conformity"),
            (f"Q.{q_id} Identify the figure of speech: 'The stars danced playfully'", "Personification"),
            (f"Q.{q_id} Choose the correct sentence:", "Had I known, I would have helped you."),
            (f"Q.{q_id} What is the meaning of 'Hobson's Choice'?", "No real choice at all"),
            (f"Q.{q_id} Choose the grammatically correct sentence:", "Each of the boys was given a prize."),
            (f"Q.{q_id} Identify the mood: 'If I were you, I would resign.'", "Subjunctive"),
            (f"Q.{q_id} Fill in: The more he earns, the ___ he spends.", "More"),
            (f"Q.{q_id} Meaning of idiom: 'To turn a deaf ear'", "To ignore someone"),
        ]
    }
    
    question_text, correct_answer = random.choice(english_questions[difficulty])
    options = generate_english_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_history_question(q_id, difficulty):
    history_questions = {
        "Easy": [
            (f"Q.{q_id} Who is known as the Father of the Indian Constitution?", "Dr. B.R. Ambedkar"),
            (f"Q.{q_id} When did India get independence?", "1947"),
            (f"Q.{q_id} Who was the first Prime Minister of India?", "Jawaharlal Nehru"),
            (f"Q.{q_id} Who was the first President of India?", "Dr. Rajendra Prasad"),
            (f"Q.{q_id} Which freedom fighter is known as 'Netaji'?", "Subhas Chandra Bose"),
            (f"Q.{q_id} Which movement was led by Mahatma Gandhi in 1942?", "Quit India Movement"),
            (f"Q.{q_id} Who gave the slogan 'Give me blood and I will give you freedom'?", "Subhas Chandra Bose"),
            (f"Q.{q_id} In which year did the Jallianwala Bagh massacre happen?", "1919"),
        ],
        "Medium": [
            (f"Q.{q_id} The Battle of Plassey was fought in which year?", "1757"),
            (f"Q.{q_id} Who founded the Indian National Congress?", "A.O. Hume"),
            (f"Q.{q_id} Who was the Viceroy during the partition of Bengal in 1905?", "Lord Curzon"),
            (f"Q.{q_id} In which session was 'Purna Swaraj' declared by INC?", "Lahore Session, 1929"),
            (f"Q.{q_id} Who led the Revolt of 1857 in Kanpur?", "Nana Sahib"),
            (f"Q.{q_id} Which reform act is also known as Montagu-Chelmsford Reforms?", "Government of India Act, 1919"),
            (f"Q.{q_id} Who was the first Governor-General of independent India?", "Lord Mountbatten"),
            (f"Q.{q_id} Who introduced Permanent Settlement in Bengal?", "Lord Cornwallis"),
        ],
        "Hard": [
            (f"Q.{q_id} The 'Doctrine of Lapse' was introduced by?", "Lord Dalhousie"),
            (f"Q.{q_id} Who wrote 'Kitab-ul-Hind'?", "Al-Biruni"),
            (f"Q.{q_id} In which year was the Simon Commission appointed?", "1927"),
            (f"Q.{q_id} Who was the founder of the Maurya Empire?", "Chandragupta Maurya"),
            (f"Q.{q_id} Which Mughal emperor built the Red Fort?", "Shah Jahan"),
            (f"Q.{q_id} Who was the last ruler of the Mughal Empire?", "Bahadur Shah II"),
            (f"Q.{q_id} The capital of King Ashoka's empire was?", "Pataliputra"),
            (f"Q.{q_id} The Treaty of Seringapatam was signed in?", "1792"),
        ]
    }
    
    question_text, correct_answer = random.choice(history_questions[difficulty])
    options = generate_history_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_geography_question(q_id, difficulty):
    geography_questions = {
        "Easy": [
            (f"Q.{q_id} Which is the longest river in India?", "Ganga"),
            (f"Q.{q_id} What is the capital of Maharashtra?", "Mumbai"),
            (f"Q.{q_id} Which is the southernmost point of India?", "Indira Point"),
            (f"Q.{q_id} How many Union Territories are there in India (as of 2025)?", "8"),
            (f"Q.{q_id} In which state is the Thar Desert located?", "Rajasthan"),
            (f"Q.{q_id} What is the capital of Kerala?", "Thiruvananthapuram"),
            (f"Q.{q_id} Mount Everest lies in which mountain range?", "Himalayas"),
            (f"Q.{q_id} Which Indian river is known as 'Dakshin Ganga'?", "Godavari"),
        ],
        "Medium": [
            (f"Q.{q_id} Which state has the longest coastline in India?", "Gujarat"),
            (f"Q.{q_id} Which is the largest freshwater lake in India?", "Wular Lake"),
            (f"Q.{q_id} Which city is known as the 'Silicon Valley of India'?", "Bengaluru"),
            (f"Q.{q_id} Which Indian state shares its border with maximum states?", "Uttar Pradesh"),
            (f"Q.{q_id} Tropic of Cancer passes through how many Indian states?", "8"),
            (f"Q.{q_id} Which plateau is known as the 'Mineral Belt of India'?", "Chotanagpur Plateau"),
            (f"Q.{q_id} Which Indian river flows westward and falls into the Arabian Sea?", "Narmada"),
            (f"Q.{q_id} Name the strait that separates India and Sri Lanka.", "Palk Strait"),
        ],
        "Hard": [
            (f"Q.{q_id} The 'Horn of Africa' includes which countries?", "Somalia, Ethiopia, Eritrea, Djibouti"),
            (f"Q.{q_id} Which river forms the famous Jog Falls?", "Sharavati"),
            (f"Q.{q_id} Which is the highest active volcano in the world?", "Ojos del Salado"),
            (f"Q.{q_id} Name the cold desert in India.", "Ladakh"),
            (f"Q.{q_id} What is the correct order (south to north) of the Himalayan ranges?", "Siwalik, Lesser Himalayas, Greater Himalayas"),
            (f"Q.{q_id} In which continent is the Great Rift Valley located?", "Africa"),
            (f"Q.{q_id} Which Indian state has the highest forest cover by area?", "Madhya Pradesh"),
            (f"Q.{q_id} Which current is responsible for warming the western coasts of Europe?", "Gulf Stream"),
        ]
    }
    
    question_text, correct_answer = random.choice(geography_questions[difficulty])
    options = generate_geography_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_computer_question(q_id, difficulty):
    computer_questions = {
        "Easy": [
            (f"Q.{q_id} What does CPU stand for?", "Central Processing Unit"),
            (f"Q.{q_id} Which of these is a programming language?", "Python"),
            (f"Q.{q_id} What is the full form of RAM?", "Random Access Memory"),
            (f"Q.{q_id} Which device is used to input data into a computer?", "Keyboard"),
            (f"Q.{q_id} What does WWW stand for?", "World Wide Web"),
        ],
        "Medium": [
            (f"Q.{q_id} In programming, what does OOP stand for?", "Object Oriented Programming"),
            (f"Q.{q_id} Which protocol is used for sending emails?", "SMTP"),
            (f"Q.{q_id} What is the binary equivalent of decimal 10?", "1010"),
            (f"Q.{q_id} Which language is used for web development?", "HTML"),
            (f"Q.{q_id} What does SQL stand for?", "Structured Query Language"),
        ],
        "Hard": [
            (f"Q.{q_id} In SQL, which command is used to remove a table?", "DROP TABLE"),
            (f"Q.{q_id} What does API stand for?", "Application Programming Interface"),
            (f"Q.{q_id} Which sorting algorithm has worst-case time complexity O(n²)?", "Bubble Sort"),
            (f"Q.{q_id} What is the purpose of DNS?", "Domain Name System"),
            (f"Q.{q_id} Which data structure uses LIFO principle?", "Stack"),
        ]
    }
    
    question_text, correct_answer = random.choice(computer_questions[difficulty])
    options = generate_computer_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_current_affairs_question(q_id, difficulty):
    current_affairs = {
        "Easy": [
            (f"Q.{q_id} Who is the current Prime Minister of India?", "Narendra Modi"),
            (f"Q.{q_id} Which country hosted the 2023 G20 Summit?", "India"),
            (f"Q.{q_id} Who is the current President of India?", "Droupadi Murmu"),
            (f"Q.{q_id} Which city will host the 2032 Summer Olympics?", "Brisbane"),
            (f"Q.{q_id} What is the currency of Japan?", "Yen"),
            (f"Q.{q_id} Which country recently launched the Artemis I mission?", "USA"),
        ],
        "Medium": [
            (f"Q.{q_id} The Chandrayaan-3 mission was launched in which year?", "2023"),
            (f"Q.{q_id} Who won the Nobel Peace Prize 2023?", "Narges Mohammadi"),
            (f"Q.{q_id} Which country recently became the 195th member of the UN?", "South Sudan"),
            (f"Q.{q_id} Which Indian state recently became the first to provide free Wi-Fi to all villages?", "Kerala"),
            (f"Q.{q_id} Name the Indian who won the Booker Prize in 2023.", "Geetanjali Shree"),
            (f"Q.{q_id} Who is the Chairperson of the Finance Commission of India (2023)?", "N.K. Singh"),
        ],
        "Hard": [
            (f"Q.{q_id} The 'Viksit Bharat' vision aims for India to become developed by which year?", "2047"),
            (f"Q.{q_id} Which country recently changed its name to Türkiye?", "Turkey"),
            (f"Q.{q_id} The International Solar Alliance was launched in which year?", "2015"),
            (f"Q.{q_id} Who is the current Secretary-General of the United Nations?", "António Guterres"),
            (f"Q.{q_id} Which country hosts the headquarters of the International Criminal Court (ICC)?", "Netherlands"),
            (f"Q.{q_id} When was the National Education Policy (NEP) 2020 implemented in India?", "2020"),
        ]
    }
    
    question_text, correct_answer = random.choice(current_affairs[difficulty])
    options = generate_current_affairs_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

def generate_gk_question(q_id, difficulty):
    gk_questions = {
        "Easy": [
            (f"Q.{q_id} How many states are there in India?", "28"),
            (f"Q.{q_id} Who is known as the Missile Man of India?", "Dr. A.P.J. Abdul Kalam"),
            (f"Q.{q_id} What is the national animal of India?", "Tiger"),
            (f"Q.{q_id} Who wrote the Indian National Anthem?", "Rabindranath Tagore"),
            (f"Q.{q_id} Which planet is known as the Red Planet?", "Mars"),
            (f"Q.{q_id} What is the currency of India?", "Indian Rupee"),
        ],
        "Medium": [
            (f"Q.{q_id} The Rajya Sabha can have maximum how many members?", "250"),
            (f"Q.{q_id} Who was the first woman President of India?", "Pratibha Patil"),
            (f"Q.{q_id} Which is the largest organ in the human body?", "Skin"),
            (f"Q.{q_id} Which country is the largest producer of tea?", "China"),
            (f"Q.{q_id} Which element has the chemical symbol 'Fe'?", "Iron"),
            (f"Q.{q_id} What does GDP stand for?", "Gross Domestic Product"),
        ],
        "Hard": [
            (f"Q.{q_id} The 'Kalinga War' was fought in which year?", "261 BCE"),
            (f"Q.{q_id} Who was the first Indian to win Nobel Prize?", "Rabindranath Tagore"),
            (f"Q.{q_id} Which treaty ended the First Anglo-Mysore War?", "Treaty of Madras"),
            (f"Q.{q_id} What is the half-life of Uranium-238?", "4.468 billion years"),
            (f"Q.{q_id} Name the author of the book 'Discovery of India'.", "Jawaharlal Nehru"),
            (f"Q.{q_id} What is the capital of Bhutan?", "Thimphu"),
        ]
    }
    
    question_text, correct_answer = random.choice(gk_questions[difficulty])
    options = generate_gk_options(correct_answer, difficulty)
    
    return {
        'question_text': question_text,
        'optionA': options['A'], 'optionB': options['B'], 'optionC': options['C'], 'optionD': options['D'],
        'answer': correct_answer, 'category': "SSC", 'course': "SSC Exam", 'created_date': datetime.now()
    }

# ==============================
# OPTION GENERATORS
# ==============================

def generate_math_options(correct_answer, difficulty):
    try:
        # Handle comma-separated answers
        if ',' in correct_answer:
            correct_num = float(correct_answer.split(',')[0])
        else:
            correct_num = float(correct_answer) if '.' in correct_answer else int(correct_answer)
    except:
        correct_num = random.randint(1, 100)
    
    variations = [1, 2, 5, 10] if difficulty == "Easy" else [3, 7, 15, 25]
    
    options = [
        str(correct_num),
        str(correct_num + random.choice(variations)),
        str(correct_num - random.choice(variations)),
        str(correct_num * random.choice([2, 3]))
    ]
    random.shuffle(options)
    
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_reasoning_options(correct_answer, category):
    wrong_options_map = {
        "Analogies": ["Eat", "Sharp", "Cook", "Write", "Jump", "Run", "Throw", "Read"],
        "Number Series": ["28", "32", "35", "40", "45", "50", "55", "60"],
        "Coding-Decoding": ["PSBOHE", "PSBOHG", "PSBOFG", "PSBOHE", "OSBPEF", "QSBPOG"],
        "Blood Relations": ["Father", "Sister", "Grandmother", "Aunt", "Uncle", "Cousin"],
        "Direction Sense": ["North", "South", "West", "North-West", "South-East", "East"],
    }
    
    wrong_options = wrong_options_map.get(category, ["Option1", "Option2", "Option3", "Option4"])
    options = [correct_answer] + random.sample(wrong_options, 3)
    random.shuffle(options)
    
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_english_options(correct_answer, difficulty):
    synonyms = {
        "Kind": ["Benevolent", "Compassionate", "Generous", "Gentle"],
        "Went": ["Gone", "Goed", "Going", "Goes"],
        "Permanent": ["Lasting", "Enduring", "Constant", "Perpetual"],
        "Sad": ["Unhappy", "Depressed", "Miserable", "Sorrowful"],
        "Beautiful": ["Pretty", "Lovely", "Gorgeous", "Stunning"]
    }
    
    if correct_answer in synonyms:
        options = [correct_answer] + synonyms[correct_answer][:3]
    else:
        options = [correct_answer, "Option1", "Option2", "Option3"]
    
    random.shuffle(options)
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_history_options(correct_answer, difficulty):
    historical_options = {
        "Dr. B.R. Ambedkar": ["Mahatma Gandhi", "Jawaharlal Nehru", "Sardar Patel", "B.R. Ambedkar"],
        "1947": ["1942", "1950", "1947", "1935"],
        "1757": ["1756", "1761", "1757", "1748"],
        "Jawaharlal Nehru": ["Mahatma Gandhi", "Sardar Patel", "Jawaharlal Nehru", "Subhas Chandra Bose"],
        "1919": ["1918", "1920", "1919", "1921"]
    }
    
    if correct_answer in historical_options:
        options = historical_options[correct_answer]
    else:
        options = [correct_answer, "Option1", "Option2", "Option3"]
    
    random.shuffle(options)
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_geography_options(correct_answer, difficulty):
    geography_options = {
        "Ganga": ["Yamuna", "Brahmaputra", "Ganga", "Godavari"],
        "Mumbai": ["Pune", "Mumbai", "Nagpur", "Thane"],
        "Gujarat": ["Maharashtra", "Tamil Nadu", "Gujarat", "Kerala"],
        "8": ["7", "9", "8", "10"],
        "Himalayas": ["Western Ghats", "Eastern Ghats", "Himalayas", "Aravalli"]
    }
    
    if correct_answer in geography_options:
        options = geography_options[correct_answer]
    else:
        options = [correct_answer, "Option1", "Option2", "Option3"]
    
    random.shuffle(options)
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_computer_options(correct_answer, difficulty):
    computer_options = {
        "Central Processing Unit": ["Computer Processing Unit", "Central Programming Unit", "Central Processing Unit", "Control Processing Unit"],
        "Python": ["Cobra", "Anaconda", "Python", "Viper"],
        "Object Oriented Programming": ["Object Organized Programming", "Object Oriented Programming", "Objective Oriented Programming", "Object Origin Programming"],
        "SMTP": ["HTTP", "FTP", "SMTP", "TCP"],
        "1010": ["1001", "1100", "1010", "1111"]
    }
    
    if correct_answer in computer_options:
        options = computer_options[correct_answer]
    else:
        options = [correct_answer, "Option1", "Option2", "Option3"]
    
    random.shuffle(options)
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_current_affairs_options(correct_answer, difficulty):
    current_options = {
        "Narendra Modi": ["Rahul Gandhi", "Narendra Modi", "Amit Shah", "Manmohan Singh"],
        "India": ["USA", "China", "India", "Japan"],
        "2023": ["2022", "2024", "2023", "2025"],
        "Droupadi Murmu": ["Pratibha Patil", "Ram Nath Kovind", "Droupadi Murmu", "APJ Abdul Kalam"],
        "Yen": ["Dollar", "Euro", "Yen", "Yuan"]
    }
    
    if correct_answer in current_options:
        options = current_options[correct_answer]
    else:
        options = [correct_answer, "Option1", "Option2", "Option3"]
    
    random.shuffle(options)
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

def generate_gk_options(correct_answer, difficulty):
    gk_options = {
        "28": ["25", "29", "28", "30"],
        "Dr. A.P.J. Abdul Kalam": ["Vikram Sarabhai", "Dr. A.P.J. Abdul Kalam", "Homi Bhabha", "C.V. Raman"],
        "Tiger": ["Lion", "Elephant", "Tiger", "Leopard"],
        "Rabindranath Tagore": ["Bankim Chandra Chatterjee", "Rabindranath Tagore", "Sarojini Naidu", "Mahatma Gandhi"],
        "Mars": ["Venus", "Jupiter", "Mars", "Saturn"]
    }
    
    if correct_answer in gk_options:
        options = gk_options[correct_answer]
    else:
        options = [correct_answer, "Option1", "Option2", "Option3"]
    
    random.shuffle(options)
    return {'A': options[0], 'B': options[1], 'C': options[2], 'D': options[3]}

# ==============================
# Bulk Insert Function (Updated with Subject)
# ==============================
def bulk_insert_questions(questions_data):
    insert_query = """
    INSERT INTO SSC_MCQ_Questions 
    (Question, OptionA, OptionB, OptionC, OptionD, Answer, Categoery, Course, CREATEDDATE, Subject)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    batch_size = 500  # Increased batch size for better performance
    total_questions = len(questions_data)
    inserted_count = 0
    
    # Count questions by subject
    subject_count = {}
    
    for i in range(0, total_questions, batch_size):
        batch = questions_data[i:i + batch_size]
        
        try:
            for question in batch:
                cursor.execute(insert_query, 
                    question['question_text'],
                    question['optionA'],
                    question['optionB'], 
                    question['optionC'],
                    question['optionD'],
                    question['answer'],
                    question['category'],
                    question['course'],
                    question['created_date'],
                    question['subject']
                )
                
                # Count by subject
                subject = question['subject']
                subject_count[subject] = subject_count.get(subject, 0) + 1
            
            conn.commit()
            inserted_count += len(batch)
            print(f"Inserted batch {i//batch_size + 1}: {len(batch)} questions (Total: {inserted_count})")
            
        except Exception as e:
            print(f"Error inserting batch: {e}")
            conn.rollback()
    
    # Print subject-wise distribution
    print("\n📊 Subject-wise Question Distribution:")
    for subject, count in subject_count.items():
        percentage = (count / total_questions) * 100
        print(f"  {subject}: {count} questions ({percentage:.1f}%)")
    
    return inserted_count

# ==============================
# Main Execution
# ==============================
def main():
    print("Starting Enhanced SSC Questions Data Population...")
    print("Generating 10,000 questions...")
    
    # Generate and insert enhanced questions
    questions_data = generate_question_data(10000)
    
    print(f"Generated {len(questions_data)} questions successfully")
    
    print("Inserting questions into database...")
    total_inserted = bulk_insert_questions(questions_data)
    
    print(f"\n✅ SUCCESS: Inserted {total_inserted} questions into the database!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()