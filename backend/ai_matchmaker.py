import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def enhance_query(query):
    query = query.lower()
    
    # 1. Experience Mapping
    numbers = re.findall(r'\d+', query)
    if numbers:
        exp_num = int(numbers[0])
        if exp_num <= 5:
            query += " exp_beginner"
        elif exp_num <= 10:
            query += " exp_intermediate"
        else:
            query += " exp_expert"

    # 2. Skill Mapping
    if any(word in query for word in ["tech", "computer", "hardware", "software"]):
        query += " it support"
    if any(word in query for word in ["medical", "doctor", "nurse", "clinic"]):
        query += " healthcare"
    if any(word in query for word in ["teacher", "tutor", "educator", "teach"]):
        query += " teaching"
    if any(word in query for word in ["manage", "organize", "coordinator"]):
        query += " event management"

    # 3. Gender Mapping (Smart Detection)
    if any(word in query for word in ["female", "woman", "lady", "girl"]):
        query += " female"
    elif any(word in query for word in ["male", "man", "boy", "guy"]): # "IT guy" likhne par ye automatically male select karega
        query += " male"

    # 4. Work Type Mapping (Remote vs On-Site)
    if any(word in query for word in ["remote", "online", "virtual", "home"]):
        query += " remote"
    elif any(word in query for word in ["on-site", "onsite", "physical", "in-person", "office"]):
        query += " on-site"

    # 5. Availability Mapping
    if any(word in query for word in ["weekend", "saturday", "sunday"]):
        query += " weekends"
    elif any(word in query for word in ["weekday", "monday", "tuesday", "wednesday", "thursday", "friday"]):
        query += " weekdays"
    elif any(word in query for word in ["flexible", "anytime", "any day"]):
        query += " flexible"

    return query


def get_best_matches(ngo_query, volunteers_data):
    if not volunteers_data:
        return []

    # Smart Query banalo
    smart_query = enhance_query(ngo_query)
    
    print(f"👉 Original Query: {ngo_query}")
    print(f"🧠 Enhanced Query: {smart_query}")

    profiles = []
    for vol in volunteers_data:
        # Experience tokenization
        exp_db = vol.get('exp', '')
        exp_token = ""
        if exp_db == '0-5':
            exp_token = "exp_beginner"
        elif exp_db == '5-10':
            exp_token = "exp_intermediate"
        elif exp_db == '>10':
            exp_token = "exp_expert"

        # 🌟 FIX: Profile text me gender, availability aur work_type bhi add kar diya
        # Taaki AI in sabko padh kar match kar sake
        profile_text = f"{vol.get('skills', '')} {vol.get('work_type', '')} {vol.get('locn', '')} {exp_token} {vol.get('gender', '')} {vol.get('availability', '')}"
        
        profiles.append(profile_text.lower())

    # NGO Query ko sabse upar daalo
    all_texts = [smart_query] + profiles

    # AI Model (TF-IDF + Cosine Similarity)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    for i, vol in enumerate(volunteers_data):
        vol['match_score'] = round(cosine_sim[i] * 100, 1)

    # Sort results highest to lowest
    ranked_volunteers = sorted(volunteers_data, key=lambda x: x['match_score'], reverse=True)

    # 10% threshold filter (Sirf relevant results dikhayega)
    filtered_results = [v for v in ranked_volunteers if v['match_score'] > 10.0]
    
    return filtered_results
