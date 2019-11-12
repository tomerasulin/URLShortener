import re, sqlite3,string,datetime,random
from urllib.parse import urlparse
from flask import Flask, request,render_template, redirect
from sqlite3 import Error
from urllib.request import urlopen


app = Flask(__name__)

#create DB
def create_DB():
    #creating table
    sql_url_table = """CREATE TABLE IF NOT EXISTS URLS(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    URL TEXT NOT NULL,
    SHORT TEXT NULL,
    TIME TEXT NOT NULL ,
    DAY TEXT NOT NULL );
    """
    #create a connection
    conn = create_connection()

    if conn is not None:
        try:
            conn.execute(sql_url_table)
            conn.commit()
            conn.close()
        except Error as e:
            print(e)

#create a connection to the SQLite database
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('urls.db')
    except Error as e:
        print(e)
    return conn

#function that randomly generate a new string for "short URL"
def encoder(num):
    return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(num))

#functino that receive a long url and check whether exists in DB
def query_select_long_db(url):
    #establish the connection to DB
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
         conn.close()
    except Error as e:
        print(e)
    return None

#function that receives a long URL and check whether there is a match of a short URL in DB
def query_select_short_db(url):
    # establish the connection to DB
    conn = create_connection()
    cursor = conn.cursor()
    try:
        #query DB
        cursor.execute('SELECT SHORT FROM URLS WHERE URL = ?',(url,))
        c = cursor.fetchone()
        cursor.execute('UPDATE URLS SET TIME = ?, DAY = ? WHERE URL = ?', (datetime.datetime.now().strftime("%H:%M:%S"), datetime.datetime.now().strftime("%d"),url))
        conn.commit()
        conn.close()
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
        cursor = conn.execute('INSERT INTO URLS(URL,SHORT,TIME,DAY) VALUES (?,?,?,?)',(url,short, datetime.datetime.now().strftime("%H:%M:%S"),datetime.datetime.now().strftime("%d")))
        conn.commit()   #save changes
        conn.close()
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
        conn.close()
        return ''.join(c)
    except Error as e:
        print(e)

#function that insert into the DB the invalid URL for control
def insert_bad_request(url):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor = conn.execute('INSERT INTO URLS(URL,TIME,DAY) VALUES (?,?,?)',(url,datetime.datetime.now().strftime("%H:%M:%S"),datetime.datetime.now().strftime("%d")))
        conn.commit()   #save changes
        conn.close()
    except Error as e:
        print(e)

#main page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('longURL') # receiving from the HTTP request the 'long URL'
        #insert the http scheme to the url in case is missing
        if urlparse(url).scheme == '':
            url = 'http://' + url
        try:
            #function that check if the URL is valid
            urlopen(url)
            if query_select_long_db(url) is not None: # check if the URL exists already in DB
                return  render_template('mainPage.html',short_url = query_select_short_db(url))
            return render_template('mainPage.html', short_url=query_insert_db(url)) # insert the new URL into DB and return his unique 'short URL'
        except Exception as e:
            insert_bad_request(url) #save the invalid URL
            return render_template('mainPage.html')
    return render_template('mainPage.html')

#redirect a short url to the long url
@app.route('/<short_url>')
def redirect_url(short_url):
    if request.method == 'POST':
        long_url = get_long_url(short_url)
        return redirect(long_url)
    return render_template('mainPage.html')

#get the DB stats , num of URLs pair, timestamp...
@app.route('/stats',methods=['GET','POST'])
def stats_urls():
    count = 0
    conn = create_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        #variables for the different requests from the user
        url_redirect_last_min = request.form.get('lastMin')
        url_redirect_last_hour = request.form.get('lastHour')
        url_redirect_last_day = request.form.get('lastDay')
        url_bad_last_min = request.form.get('lastMinBad')
        url_bad_last_hour = request.form.get('lastHourBad')
        url_bad_last_day = request.form.get('lastDayBad')
        num_of_redirect = request.form.get('redirectBtn')
        try:
            if url_redirect_last_min is not None or url_redirect_last_hour is not None or url_redirect_last_day is not None: #case of the number of redirection
                c = cursor.execute('SELECT TIME,DAY FROM URLS WHERE SHORT IS NOT NULL')
                for row in c:
                    (h,m,s) = ''.join(row[0]).split(':')
                    d = row[1]
                    if url_redirect_last_min is not None:
                        if datetime.datetime.now().minute > int(m) - 1 and datetime.datetime.now().minute < int(m) + 1:
                            count += 1
                    elif url_redirect_last_hour is not None:
                        if datetime.datetime.now().hour > int(h) - 1 and datetime.datetime.now().hour < int(h) + 1:
                            count += 1
                    elif url_redirect_last_day is not None:
                        if datetime.datetime.now().day > int(d) - 1 and datetime.datetime.now().day < int(d) + 1:
                            count += 1
                return render_template('stats.html', redir=count)
            elif url_bad_last_min is not None or url_bad_last_hour is not None or url_bad_last_day is not None: # case of the bad requests
                c = cursor.execute('SELECT TIME,DAY FROM URLS WHERE SHORT IS NULL')
                for row in c:
                    (h, m, s) = ''.join(row[0]).split(':')
                    d = row[1]
                    if url_bad_last_min is not None:
                        if datetime.datetime.now().minute > int(m) - 1 and datetime.datetime.now().minute < int(m) + 1:
                            count += 1
                    elif url_bad_last_hour is not None:
                        if datetime.datetime.now().hour > int(h) - 1 and datetime.datetime.now().hour < int(h) + 1:
                            count += 1
                    elif url_bad_last_day is not None:
                        if datetime.datetime.now().day > int(d) - 1 and datetime.datetime.now().day < int(d) + 1:
                            count += 1
                return render_template('stats.html', badtime=count)
            elif num_of_redirect is not None:   #case of the amount of pairs of long+short URLs
                cursor.execute('SELECT COUNT(URL) FROM URLS WHERE SHORT IS NOT NULL')
                c = cursor.fetchone()
                count = c[0]
            return render_template('stats.html', count=count)
        except Error as e:
            print(e)
    conn.close()
    return render_template('stats.html')

if __name__ == '__main__':
    #conn = create_connection()
    #conn.execute("DROP TABLE IF EXISTS URLS")
    create_DB()
    app.static_folder = 'static'
    app.run(debug=True)


