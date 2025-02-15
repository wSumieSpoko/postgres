from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Klucz do obsługi flash messages

# Ustawienia połączenia z bazą danych PostgreSQL
db_params = {
    "host": "localhost",
    "database": "Y&Y",
    "user": "postgres",
    "password": "1234",
    "port": 5432
}

# Funkcja do połączenia się z bazą danych
def get_db_connection():
    conn = psycopg2.connect(**db_params)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE name = %s', (name,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        flash('User already exists, choose another name.', 'error')
        return redirect(url_for('index'))
    
    cursor.execute('INSERT INTO users (name, password) VALUES (%s, %s)', (name, password))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('You have successfully registered!', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE name = %s AND password = %s', (name, password))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        session['user_name'] = name  # Zapisujemy nazwę użytkownika w sesji
        flash(f'Login successful! Welcome, {session["user_name"]}.', 'success')
        return redirect(url_for('calendar'))  # Przekierowanie na stronę kalendarza
    else:
        flash('Invalid credentials, please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/calendar')
def calendar():
    if 'user_name' not in session:
        flash('You must be logged in to access the calendar.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sortowanie wydarzeń od najnowszego do najstarszego
    cursor.execute('SELECT event_date, event_time, description FROM events WHERE user_name = %s ORDER BY event_date DESC, event_time DESC', (session['user_name'],))
    events = cursor.fetchall()  # Pobieramy wydarzenia użytkownika
    
    cursor.close()
    conn.close()
    
    return render_template('index2.html', user_name=session['user_name'], events=events)

@app.route('/add_event', methods=['POST'])
def add_event():
    if 'user_name' not in session:
        flash('You must be logged in to add events.', 'error')
        return redirect(url_for('index'))

    event_date = request.form['event_date']
    event_time = request.form['event_time']
    description = request.form['description']
    user_name = session['user_name']

    if not event_date or not event_time or not description:
        flash('All fields are required!', 'error')
        return redirect(url_for('calendar'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    
        cursor.execute('INSERT INTO events (user_name, event_date, event_time, description) VALUES (%s, %s, %s, %s)',
                       (user_name, event_date, event_time, description))
    
        conn.commit()
        cursor.close()
        conn.close()
    
        flash('Event added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('calendar'))

@app.route('/delete_event', methods=['POST'])
def delete_event():
    if 'user_name' not in session:
        flash('You must be logged in to delete events.', 'error')
        return redirect(url_for('index'))

    event_date = request.form['event_date']
    event_time = request.form['event_time']
    user_name = session['user_name']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Usuwanie wydarzenia
        cursor.execute('DELETE FROM events WHERE user_name = %s AND event_date = %s AND event_time = %s',
                       (user_name, event_date, event_time))
        conn.commit()

        cursor.close()
        conn.close()

        flash('Event deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('calendar'))


@app.route('/logout')
def logout():
    session.pop('user_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
