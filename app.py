from typing import List, Dict
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from email_validator import validate_email, EmailNotValidError
import os
from itsdangerous import URLSafeTimedSerializer
import mysql.connector
import json

app = Flask(__name__)
app.secret_key = '12345'


def get_db_connection():
    config = {
        'user': 'root',
        'password': 'root',
        'host': 'db',
        'port': '3306',
        'database': 'bankdb'
    }
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except mysql.connector.Error as err:
        print("Error connecting to MySQL database: {}".format(err))
        return None


@app.route('/')
def home():
    logged_in = 'email' in session
    return render_template('index.html', logged_in=logged_in, email=session.get('email'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            v = validate_email(email)  # validate and get info
            email = v["email"]  # replace with normalized form
        except EmailNotValidError as e:
            flash('Invalid email address!')
            return render_template('register.html'), 400
        if not password:
            flash('Password is required!')
            return render_template('register.html'), 400
        
       # ...验证和邮箱检查的代码...
        connection = get_db_connection()
        if connection is None:
            flash('Unable to connect to the database. Please try again later.')
            return render_template('register.html'), 500
        cursor = connection.cursor(buffered=True)
        try:
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone() is not None:
                flash('Email already exists!')
                return render_template('register.html'), 400
            # 保存新用户
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            connection.commit()
            flash('Registration successful!')
            session['email'] = email
            session['logged_in'] = True
            return redirect(url_for('home'))
        except mysql.connector.Error as err:
            flash('An error occurred during registration. Please try again.')
            print("Something went wrong: {}".format(err))
            return render_template('register.html'), 500
        finally:
            cursor.close()
            connection.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        connection = get_db_connection()
        if connection is None:
            flash('Unable to connect to the database. Please try again later.')
            return render_template('login.html'), 500
        cursor = connection.cursor(buffered=True)
        try:
            cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result is None:
                flash('Invalid email or password.')
                return render_template('login.html'), 400
            hashed_password = result[0]
            if not check_password_hash(hashed_password, password):
                flash('Invalid email or password.')
                return render_template('login.html'), 400
            session['email'] = email
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('home'))
        finally:
            cursor.close()
            connection.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功注销。', 'success')
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    # 此处应检索用户数据，如个人资料信息和头像等
    # user = get_user_profile(email)  # 示例函数，您需要根据实际情况实现
    # return render_template('profile.html', user=user)
    return render_template('profile.html', email=email)  # 暂时使用邮箱作为示例
    
@app.route('/comments')
def comments():
    if 'logged_in' not in session:
        flash('You need to be logged in to view comments.')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM abstracts")
        abstracts_data = cursor.fetchall()
        cursor.execute("SELECT * FROM introductory_materials")
        intro_data = cursor.fetchall()
    except mysql.connector.Error as err:
        flash('An error occurred while fetching comments: {}'.format(err))
        abstracts_data, intro_data = [], []
    finally:
        cursor.close()
        connection.close()

    return render_template('comments.html', abstracts=abstracts_data, intro=intro_data)

@app.route('/submit_comments', methods=['POST'])
def submit_comments():
    if 'logged_in' not in session or 'email' not in session:
        flash('请先登录再提交评论。')
        return redirect(url_for('login'))
    
    user_email = session['email']  # 从会话中获取用户邮箱
    abstracts_ids = request.form.getlist('abstracts_ids')  # 获取选中的摘要ID
    intros_ids = request.form.getlist('intros_ids')  # 获取选中的介绍材料ID

    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。')
        return redirect(url_for('comments'))

    try:
        with connection.cursor() as cursor:
            # 获取当前用户的 user_id
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
            user_id_result = cursor.fetchone()
            if user_id_result:
                user_id = user_id_result[0]

                # 遍历所有选中的摘要ID，并插入到abstracts_comments表中
                for abstract_id in abstracts_ids:
                    cursor.execute(
                        "INSERT INTO abstracts_comments (user_id, abstract_id, comment) VALUES (%s, %s, (SELECT content FROM abstracts WHERE id = %s))",
                        (user_id, abstract_id, abstract_id)
                    )

                # 遍历所有选中的介绍材料ID，并插入到introductory_comments表中
                for intro_id in intros_ids:
                    cursor.execute(
                        "INSERT INTO introductory_comments (user_id, intro_material_id, comment) VALUES (%s, %s, (SELECT content FROM introductory_materials WHERE id = %s))",
                        (user_id, intro_id, intro_id)
                    )

                connection.commit()
                flash('评论提交成功。')
            else:
                flash('用户未找到。')
                return redirect(url_for('comments'))

    except mysql.connector.Error as err:
        connection.rollback()
        flash(f'提交评论时发生错误：{err}')
        return redirect(url_for('comments'))
    finally:
        if connection.is_connected():
            connection.close()

    return redirect(url_for('home'))



@app.route('/view_comments')
def view_comments():
    if 'logged_in' not in session or 'email' not in session:
        flash('请先登录再查看评论。')
        return redirect(url_for('login'))

    email = session['email']
    connection = get_db_connection()
    
    if not connection:
        flash('数据库连接失败。')
        return render_template('view_comments.html', abstracts_comments=[], intros_comments=[])
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # 先获取用户的ID
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_result = cursor.fetchone()
            user_id = user_result['id'] if user_result else None

            # 如果有有效的user_id，则获取该用户的评论
            if user_id:
                cursor.execute("SELECT id, comment FROM abstracts_comments WHERE user_id = %s", (user_id,))
                abstracts_comments = cursor.fetchall()

                cursor.execute("SELECT id, comment FROM introductory_comments WHERE user_id = %s", (user_id,))
                intros_comments = cursor.fetchall()
            else:
                flash('未找到用户。')
                return redirect(url_for('home'))

    except mysql.connector.Error as err:
        flash(f'获取评论时发生错误：{err}')
        abstracts_comments = []
        intros_comments = []
    finally:
        connection.close()

    return render_template('view_comments.html', abstracts_comments=abstracts_comments, intros_comments=intros_comments)


@app.route('/delete_comment/<int:comment_id>/<comment_type>', methods=['POST'])
def delete_comment(comment_id, comment_type):
    if 'logged_in' not in session or 'email' not in session:
        flash('请先登录。')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('数据库连接失败。')
        return redirect(url_for('view_comments'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            email = session['email']
            # 先获取用户的ID
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            user_id = user['id'] if user else None

            # 检查评论是否属于当前登录用户
            if comment_type == 'abstract':
                cursor.execute("SELECT user_id FROM abstracts_comments WHERE id = %s", (comment_id,))
            else:
                cursor.execute("SELECT user_id FROM introductory_comments WHERE id = %s", (comment_id,))
            
            comment_owner = cursor.fetchone()
            if comment_owner and comment_owner['user_id'] == user_id:
                # 用户拥有该评论，可以删除
                if comment_type == 'abstract':
                    cursor.execute("DELETE FROM abstracts_comments WHERE id = %s", (comment_id,))
                else:
                    cursor.execute("DELETE FROM introductory_comments WHERE id = %s", (comment_id,))
                connection.commit()
                flash('评论已删除。')
            else:
                flash('您无法删除该评论。')
    except mysql.connector.Error as err:
        connection.rollback()
        flash(f'删除评论时发生错误：{err}')
    finally:
        connection.close()

    return redirect(url_for('view_comments'))



@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    greeting = f'Hello, {name}!'
    return render_template('greet.html', greeting=greeting)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedback = request.form['feedback']
        return redirect(url_for('feedbackresult', feedback=feedback))
    return render_template('feedback.html')

@app.route('/feedbackresult/<feedback>')
def feedbackresult(feedback):
    return render_template('feedbackresult.html', feedback=feedback)

@app.route('/message')
def message():
    message = "Have a great day!"
    return render_template('message.html', message=message)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/current-time')
def current_time():
    now = datetime.datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return render_template('current_time.html', time=formatted_time)

@app.route('/api')
def api():
    return jsonify({"message": "Welcome to our API"})

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    images = ['image1.jpg', 'image2.jpg', 'image3.jpg']
    return render_template('gallery.html', images=images)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    return render_template('confirmation.html', name=name, email=email)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)