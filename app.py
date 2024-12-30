import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/Registration', methods=['GET', 'POST'])

def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username.isalpha() or not username:
            return render_template('Registration.html', error="please enter valid name")
        if len(password)<8 or not password:
            return render_template('Registration.html', error="password must be more than 8 chracters")

        conn = sqlite3.connect('blog.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user:
            return render_template('Registration.html', error="this user name is exist!")
        
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('Registration.html')


@app.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('blog.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password): 
            session['username'] = username
            return redirect(url_for('blogs'))
        else:
           return render_template('login.html', error="Wrong Password or User Name!")

    return render_template('login.html')


@app.route('/blogs')

def blogs():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()
    
  
    cursor.execute('''
        SELECT blogs.id, blogs.title, blogs.content, blogs.user_id, users.username
        FROM blogs
        JOIN users ON blogs.user_id = users.id
    ''')
    blogs = cursor.fetchall()
    conn.close()

    return render_template('blogs.html', blogs=blogs)


@app.route('/create_blog', methods=['GET', 'POST'])

def create_blog():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title or not content:
            return 'Title and content are required fields.'

        try:
            conn = sqlite3.connect('blog.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
            user_id = cursor.fetchone()[0]  
         
            cursor.execute('INSERT INTO blogs (title, content, user_id) VALUES (?, ?, ?)', (title, content, user_id))
            conn.commit()
            conn.close()

            return redirect(url_for('blogs'))  
        except Exception as e:
            return f'An error occurred: {e}'  

    return render_template('create_blog.html')  


@app.route('/edit_blog/<int:blog_id>', methods=['GET', 'POST'])
def edit_blog(blog_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM blogs WHERE id = ?', (blog_id,))
    blog = cursor.fetchone()

    if not blog:
        return 'Blog not found'
    cursor.execute('SELECT username FROM users WHERE id = ?', (blog[3],))
    owner_username = cursor.fetchone()[0]
    if owner_username != session['username']:
        return 'You do not have permission to edit this blog'

    if request.method == 'POST':
        
        title = request.form['title']
        content = request.form['content']
        cursor.execute('UPDATE blogs SET title = ?, content = ? WHERE id = ?', (title, content, blog_id))
        conn.commit()
        conn.close()

        return redirect(url_for('blogs'))
    conn.close()
    return render_template('blogs.html', blogs=fetch_blogs(), current_blog=blog)

def fetch_blogs():
    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT blogs.id, blogs.title, blogs.content, blogs.user_id, users.username 
                      FROM blogs 
                      JOIN users ON blogs.user_id = users.id''')
    blogs = cursor.fetchall()
    conn.close()
    return blogs


@app.route('/delete_blog/<int:blog_id>', methods=['POST'])


def delete_blog(blog_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM blogs WHERE id = ?', (blog_id,))
    blog = cursor.fetchone()

    if blog:
        cursor.execute('SELECT username FROM users WHERE id = ?', (blog[3],))
        owner_username = cursor.fetchone()[0]

        if owner_username == session['username']:
        
            cursor.execute('DELETE FROM blogs WHERE id = ?', (blog_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('blogs'))
        else:
            conn.close()
            return 'You do not have permission to delete this blog'
    else:
        conn.close()
        return 'Blog not found'



if __name__ == '__main__':
    app.run(debug=True)
