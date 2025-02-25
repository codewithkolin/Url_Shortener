from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
from datetime import datetime
import random
import string
import validators
import os

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()  # Secret key for flashing messages


# Database configuration
def get_db_connection():
    conn = sqlite3.connect('urls.db')
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database table
def init_db():
    with app.app_context():
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL
            )
        ''')
        conn.commit()
        conn.close()


init_db()


# Generate a unique short code
def generate_short_code():
    chars = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choices(chars, k=6))
        if not get_original_url(short_code):
            return short_code


# Retrieve original URL from database
def get_original_url(short_code):
    conn = get_db_connection()
    url = conn.execute(
        'SELECT original_url FROM urls WHERE short_code = ?', (short_code,)
    ).fetchone()
    conn.close()
    return url['original_url'] if url else None


# Home route with form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url'].strip()

        # Add scheme if missing
        if not original_url.startswith(('http://', 'https://')):
            original_url = f'http://{original_url}'

        # Validate URL
        if not validators.url(original_url):
            flash('Invalid URL. Please enter a valid web address')
            return redirect(url_for('index'))

        # Generate and save short code
        short_code = generate_short_code()
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO urls (original_url, short_code, created_at) VALUES (?, ?, ?)',
                (original_url, short_code, datetime.now())
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            flash('An error occurred. Please try again.')
            return redirect(url_for('index'))

        short_url = request.host_url + short_code
        return render_template('index.html', short_url=short_url)

    return render_template('index.html')


# Redirect route
@app.route('/<short_code>')
def redirect_to_url(short_code):
    original_url = get_original_url(short_code)
    if original_url:
        return redirect(original_url)
    else:
        abort(404)


# 404 error handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)