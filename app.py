from flask import Flask, render_template, request,redirect, url_for, session
from distutils.log import debug
from fileinput import filename
from PyPDF2 import PdfReader
from flask_mysqldb import MySQL
from winnowing import winnow
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
 
app = Flask(__name__)
app.secret_key='asdsdfsdfs13sdf_df%&'
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'duplicate_detection'
 
mysql = MySQL(app)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dologin',methods=['GET','POST'])
def dologin():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * FROM user WHERE username = %s and password = %s""", (username,password,))
        user = cursor.fetchone()
        # print(user)
        if user:
            session['username']=username
            session['id'] = user[0]
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    # return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username',None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    checklogin()
    # setup for first time
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM settings""")
    setting = cursor.fetchone()
    if not setting:
        cursor.execute(''' INSERT INTO settings(id, is_stemming, is_stopword, k_gram, hash, windows) VALUES(%s,%s,%s,%s,%s,%s)''',(1, 0, 0, 5,5,5))
        mysql.connection.commit()
    cursor.close()
    return render_template('home.html',tag='home')

@app.route('/user')
def user():
    checklogin()
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM user""")
    data = cursor.fetchall()
    cursor.close()
    # msg = ''
    # if status == 1:
    #     msg = 'Berhasil menambahkan user!'
    return render_template('user.html',tag='user', data=data)

@app.route('/edit-user', methods = ['POST'])
def edituser():
    if request.method == 'POST':  
        id = request.form['id']
        nama = request.form['nama']
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        if(password != ""):
            sql = "UPDATE user SET nama=%s, username=%s, password=%s WHERE id=%s"
            data = (nama, username, password, id,)
        else:
            sql = "UPDATE user SET nama=%s, username=%s WHERE id=%s"
            data = (nama, username, id,)
        cursor.execute(sql, data)
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('user'))
        # cursor.execute("""SELECT * FROM user WHERE username = %s""", (username,))
    # msg = ''
    # if status == 1:
    #     msg = 'Berhasil menambahkan user!'
    # return render_template('user.html',tag='user', data=data)
@app.route('/user/delete/<int:id>')
def deleteuser(id):
    cursor = mysql.connection.cursor()
    cursor.execute("""DELETE FROM user WHERE id = %s""", (id,))
    mysql.connection.commit()
    cursor.close()
    # msg = ''
    # if status == 1:
    #     msg = 'Berhasil menambahkan user!'
    return redirect(url_for('user'))

@app.route('/add-user', methods = ['POST'])  
def adduser():  
    if request.method == 'POST':  
        name = request.form['nama']
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * FROM user WHERE username = %s""", (username,))
        user = cursor.fetchone()
        status =''
        
        # cursor.close()
        if not user:
            # cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO user(nama, username, password) VALUES(%s,%s,%s)''',(name,username, password))
            mysql.connection.commit()
            status =1
            
        else:
            status =-1
            
        cursor.close()

        return redirect(url_for('user'))

@app.route('/sinonim/')
def sinonim():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('sinonim.html',tag='sinonim')
@app.route('/stopwords/')
def stopwords():
    checklogin()
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM stopwords""")
    
    data = cursor.fetchall()
    # for x in kata:
    #     cursor.execute(''' INSERT INTO stopwords(word) VALUES(%s)''',(x,))
    #     mysql.connection.commit()
    cursor.close()
    return render_template('stopwords.html',tag='stopwords', data=data)
@app.route('/add-stopwords/', methods = ['POST'])
def addstopwords():
    if request.method == 'POST':  
        # dump(request)
        kata = request.form['kata']

        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * FROM stopwords WHERE word = %s""", (kata,))
        result = cursor.fetchone()
        status =''
        
        # cursor.close()
        if not result:
            # cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO stopwords(word) VALUES(%s)''',(kata,))
            mysql.connection.commit()
            status =1
            
        else:
            status =-1
            
        cursor.close()
        # dump(request)
        return redirect(url_for('stopwords'))
@app.route('/edit-stopwords/', methods = ['POST'])
def editstopwords():
    if request.method == 'POST':  
        id = request.form['id']
        kata = request.form['kata']

        cursor = mysql.connection.cursor()
        sql = "UPDATE stopwords SET word=%s WHERE id=%s"
        data = (kata, id,)

        cursor.execute(sql, data)
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('stopwords'))
@app.route('/delete-stopwords/<int:id>')
def deletestopwords(id):
    cursor = mysql.connection.cursor()
    cursor.execute("""DELETE FROM stopwords WHERE id = %s""", (id,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('stopwords'))
@app.route('/kata-dasar/')
def katadasar():
    checklogin()
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM kata_dasar""")
    
    data = cursor.fetchall()

    return render_template('katadasar.html',tag='katadasar', data=data)
@app.route('/add-katadasar/', methods = ['POST'])
def addkatadasar():
    if request.method == 'POST':  
        # dump(request)
        kata = request.form['kata']

        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * FROM kata_dasar WHERE kata = %s""", (kata,))
        result = cursor.fetchone()
        status =''
        
        # cursor.close()
        if not result:
            # cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO kata_dasar(kata) VALUES(%s)''',(kata,))
            mysql.connection.commit()
            status =1
            
        else:
            status =-1
            
        cursor.close()
        # dump(request)
        return redirect(url_for('katadasar'))
@app.route('/edit-katadasar/', methods = ['POST'])
def editkatadasar():
    if request.method == 'POST':  
        id = request.form['id']
        kata = request.form['kata']

        cursor = mysql.connection.cursor()
        sql = "UPDATE kata_dasar SET kata=%s WHERE id=%s"
        data = (kata, id,)

        cursor.execute(sql, data)
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('katadasar'))
@app.route('/delete-katadasar/<int:id>')
def deletekatadasar(id):
    cursor = mysql.connection.cursor()
    cursor.execute("""DELETE FROM kata_dasar WHERE id = %s""", (id,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('katadasar'))
@app.route('/proses-deteksi/')
def deteksi():
    checklogin()
    return render_template('deteksi.html',tag='deteksi')

@app.route('/hasil-deteksi', methods = ['POST'])  
def hasil():  
    if request.method == 'POST':  
        files = request.files.getlist('file[]')
        # f.save(f.filename)
        isi = [];
        arrteks = []
        for x in files:
            reader = PdfReader(x)
            page = reader.pages[0]
            text = page.extract_text()    
            temp = { "filename" : x.filename, "text" : text}
            isi.append(temp)
            arrteks.append(text)
        text1 = arrteks[0]
        text2 = arrteks[1]

        #winnowing process
        has1 = winnow(text1)
        has2 = winnow(text2)
        #winnowing and jaccard
        arr1 = []
        for x in has1:
            arr1.append(x[1])
        arr2 = []
        for x in has2:
            arr2.append(x[1])
        similarity = jaccard_similarity(set(arr1), set(arr2))*100
        similarity = round(similarity, 2)
        winnows = []
        winnows.append(str(similarity)+"%")

        # winnow and cosine 
        # preprocessing
        arr1 = np.array(arr1)
        arr2 = np.array(arr2)
        len1 = len(arr1)
        len2 = len(arr2)
        if(len1 > len2):
            pad2 = np.pad(arr2, (0, len1-len2), 'constant')
            pad1 = arr1
        else:
            pad1 = np.pad(arr1, (0, len2-len1), 'constant')
            pad2 = arr2
        combined = np.vstack((pad1, pad2))
        similarity = cosine_similarity(combined)
        percentage = round(similarity[0][1], 2) * 100
        winnows.append(str(percentage)+"%")

        # Tfidf
        tfidf = TfidfVectorizer()
        arr = [text1, text2]
        tfidfs = []
        result = tfidf.fit_transform(arr)
        result = result.toarray()
        similarity = jaccard_similarity(set(result[0]), set(result[1]))*100
        tfidfs.append(str(round(similarity,2))+"%")

        # cosine
        similarity = cosine_similarity(result)
        percentage = similarity[0][1] * 100
        percentage = round(similarity[0][1], 2) * 100
        tfidfs.append(str(percentage)+"%")

        
        return render_template("hasil.html", tag='hasil', data = isi, winnow=winnows, tfidf=tfidfs)  
def jaccard_similarity(A, B):
    #Find intersection of two sets
    nominator = A.intersection(B)

    #Find union of two sets
    denominator = A.union(B)

    #Take the ratio of sizes
    similarity = len(nominator)/len(denominator)
    
    return similarity

@app.route('/settings/')
def setting():
    if 'username' not in session:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM settings """)
    setting = cursor.fetchone()
    cursor.close()
    return render_template('setting.html',tag='setting', data=setting)
@app.route('/edit-setting', methods = ['POST'])
def editsetting():
    if request.method == 'POST':  
        # dump(request)
        #
        stemming = 0
        stopword = 0
        if 'stemming' in request.form:
            stemming = 1
        if 'stopword' in request.form:
            stopword = 1
        # stemming = request.form['stemming']
        # stopword = request.form['stopword']
        kgram = request.form['kgram']
        _hash = request.form['hash']
        windows = request.form['windows']

        cursor = mysql.connection.cursor()
        cursor.execute("""UPDATE settings SET k_gram=%s, hash=%s, windows=%s, is_stemming=%s, is_stopword=%s WHERE id=1""", (kgram,_hash,windows,stemming,stopword,))        
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('setting'))
def checklogin():
    if 'username' not in session:
        return redirect(url_for('login'))    
if __name__ == '__main__':
    app.run(debug=True)
