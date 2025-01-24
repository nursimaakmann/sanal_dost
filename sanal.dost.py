from flask import Flask, request, render_template_string, redirect, url_for, make_response
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 's3cr3t_key'

# Veritabanı bağlantısı
def get_db_connection():
    conn = sqlite3.connect('sanal_dost.db')
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı başlatma
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kullanıcılar için tablo
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password TEXT)''')
    
    # Duygular tablosu (ilk 4 duygu)
    cursor.execute('''CREATE TABLE IF NOT EXISTS emotions (
                        id INTEGER PRIMARY KEY,
                        emotion TEXT,
                        suggestion TEXT)''')
    
    # Kullanıcıların ruh hali geçmişi
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_emotions (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        emotion TEXT,
                        suggestion TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # İlk dört duygu için veriler
    cursor.execute("SELECT COUNT(*) FROM emotions")
    if cursor.fetchone()[0] == 0:
        emotions = [
            ('Happy', 'Bugün bu enerjinle yeni bir şey dene!'),
            ('Sad', 'Bir arkadaşını ara ve konuşmaya çalış.'), 
            ('Stressed', 'Derin nefes al, kısa bir yürüyüş yap.'),
            ('Unmotivated', 'Küçük bir hedef belirle ve başla.')
        ]
        cursor.executemany("INSERT INTO emotions (emotion, suggestion) VALUES (?, ?)", emotions)
    
    conn.commit()
    conn.close()

init_db()

# HTML Şablonu
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sanal Dost</title>
    <style>
        body {
            background-color: #B0A0D1;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            width: 80%;
            max-width: 400px;
            text-align: center;
        }
        h1 {
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        input[type="text"], input[type="password"], select, button {
            font-size: 16px;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            width: 100%;
        }
        button {
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        p {
            margin-top: 10px;
        }
        .emotion-option {
            font-size: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sanal Dost Uygulaması</h1>
        <div>
            {% if not user %}
            <p><a href="{{ url_for('login') }}">Giriş Yap</a> | <a href="{{ url_for('register') }}">Kayıt Ol</a></p>
            {% else %}
            <p>Hoşgeldiniz, <strong>{{ user['username'] }}</strong>!</p>
            <a href="{{ url_for('logout') }}">Çıkış Yap</a>
            <form method="POST">
                <label for="emotion"><strong>Ruh halinizi seçin:</strong></label>
                <select name="emotion" id="emotion">
                    <option value="Happy" {% if selected_emotion == 'Happy' %}selected{% endif %} class="emotion-option">&#128522; Mutlu</option>
                    <option value="Sad" {% if selected_emotion == 'Sad' %}selected{% endif %} class="emotion-option">&#128546; Üzgün</option>
                    <option value="Stressed" {% if selected_emotion == 'Stressed' %}selected{% endif %} class="emotion-option">&#128561; Stresli</option>
                    <option value="Unmotivated" {% if selected_emotion == 'Unmotivated' %}selected{% endif %} class="emotion-option">&#128577; Motivasyonsuz</option>
                </select>
                <button type="submit">Öneri Al</button>
            </form>
            {% if suggestion %}
            <h2>Öneriniz:</h2>
            <p>{{ suggestion }}</p>
            {% endif %}
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# Giriş ve Kayıt HTML Şablonu
LOGIN_REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            background-color: #B0A0D1;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            width: 80%;
            max-width: 400px;
            text-align: center;
        }
        h1 {
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        input[type="text"], input[type="password"] {
            font-size: 16px;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            width: 100%;
        }
        button {
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <form method="POST">
            Kullanıcı Adı: <input type="text" name="username" required><br>
            Şifre: <input type="password" name="password" required><br>
            <button type="submit">{{ button_text }}</button>
        </form>
        <p>{{ message }}</p>
    </div>
</body>
</html>
'''

# Flask Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    suggestion = None
    selected_emotion = None
    user = None

    if 'user_id' in request.cookies:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (request.cookies['user_id'],))
        user = cursor.fetchone()
        conn.close()

    if request.method == 'POST' and user:
        selected_emotion = request.form['emotion']
        
        # Debug: Seçilen duyguyu kontrol et
        print(f"Seçilen duygu: {selected_emotion}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT suggestion FROM emotions WHERE emotion = ?", (selected_emotion,))
        result = cursor.fetchone()

        # Debug: Çekilen öneriyi kontrol et
        print(f"Çekilen öneri: {result}")

        if result:
            suggestion = result[0]
            cursor.execute("INSERT INTO user_emotions (user_id, emotion, suggestion) VALUES (?, ?, ?)", 
                           (user['id'], selected_emotion, suggestion))
            conn.commit()
        else:
            suggestion = "Bu duygu için bir öneri bulunmamaktadır."
        conn.close()

    return render_template_string(HTML_TEMPLATE, suggestion=suggestion, selected_emotion=selected_emotion, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('user_id', str(user['id']))
            return resp
        else:
            return 'Geçersiz giriş'

    return render_template_string(LOGIN_REGISTER_TEMPLATE, title="Giriş Yap", button_text="Giriş Yap", message="")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))

    return render_template_string(LOGIN_REGISTER_TEMPLATE, title="Kayıt Ol", button_text="Kayıt Ol", message="")

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('home')))
    resp.delete_cookie('user_id')
    return resp

if __name__ == '__main__':
    app.run(debug=True)

