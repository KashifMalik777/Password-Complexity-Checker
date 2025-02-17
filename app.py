from flask import Flask, render_template, request, jsonify
import re
import hashlib
import requests

app = Flask(__name__)

def get_leak_count(password):
    
    # Check if the password has been leaked using the Have I Been Pwned API.
    # Returns the number of times the password was seen in breaches.

    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]
    url = "https://api.pwnedpasswords.com/range/" + prefix
    try:
        response = requests.get(url)
        if response.status_code != 200:
            # If the API call fails, we return None.
            return None
    except Exception as e:
        return None

    hashes = (line.split(":") for line in response.text.splitlines())
    for hash_suffix, count in hashes:
        if hash_suffix == suffix:
            return int(count)
    return 0

def assess_password_strength(password):
    feedback = []
    score = 0

    # Check length Require at least 8 characters
    if len(password) < 8:
        feedback.append("Password is too short (should be at least 8 characters).")
    else:
        score += 1

    # Check for lowercase letters
    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Include at least one lowercase letter.")

    # Check for uppercase letters
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Include at least one uppercase letter.")

    # Check for digits
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Include at least one number.")

    # Check for special characters
    if re.search(r"[^\w\s]", password):  # Non-alphanumeric characters
        score += 1
    else:
        feedback.append("Include at least one special character.")

    # Determine strength based on score
    if score <= 2:
        strength = "Weak"
    elif score == 3:
        strength = "Moderate"
    elif score == 4:
        strength = "Strong"
    else:
        strength = "Very Strong"

    percent = int((score / 5) * 100)

    # Check if the password is leaked
    leak_count = get_leak_count(password)
    if leak_count is None:
        leak_message = "Could not verify if the password has been leaked."
    elif leak_count == 0:
        leak_message = "Good news — this password was NOT found in any known breaches."
    else:
        leak_message = f"Warning: This password has been leaked {leak_count} time(s)!"

    return strength, feedback, score, percent, leak_message

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assess', methods=['POST'])
def assess():
    data = request.get_json()
    password = data.get('password', '')
    strength, suggestions, score, percent, leak_message = assess_password_strength(password)
    return jsonify({
        'strength': strength, 
        'feedback': suggestions,
        'score': score,
        'percentage': percent,
        'password': password,  # (Note: In production, avoid sending plaintext passwords back.)
        'leakMessage': leak_message
    })

if __name__ == '__main__':
    app.run(debug=True)
