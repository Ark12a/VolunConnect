import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# 1. Cities table create karna
cursor.execute("DROP TABLE IF EXISTS cities CASCADE;")
create_table_query = """
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) UNIQUE NOT NULL,
    lat NUMERIC(10, 6),
    lng NUMERIC(10, 6)
);
"""
cursor.execute(create_table_query)

# 2. Indian Cities ka data coordinates ke saath (Jo balance_db.py mein use hui hain)
cities_data = [
    ('Mumbai', 19.0760, 72.8777),
    ('Delhi', 28.6139, 77.2090),
    ('Bengaluru', 12.9716, 77.5946),
    ('Chennai', 13.0827, 80.2707),
    ('Kolkata', 22.5726, 88.3639),
    ('Lucknow', 26.8467, 80.9462),
    ('Patna', 25.5941, 85.1376),
    ('Hyderabad', 17.3850, 78.4867),
    ('Dehradun', 30.3165, 78.0322),
    ('Bhopal', 23.2599, 77.4126),
    ('Agra', 27.1767, 78.0081)
]

# 3. Bulk Insert
insert_query = "INSERT INTO cities (city_name, lat, lng) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;"
cursor.executemany(insert_query, cities_data)

conn.commit()
cursor.close()
conn.close()

print("BINGO! 'cities' table successfully created and populated in Neon PostgreSQL.")