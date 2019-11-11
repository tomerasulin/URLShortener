import re
from urllib.parse import urlparse
from flask import Flask, request,render_template, redirect
from sqlite3 import Error
import sqlite3,string
import random

app = Flask(__name__)

#create DB
def create_DB():
    #creating table
    sql_url_table = """CREATE TABLE IF NOT EXISTS URLS(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    URL TEXT NOT NULL,
    SHORT TEXT NOT NULL,
    TIME DATETIME DEFAULT CURRENT_TIMESTAMP);
    """
    #create a database connection
    conn = create_connection()

    if conn is not None:
        try:
            conn.execute(sql_url_table)
            conn.commit()
        except Error as e:
            print(e)

#create a database connection to the SQLite database
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('urls.db')
    except Error as e:
        print(e)
    return conn

#function that randomly generate a new string in length of 'num'
def encoder(num):
    return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(num))

#functino that receive a long url and check whether exists in DB
def query_select_long_db(url):
    #assembling the connection to DB
    conn = create_connection()
    cursor = conn.cursor()
    try:
        #query the DB
         cursor.execute('SELECT URL FROM URLS WHERE URL = ?',(url,))
         c = cursor.fetchone()
         if (c == None):        #in case empty
             return None
         for row in c:          #case of already exists
             if (row == url):
                 return url
    except Error as e:
        print(e)
    return None

#function that receives a long URL and check whether there is a match of a short URL in DB
def query_select_short_db(url):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT SHORT FROM URLS WHERE URL = ?',(url,))
        c = cursor.fetchone()
        return ''.join(c)
    except Error as e:
        print(e)
    return None

#function that insert into the DB the long and short URLs pairs
def query_insert_db(url):
    #calling to function which encode the url
    short = encoder(random.randint(1,6))
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor = conn.execute('INSERT INTO URLS(URL,SHORT) VALUES (?,?)',(url,short))
        conn.commit()   #save changes
    except Error as e:
        print(e)
    return short

#function that receives a short url and return the appropriate long url
def get_long_url(short):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT URL FROM URLS WHERE SHORT = ?',(short,))
        c = cursor.fetchone()
        return ''.join(c)
    except Error as e:
        print(e)

#function that receives an URL and check whether is legal
def bad_request(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    print(re.match(regex,url))

    return re.match(regex,url)
#main page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('longURL')
        if urlparse(url).scheme == '':
            url = 'http://' + url
        if(bad_request(url) is not None):
            if query_select_long_db(url) is not None:
                return  render_template('mainPage.html',short_url = query_select_short_db(url))
            return render_template('mainPage.html', short_url=query_insert_db(url))
        return render_template(url,code=404)
    return render_template('mainPage.html')

#redirect a short url to the long url
@app.route('/<short_url>')
def redirect_url(short_url):
    long_url = get_long_url(short_url)
    return redirect(long_url)

#get the DB stats , num of URLs pair, timestamp...
@app.route('/stats')
def stats_urls():
    time_list = list()
    conn = create_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        url_redirect = request.get('URLRed')
        url_bad_request = request.get('badReq')
        try:
            if url_redirect is not None:
                c = cursor.execute('SELECT TIME FROM URLS')
                for row in c:
                    if row < url_redirect:
                        time_list.append(row)
        except Error as e:
            print(e)
    try:
        cursor.execute('SELECT COUNT(*) FROM URLS')
        c = cursor.fetchone()
        return render_template('stats.html', count=c[0], time_redirect=time_list)
    except Error as e:
        print(e)

if __name__ == '__main__':
    #conn = create_connection()
    #conn.execute("DROP TABLE IF EXISTS URLS")
    create_DB()
    app.run(debug=True)


