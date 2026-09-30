"""
database/seed_aptitude_questions.py
--------------------------------------
Phase 5: seeds the aptitude_questions table with 75 questions across the
5 required categories (15 each), so a real test can randomly draw 30 of
them without always serving the same fixed set.

Run with the backend's DATABASE_URL:
    cd backend && python ../database/seed_aptitude_questions.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine, text
from app.config import settings

QUESTIONS = []

# ---------------------------------------------------------------------------
# Logical Reasoning (15)
# ---------------------------------------------------------------------------
QUESTIONS += [
    ("logical_reasoning", "If all Zips are Zaps, and all Zaps are Zops, then all Zips are:", "Zops", "Zaps only", "Not Zops", "Cannot be determined", "A"),
    ("logical_reasoning", "Find the odd one out: Apple, Banana, Carrot, Mango", "Apple", "Banana", "Carrot", "Mango", "C"),
    ("logical_reasoning", "If MONDAY is coded as NPOEBZ, how is TUESDAY coded?", "UVFTEBZ", "UVFTZEB", "UVFTEZB", "UVTFEBZ", "A"),
    ("logical_reasoning", "A is B's sister. C is B's mother. D is C's father. How is A related to D?", "Grandson", "Granddaughter", "Daughter", "Son", "B"),
    ("logical_reasoning", "Complete the series: 2, 6, 12, 20, 30, ?", "40", "42", "44", "36", "B"),
    ("logical_reasoning", "Pointing to a man, a woman said, 'His mother is the only daughter of my mother.' How is the woman related to the man?", "Mother", "Aunt", "Sister", "Grandmother", "A"),
    ("logical_reasoning", "Which number should replace the question mark: 3, 9, 27, 81, ?", "162", "243", "324", "729", "B"),
    ("logical_reasoning", "If 'CAT' is coded as 3120, how is 'DOG' coded using the same logic (A=1,B=2...)?", "4157", "4715", "4571", "4175", "A"),
    ("logical_reasoning", "Statement: All engineers are graduates. Some graduates are teachers. Conclusion: Some engineers are teachers. Is the conclusion valid?", "Valid", "Invalid", "Cannot be determined", "Partially valid", "C"),
    ("logical_reasoning", "Find the missing term: AZ, BY, CX, DW, ?", "EV", "EU", "FV", "EW", "A"),
    ("logical_reasoning", "In a certain code, 'GO' is written as '715'. How is 'SO' written?", "1915", "1815", "2015", "1715", "A"),
    ("logical_reasoning", "Five friends sit in a row. P is to the left of Q but right of R. S is to the right of Q. T is between Q and S. What is the order?", "R P Q T S", "P R Q T S", "R P T Q S", "P Q R T S", "A"),
    ("logical_reasoning", "If 'PENCIL' is coded as 'QFODJM', how is 'ERASER' coded?", "FSBTFS", "FSBTFT", "FSATFS", "ESBTFS", "A"),
    ("logical_reasoning", "Which figure completes the analogy: Book is to Library as Painting is to?", "Museum", "Frame", "Artist", "Canvas", "A"),
    ("logical_reasoning", "A cube is painted red on all faces and cut into 27 equal smaller cubes. How many small cubes have exactly 2 faces painted?", "8", "12", "6", "4", "B"),
]

# ---------------------------------------------------------------------------
# Quantitative Aptitude (15)
# ---------------------------------------------------------------------------
QUESTIONS += [
    ("quantitative", "What is 15% of 240?", "32", "36", "40", "24", "B"),
    ("quantitative", "If a train travels 300 km in 5 hours, what is its speed?", "50 km/h", "60 km/h", "55 km/h", "45 km/h", "B"),
    ("quantitative", "The average of 5 numbers is 20. If one number is removed, the average becomes 18. What is the removed number?", "24", "26", "28", "30", "C"),
    ("quantitative", "A shopkeeper marks an item 20% above cost price and gives a 10% discount. What is his profit percentage?", "8%", "10%", "12%", "6%", "A"),
    ("quantitative", "Simplify: (12 + 8) / 4 * 2", "10", "8", "12", "5", "A"),
    ("quantitative", "What is the compound interest on Rs. 1000 at 10% per annum for 2 years?", "Rs. 210", "Rs. 200", "Rs. 220", "Rs. 190", "A"),
    ("quantitative", "If x + y = 10 and x - y = 4, what is x?", "5", "6", "7", "8", "C"),
    ("quantitative", "A can complete a task in 10 days, B in 15 days. How long will they take working together?", "5 days", "6 days", "7 days", "8 days", "B"),
    ("quantitative", "What is the value of 7^2 - 3^2?", "40", "42", "44", "38", "A"),
    ("quantitative", "Convert 0.75 into a fraction.", "3/4", "7/5", "5/7", "4/3", "A"),
    ("quantitative", "The ratio of two numbers is 3:5 and their sum is 40. Find the larger number.", "24", "25", "26", "20", "A"),
    ("quantitative", "A car covers a distance in 6 hours at 50 km/h. How long will it take at 60 km/h?", "5 hours", "4.5 hours", "5.5 hours", "6 hours", "A"),
    ("quantitative", "What is the LCM of 12 and 18?", "36", "24", "48", "72", "A"),
    ("quantitative", "If the price of an item increases by 25%, by what percentage should it be reduced to bring it back to the original price?", "20%", "25%", "15%", "30%", "A"),
    ("quantitative", "A sum of money doubles itself in 8 years at simple interest. What is the rate of interest?", "12.5%", "10%", "15%", "8%", "A"),
]

# ---------------------------------------------------------------------------
# Verbal Ability (15)
# ---------------------------------------------------------------------------
QUESTIONS += [
    ("verbal", "Choose the correct synonym for 'Benevolent':", "Kind", "Cruel", "Selfish", "Arrogant", "A"),
    ("verbal", "Choose the correct antonym for 'Abundant':", "Scarce", "Plentiful", "Huge", "Rich", "A"),
    ("verbal", "Fill in the blank: She has been working here ___ 2019.", "since", "for", "from", "in", "A"),
    ("verbal", "Identify the correctly spelled word:", "Occassion", "Occasion", "Ocasion", "Occession", "B"),
    ("verbal", "Choose the correct sentence:", "He don't like coffee.", "He doesn't likes coffee.", "He doesn't like coffee.", "He not like coffee.", "C"),
    ("verbal", "What is the meaning of the idiom 'Break the ice'?", "Start a conversation", "End a relationship", "Cause trouble", "Freeze something", "A"),
    ("verbal", "Choose the correct passive voice: 'She writes a letter.'", "A letter was written by her.", "A letter is written by her.", "A letter is being written by her.", "A letter has written by her.", "B"),
    ("verbal", "Identify the part of speech of the underlined word: 'She sings beautifully.'", "Adverb", "Adjective", "Noun", "Verb", "A"),
    ("verbal", "Choose the correct synonym for 'Meticulous':", "Careless", "Careful", "Quick", "Lazy", "B"),
    ("verbal", "Choose the correct antonym for 'Optimistic':", "Pessimistic", "Hopeful", "Cheerful", "Confident", "A"),
    ("verbal", "Fill in the blank: Neither the manager nor the employees ___ available.", "is", "are", "was", "be", "B"),
    ("verbal", "Choose the correctly punctuated sentence:", "Its a beautiful day, isnt it?", "It's a beautiful day, isn't it?", "Its a beautiful day, isn't it?", "It's a beautiful day, isnt it?", "B"),
    ("verbal", "What does 'procrastinate' mean?", "To delay doing something", "To finish quickly", "To organize", "To celebrate", "A"),
    ("verbal", "Choose the one-word substitute for 'a person who loves books':", "Bibliophile", "Philanthropist", "Linguist", "Author", "A"),
    ("verbal", "Identify the correct comparative form: 'This road is ___ than that one.'", "wider", "more wide", "widest", "wide", "A"),
]

# ---------------------------------------------------------------------------
# Basic Technical Reasoning (15)
# ---------------------------------------------------------------------------
QUESTIONS += [
    ("technical_reasoning", "What is the time complexity of binary search on a sorted array?", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "A"),
    ("technical_reasoning", "Which data structure uses FIFO (First In First Out) order?", "Queue", "Stack", "Tree", "Graph", "A"),
    ("technical_reasoning", "What does SQL stand for?", "Structured Query Language", "Simple Query Language", "Sequential Query Language", "Structured Question Language", "A"),
    ("technical_reasoning", "Which HTTP method is typically used to update an existing resource?", "PUT", "GET", "DELETE", "TRACE", "A"),
    ("technical_reasoning", "In object-oriented programming, what does 'encapsulation' refer to?", "Bundling data and methods that operate on it", "Creating multiple classes", "Inheriting from a parent class", "Overloading functions", "A"),
    ("technical_reasoning", "What is the primary key in a relational database used for?", "Uniquely identifying a row", "Sorting a table", "Joining two tables only", "Storing large text", "A"),
    ("technical_reasoning", "Which of these is NOT a programming paradigm?", "Object-Oriented", "Functional", "Sequential Query", "Procedural", "C"),
    ("technical_reasoning", "What does 'API' stand for?", "Application Programming Interface", "Applied Program Instruction", "Automated Program Interface", "Application Process Integration", "A"),
    ("technical_reasoning", "Which sorting algorithm has the best average-case time complexity: O(n log n)?", "Merge Sort", "Bubble Sort", "Selection Sort", "Insertion Sort", "A"),
    ("technical_reasoning", "What is the purpose of a 'foreign key' in a database?", "To link two tables together", "To encrypt data", "To create an index", "To store passwords", "A"),
    ("technical_reasoning", "In Git, what command is used to combine changes from one branch into another?", "merge", "commit", "clone", "fetch", "A"),
    ("technical_reasoning", "What does 'REST' stand for in RESTful APIs?", "Representational State Transfer", "Remote State Transfer", "Representational Server Technology", "Remote Server Transfer", "A"),
    ("technical_reasoning", "Which of these is a NoSQL database?", "MongoDB", "PostgreSQL", "MySQL", "SQLite", "A"),
    ("technical_reasoning", "What is the main advantage of using a hash table?", "Fast average-case lookup, O(1)", "Guaranteed sorted order", "Low memory usage", "Simplicity of implementation only", "A"),
    ("technical_reasoning", "What does 'CI/CD' stand for in software development?", "Continuous Integration / Continuous Deployment", "Code Inspection / Code Delivery", "Central Integration / Central Deployment", "Continuous Inspection / Continuous Development", "A"),
]

# ---------------------------------------------------------------------------
# Problem Solving (15)
# ---------------------------------------------------------------------------
QUESTIONS += [
    ("problem_solving", "You have 8 identical-looking balls, one heavier than the rest. Using a balance scale, what is the minimum number of weighings needed to find it?", "2", "3", "4", "1", "A"),
    ("problem_solving", "A farmer has to cross a river with a fox, a chicken, and a bag of grain, but can only take one at a time. What must he take first to avoid the fox eating the chicken or the chicken eating the grain?", "The chicken", "The fox", "The grain", "Any of them", "A"),
    ("problem_solving", "If you have only a 3-liter and a 5-liter jug, how can you measure exactly 4 liters?", "Fill 5L, pour into 3L, empty 3L, pour remaining 2L into 3L, fill 5L again, top off 3L", "Fill 3L twice", "Fill 5L once", "It's not possible", "A"),
    ("problem_solving", "A clock shows 3:15. What is the angle between the hour and minute hands?", "7.5 degrees", "0 degrees", "15 degrees", "30 degrees", "A"),
    ("problem_solving", "You are given two ropes that each take exactly 1 hour to burn, but burn unevenly. How do you measure 45 minutes?", "Light both ends of one rope and one end of the other simultaneously", "Light one end of each rope", "Cut each rope in half", "It cannot be measured", "A"),
    ("problem_solving", "A bat and a ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost?", "$0.05", "$0.10", "$0.15", "$0.01", "A"),
    ("problem_solving", "If 5 machines take 5 minutes to make 5 widgets, how long would 100 machines take to make 100 widgets?", "5 minutes", "100 minutes", "20 minutes", "50 minutes", "A"),
    ("problem_solving", "In a lake, a patch of lily pads doubles in size every day. It takes 48 days to cover the whole lake. How many days to cover half the lake?", "47", "24", "46", "45", "A"),
    ("problem_solving", "You have two eggs and access to a 100-floor building. You want to find the highest floor from which an egg won't break when dropped, minimizing worst-case drops. What's a good first-drop strategy?", "Start at floor 14, then decrease the interval each time", "Start at floor 50", "Start at floor 1", "Drop from floor 100 first", "A"),
    ("problem_solving", "Three switches outside a room control three bulbs inside. You can flip switches but only enter the room once. How do you determine which switch controls which bulb?", "Turn on switch 1, wait, turn it off, turn on switch 2, then enter and check heat and light", "Turn all switches on at once", "It's not possible", "Turn switches on one at a time and check light only", "A"),
    ("problem_solving", "A snail climbs 3 feet up a wall each day but slips back 2 feet each night. How many days to climb a 10-foot wall?", "8 days", "10 days", "7 days", "9 days", "A"),
    ("problem_solving", "You need to sort a list of 1 million numbers with limited memory. Which approach fits best?", "External merge sort", "Bubble sort", "Load everything into memory and use quicksort", "Selection sort", "A"),
    ("problem_solving", "A man is looking at a photo and says, 'I have no siblings, but that man's father is my father's son.' Who is in the photo?", "His son", "Himself", "His father", "His nephew", "A"),
    ("problem_solving", "How would you find if a linked list has a cycle in it, using O(1) extra space?", "Floyd's cycle detection (slow/fast pointers)", "Store all nodes in a hash set", "Traverse and count nodes", "It cannot be done in O(1) space", "A"),
    ("problem_solving", "You're designing a system to handle 10x traffic growth. What's the FIRST thing you should investigate?", "Where the current bottleneck is (via profiling/metrics)", "Immediately add more servers", "Rewrite the whole system", "Switch programming languages", "A"),
]

if __name__ == "__main__":
    print(f"Total questions prepared: {len(QUESTIONS)}")
    for cat in ["logical_reasoning", "quantitative", "verbal", "technical_reasoning", "problem_solving"]:
        count = sum(1 for q in QUESTIONS if q[0] == cat)
        print(f"  {cat}: {count}")

    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        existing = conn.execute(text("SELECT COUNT(*) FROM aptitude_questions")).scalar()
        if existing and existing > 0:
            print(f"aptitude_questions already has {existing} rows — skipping seed (delete rows first to reseed).")
        else:
            for category, text_q, a, b, c, d, correct in QUESTIONS:
                conn.execute(
                    text("""
                        INSERT INTO aptitude_questions
                            (category, question_text, option_a, option_b, option_c, option_d, correct_option)
                        VALUES (:category, :question_text, :a, :b, :c, :d, :correct)
                    """),
                    {"category": category, "question_text": text_q, "a": a, "b": b, "c": c, "d": d, "correct": correct},
                )
            print(f"Inserted {len(QUESTIONS)} aptitude questions.")
