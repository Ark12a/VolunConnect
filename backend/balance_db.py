import psycopg2
import psycopg2.extras
import random
import itertools
import os
from dotenv import load_dotenv
import os

load_dotenv() # Ye command .env file ko read karegi aur variables set kar degi
# 1. Database Connection (Yahan apna cloud DB URL daal dena)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/login1")
db = psycopg2.connect(DATABASE_URL)
cursor = db.cursor()

# 2. Table ko naye sire se banana
cursor.execute("DROP TABLE IF EXISTS volunteers CASCADE")
cursor.execute(""" 
CREATE TABLE volunteers (
    VolunteerId SERIAL PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(100),
    skills VARCHAR(50),
    exp VARCHAR(50),
    availability VARCHAR(50),
    work_type VARCHAR(50),
    rating VARCHAR(50),
    locn VARCHAR(50),
    gender VARCHAR(50)
)
""")
db.commit()

# 3. Filter Options
skills = ['IT Support', 'Teaching', 'Healthcare', 'Event Management']
locations = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Kolkata', 'Lucknow', 'Patna', 'Hyderabad', 'Dehradun', 'Bhopal', 'Agra']
exps = ['0-5', '5-10', '>10']
availabilities = ['Weekdays', 'Weekends', 'Flexible']
work_types = ['On-site', 'Remote']

# 4. Indian Names for Authentic Data
male_firsts = ['Aarav', 'Vihaan', 'Aditya', 'Arjun', 'Sai', 'Rohan', 'Amit', 'Rahul', 'Vikram', 'Karan', 'Rajesh', 'Sanjay', 'Deepak', 'Anil', 'Manoj', 'Akash', 'Pratham', 'Navneet', 'Asutosh', 'Digvijay', 'Arkadyuti', 'Ravi', 'Sunil']
female_firsts = ['Diya', 'Isha', 'Priya', 'Neha', 'Pooja', 'Anjali', 'Sneha', 'Kavya', 'Shruti', 'Swati', 'Riya', 'Kiran', 'Megha', 'Nisha', 'Rekha', 'Oishiki', 'Sinjini', 'Atrayee', 'Khusi', 'Prathiba', 'Nitu']
last_names = ['Sharma', 'Singh', 'Kumar', 'Patel', 'Gupta', 'Das', 'Dutta', 'Saha', 'Yadav', 'Bhandary', 'Jaiswal', 'Mor', 'Pawar', 'Nair', 'Koel', 'Reddy', 'Verma', 'Mishra', 'Pandey', 'Nath']

# 5. Har combination banayenge
base_combinations = list(itertools.product(skills, locations, exps, availabilities, work_types))
data_to_insert = []
volunteer_id = 10001 

print("Generating Indian Volunteer Profiles for PostgreSQL... Please wait.")

for combo in base_combinations:
    skill, loc, exp, avail, work = combo
    
    # EXACT 3:2 RATIO: 6 Male
    for _ in range(6):
        fname = random.choice(male_firsts)
        lname = random.choice(last_names)
        fullname = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}{random.randint(10,999)}@gmail.com"
        
        data_to_insert.append((volunteer_id, fullname, email, skill, exp, avail, work, "", loc, "male"))
        volunteer_id += 1
        
    # EXACT 3:2 RATIO: 4 Female
    for _ in range(4):
        fname = random.choice(female_firsts)
        lname = random.choice(last_names)
        fullname = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}{random.randint(10,999)}@gmail.com"
        
        data_to_insert.append((volunteer_id, fullname, email, skill, exp, avail, work, "", loc, "female"))
        volunteer_id += 1

random.shuffle(data_to_insert)

# 6. Bulk Insert using execute_values (Fastest method for PostgreSQL)
sql = """INSERT INTO volunteers 
         (VolunteerId, fullname, email, skills, exp, availability, work_type, rating, locn, gender) 
         VALUES %s"""

print(f"Inserting {len(data_to_insert)} records into PostgreSQL...")
psycopg2.extras.execute_values(cursor, sql, data_to_insert, page_size=1000)
db.commit()

print("BINGO! Records successfully added.")
cursor.close()
db.close()
