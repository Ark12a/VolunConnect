import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# Users table create karna
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
);
"""

cursor.execute(create_table_query)
conn.commit()
cursor.close()
conn.close()

print("BINGO! 'users' table successfully created in PostgreSQL.")