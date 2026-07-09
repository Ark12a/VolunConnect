import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# 1. skills_mapping table create karna
cursor.execute("""
CREATE TABLE IF NOT EXISTS skills_mapping (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100),
    category VARCHAR(100)
);
""")

# 2. support_tickets table create karna
cursor.execute("""
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(100),
    issue VARCHAR(100),
    message TEXT
);
""")

conn.commit()
cursor.close()
conn.close()

print("BINGO! 'skills_mapping' aur 'support_tickets' tables successfully create ho gayi hain.")