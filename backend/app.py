from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import random
import re
import math
import mysql.connector
import os
from ai_matchmaker import get_best_matches
import urllib.parse

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "super_secret_hackathon_key"

# ==========================================
# MYSQL CONNECTION
# ==========================================
def get_db():
    # Tumhare balance_db.py ke hisaab se local MySQL credentials
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "admin123"),
        database=os.getenv("DB_NAME", "login1")
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_verified_experts(cursor):
    """MySQL compatible query: use RAND() instead of RANDOM()"""
    cursor.execute("""
        (SELECT * FROM volunteers WHERE skills = 'IT Support' AND exp IN ('>10', '10+', '10-15') LIMIT 1)
        UNION ALL
        (SELECT * FROM volunteers WHERE skills = 'Teaching' AND gender = 'female' AND exp IN ('>10', '10+', '10-15') LIMIT 1)
        UNION ALL
        (SELECT * FROM volunteers WHERE skills = 'Healthcare' AND gender = 'female' AND exp IN ('>10', '10+', '10-15') LIMIT 1)
        UNION ALL
        (SELECT * FROM volunteers WHERE skills = 'Event Management' AND exp IN ('>10', '10+', '10-15') LIMIT 1)
    """)
    experts = cursor.fetchall()
    
    if not experts or len(experts) < 4:
        kami = 4 - len(experts) if experts else 4
        if kami > 0:
            cursor.execute(f"SELECT * FROM volunteers ORDER BY RAND() LIMIT {kami}")
            extra_vols = cursor.fetchall()
            experts.extend(extra_vols)
            
    return experts

# ==========================================
# 1. HOME & LOGIN ROUTE 
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def home():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    recommended_vols = get_verified_experts(cursor)
    error_msg = None

    if request.method == 'POST':
        email = request.form.get('Username')
        password = request.form.get('Password')

        if not email or not password:
            error_msg = "All fields required!"
        else:
            cursor.execute("SELECT * FROM users WHERE username=%s", (email,))
            user = cursor.fetchone()

            if user:
                if user['password'] == password:
                    session['user_email'] = email 
                    cursor.close()
                    db.close()
                    return redirect(url_for('filter_page'))
                else:
                    error_msg = "Wrong Password! Please try again."
            else:
                error_msg = "Account not found! Please Sign Up first."

    cursor.close()
    db.close()
    return render_template("index.html", recommended_vols=recommended_vols, error=error_msg)

# ==========================================
# 2. SIGN UP ROUTE
# ==========================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('Username')
        password = request.form.get('Password')

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            db.close()
            return "<h3>Email already registered! Please <a href='/'>Login</a>.</h3>"
            
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (email, password))
        db.commit()
        cursor.close()
        db.close()
        
        return redirect(url_for('home'))
        
    return render_template("signup.html")

# ==========================================
# 3. LOGOUT ROUTE 
# ==========================================
@app.route('/logout')
def logout():
    session.pop('user_email', None) 
    return redirect(url_for('home'))

# ==========================================
# 4. NGO DASHBOARD (FILTER PAGE)
# ==========================================
@app.route('/filter')
def filter_page():
    user_email = session.get('user_email', 'Guest')      
    db = get_db()
    cursor = db.cursor(dictionary=True)
    recommended_vols = get_verified_experts(cursor)
    
    # Jinja template ke liye initial critical cities
    cursor.execute("SELECT city_name FROM cities ORDER BY RAND() LIMIT 3")
    cities_data = cursor.fetchall()
    critical_cities = [c['city_name'] for c in cities_data]
    
    cursor.close()
    db.close()
    return render_template('filter.html', user_email=user_email, recommended_vols=recommended_vols, critical_cities=critical_cities)

# ==========================================
# 5. API: LIVE HEATMAP
# ==========================================
@app.route('/api/live-heatmap')
def live_heatmap():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT city_name, lat, lng FROM cities WHERE lat IS NOT NULL AND lng IS NOT NULL ORDER BY RAND() LIMIT 20") 
    cities = cursor.fetchall()
    
    hotspots = [[float(c['lat']), float(c['lng']), round(random.uniform(0.5, 1.0), 2)] for c in cities]
    critical_cities = [c['city_name'] for c in cities[:3]]
    
    cursor.close()
    db.close()
    
    return jsonify({
        "critical_cities": critical_cities,
        "hotspots": hotspots
    })

# ==========================================
# 6. AI SMART SEARCH
# ==========================================
@app.route('/ai-search', methods=['GET', 'POST'])
def ai_search():
    user_email = session.get('user_email', 'Guest')
    ngo_query = request.values.get('ai_query')

    if not ngo_query:
        return redirect(url_for('filter_page'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    words = ngo_query.lower().replace(',', '').replace('.', '').split()
    target_city, target_lat, target_lng = None, None, None
    
    for word in words:
        if len(word) > 2:
            cursor.execute("SELECT city_name, lat, lng FROM cities WHERE LOWER(city_name) = %s LIMIT 1", (word,))
            result = cursor.fetchone()
            if result:
                target_city = result['city_name']
                target_lat = float(result['lat'])
                target_lng = float(result['lng'])
                break
                
    cursor.execute("""
        SELECT v.*, c.lat, c.lng 
        FROM volunteers v
        LEFT JOIN cities c ON LOWER(v.locn) = LOWER(c.city_name)
    """)
    all_volunteers = cursor.fetchall()
    cursor.close()
    db.close()
    
    skills_query = ngo_query.lower()
    
    try:
        ranked_results = get_best_matches(skills_query, all_volunteers)
    except NameError:
        ranked_results = all_volunteers

    final_results = []
    for vol in ranked_results:
        if target_lat and target_lng and vol.get('lat') and vol.get('lng'):
            dist = calculate_distance(target_lat, target_lng, float(vol['lat']), float(vol['lng']))
            vol['distance_km'] = round(dist, 1)
        else:
            vol['distance_km'] = 99999
            
        final_results.append(vol)

    if target_city:
        final_results = sorted(final_results, key=lambda k: (-k.get('match_score', 0), k.get('distance_km', 99999)))
    else:
        final_results = sorted(final_results, key=lambda k: -k.get('match_score', 0))

    # Pagination logic fix
    page = request.args.get('page', 1, type=int)
    total_pages = math.ceil(len(final_results) / 5) if final_results else 1
    paginated_data = final_results[(page-1)*5 : page*5]

    return render_template('result.html', volunteers=paginated_data, ai_search=True, ai_query=ngo_query, user_email=user_email, page=page, total_pages=total_pages)

# ==========================================
# 7. MANUAL SEARCH 
# ==========================================
@app.route('/search', methods=['GET', 'POST']) 
def search_volunteers():
    user_email = session.get('user_email', 'Guest')      
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    skills = request.values.get('skills')
    location = request.values.get('location')
    
    query = "SELECT * FROM volunteers WHERE 1=1"
    params = []

    if skills: 
        query += " AND skills = %s"
        params.append(skills)
    if location: 
        query += " AND locn = %s"
        params.append(location)

    cursor.execute(query, tuple(params))
    all_filtered_data = cursor.fetchall()
    
    cursor.close()
    db.close()

    # Pagination logic fix
    page = request.args.get('page', 1, type=int)
    total_pages = math.ceil(len(all_filtered_data) / 5) if all_filtered_data else 1
    paginated_data = all_filtered_data[(page-1)*5 : page*5]

    return render_template('result.html', volunteers=paginated_data, user_email=user_email, page=page, total_pages=total_pages)

# ==========================================
# 8. PROFILE DETAIL
# ==========================================
@app.route('/volunteer/<int:VolunteerId>')
def volunteer_detail(VolunteerId):
    user_email = session.get('user_email', 'Guest')      
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM volunteers WHERE VolunteerId = %s", (VolunteerId,))
    vol_data = cursor.fetchone()

    cursor.close()
    db.close()
    
    return render_template('detail.html', vol=vol_data, user_email=user_email)

# ==========================================
# 9. SUPPORT PAGE ROUTE 
# ==========================================
@app.route('/support', methods=['GET', 'POST'])
def support_page():
    user_email = session.get('user_email', 'Guest') 
    success_msg = None

    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        issue = request.form.get('issue')
        message = request.form.get('message')

        if fullname and email and issue and message:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO support_tickets (fullname, email, issue, message) 
                VALUES (%s, %s, %s, %s)
            """, (fullname, email, issue, message))
            db.commit()
            cursor.close()
            db.close()
            success_msg = "Mission Accomplished!"

    return render_template('support.html', user_email=user_email, success_msg=success_msg)

if __name__ == '__main__':
    app.run(debug=True)
