import os
from flask import Flask, render_template, request,redirect, url_for, session, json, current_app as app, jsonify, json
from distutils.log import debug
from fileinput import filename
from PyPDF2 import PdfReader
from flask_mysqldb import MySQL
from winnowing import winnow
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial import distance
import numpy as np
import re,string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

 
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
    if 'username' not in session:
        return redirect(url_for('login'))
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
    if 'username' not in session:
        return redirect(url_for('login'))
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
@app.route('/add-sinonim/', methods = ['POST'])
def addsinonim():
    if request.method == 'POST':  
        # dump(request)
        kata = request.form['kata']
        sinonim = request.form['sinonim']

        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * FROM kamus_sinonim WHERE kata = %s""", (kata,))
        result = cursor.fetchone()
        status =''
        
        # cursor.close()
        if not result:
            # cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO kamus_sinonim(kata, sinonim) VALUES(%s,%s)''',(kata,sinonim,))
            mysql.connection.commit()
            status =1
            
        else:
            status =-1
            
        cursor.close()
        # dump(request)
        return redirect(url_for('sinonim'))
@app.route('/edit-sinonim/', methods = ['POST'])
def editsinonim():
    if request.method == 'POST':  
        id = request.form['id']
        kata = request.form['kata']
        sinonimnya = request.form['sinonim']

        cursor = mysql.connection.cursor()
        sql = "UPDATE kamus_sinonim SET kata=%s, sinonim=%s WHERE id=%s"
        data = (kata,sinonimnya, id,)

        cursor.execute(sql, data)
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('sinonim'))
@app.route('/delete-sinonim/<int:id>')
def deletesinonim(id):
    cursor = mysql.connection.cursor()
    cursor.execute("""DELETE FROM kamus_sinonim WHERE id = %s""", (id,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('sinonim'))
@app.route('/stopwords/')
def stopwords():

    if 'username' not in session:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM stopwords""")
    
    data = cursor.fetchall()
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
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('katadasar.html',tag='katadasar')
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
        changes = []
        for x in files:
            if(x.filename.endswith('.pdf')):
                reader = PdfReader(x)
                page = reader.pages[0]
                text = page.extract_text()    
            elif (x.filename.endswith('.txt')):
                f  = x
                # f.save(secure_filename(x.filename))
                text = f.read()
                text = str(text, 'utf-8')

            temp = { "filename" : x.filename, "text" : text}
            isi.append(temp)
            arrteks.append(text)
        text1 = arrteks[0]
        text2 = arrteks[1]
        changes.append(['Original Text', text1, text2])

        # setting
        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * FROM settings """)
        setting = cursor.fetchone()
        cursor.close()

        text1 = casefolding(text1)
        text2 = casefolding(text2)
        changes.append(['Case Folding', text1, text2])

        if(setting[2] ==1):
            text1 = stopword_removal(text1)
            text2 = stopword_removal(text2)
            changes.append(['Stopword Removal',text1, text2])

        if(setting[1] ==1):
            text1 = stemming(text1)
            text2 = stemming(text2)
            changes.append(['Stemming',text1, text2])        

        if(setting[6] ==1):
            # synonym recognition
            text1, text2 = synonym(text1, text2)
            changes.append(['Synonym Recognition',text1, text2])                
        #winnowing process
        has1 = winnow(text1)
        has2 = winnow(text2)
        changes.append(['Winnowing',has1, has2])        
        #winnowing and jaccard
        arr1 = []
        for x in has1:
            arr1.append(x[1])
        arr2 = []
        for x in has2:
            arr2.append(x[1])

        similarity = jaccard_similarity(set(arr1), set(arr2))
        
        
        winnows = []
        winnows.append(similarity)

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
        similarity = cosine(combined)
        winnows.append(similarity)

        # winnow and dice_similarity
        similarity = dice_similarity(set(arr1), set(arr2))
        winnows.append(similarity)

        # Tfidf
        tfidf = TfidfVectorizer()
        arr = [text1, text2]
        tfidfs = []
        result = tfidf.fit_transform(arr)
        result = result.toarray()
        similarity = jaccard_similarity(set(result[0]), set(result[1]))
        tfidfs.append(similarity)
        changes.append(['TF-IDF',result[0], result[1]])        

        # cosine
        similarity = cosine(result)
        tfidfs.append(similarity)

        # dice_similarity
        dice = dice_similarity(set(result[0]), set(result[1]))
        tfidfs.append(dice)

        
        return render_template("hasil.html", tag='hasil', data = isi, winnow=winnows, tfidf=tfidfs, teks1=text1, teks2=text2, changes=changes)  
def casefolding(teks):
    # to lower
    teks = teks.lower()
    # hapus angka
    teks = re.sub(r"\d+", "", teks)
    # hapus tanda baca
    teks = teks.translate(str.maketrans("","",string.punctuation))
    # hapus karakter kosong
    teks = teks.strip()
    return teks
def stopword_removal(teks):
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT word FROM stopwords""")
    
    data = cursor.fetchall()
    data = [item[0] for item in data]
    cursor.close()

    tokens = set(teks.split())
    removed = []
    for word in tokens:
        if( word in data):
            teks = teks.replace(word, '')
            removed.append(word)
    return teks.strip()
def stemming(teks):
    Fact = StemmerFactory()
    stemmer = Fact.create_stemmer()
    out =  stemmer.stem(teks)
    return out

def synonym(teks1, teks2):
    teks1 = teks1.split()
    teks2 = teks2.split()
    a = len(teks1)
    b = len(teks2)
    leap = a
    if(b < a):
        leap = b
    cursor = mysql.connection.cursor()
    for i in range(leap):
        if(teks1[i] != teks2[i]):
            cursor.execute("""SELECT count(*) FROM kamus_sinonim WHERE (kata =%s && sinonim = %s) or (sinonim =%s && kata = %s) """, (teks1[i], teks2[i], teks1[i], teks2[i]))
            result = cursor.fetchone()
            if(result[0] >= 1):
                teks2[i] = teks1[i]
    cursor.close()
    temp = lambda x : (str(i) for i in x)
    teks1 = ' '.join(temp(teks1))
    teks2 = ' '.join(temp(teks2))
    return teks1, teks2



def jaccard_similarity(A, B):
    nominator = A.intersection(B)
    denominator = A.union(B)
    similarity = len(nominator)/len(denominator)
    similarity = round(similarity, 2)*100
    
    return str(similarity)+"%"
def cosine(data):
    similarity = cosine_similarity(data)
    percentage = similarity[0][1] * 100
    percentage = round(similarity[0][1], 2) * 100

    return str(percentage)+"%"
def dice_similarity(A, B):
    nominator = A.intersection(B)
    denominator = A.union(B)
    similarity = 2. * len(nominator)/(len(A)+len(B))
    similarity = round(similarity, 2)*100
    
    return str(similarity)+"%"
    
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
        synonym = 0
        if 'stemming' in request.form:
            stemming = 1
        if 'stopword' in request.form:
            stopword = 1
        if 'synonym' in request.form:
            synonym = 1
        # stemming = request.form['stemming']
        # stopword = request.form['stopword']
        kgram = request.form['kgram']
        _hash = request.form['hash']
        windows = request.form['windows']

        cursor = mysql.connection.cursor()
        cursor.execute("""UPDATE settings SET k_gram=%s, hash=%s, windows=%s, is_stemming=%s, is_stopword=%s, is_sinonim=%s WHERE id=1""", (kgram,_hash,windows,stemming,stopword,synonym,))        
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('setting'))
def checklogin():
    if 'username' not in session:
        return redirect(url_for('login'))    
@app.route("/ajaxsinonim",methods=["POST","GET"])
def ajaxsinonim():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        draw = request.form['draw'] 
        row = int(request.form['start'])
        rowperpage = int(request.form['length'])
        searchValue = request.form["search[value]"]
        print(draw)
        print(row)
        print(rowperpage)
        print(searchValue)

        ## Total number of records without filtering
        cursor.execute("select count(*) as allcount from kamus_sinonim")
        rsallcount = cursor.fetchone()
        totalRecords = rsallcount[0]
        print(totalRecords) 

        ## Total number of records with filtering
        likeString = "%" + searchValue +"%"
        cursor.execute("SELECT count(*) as allcount from kamus_sinonim WHERE kata LIKE %s OR sinonim LIKE %s", (likeString, likeString,))
        rsallcount = cursor.fetchone()
        totalRecordwithFilter = rsallcount[0]
        print(totalRecordwithFilter) 

        ## Fetch records
        if searchValue=='':
            cursor.execute("SELECT * FROM kamus_sinonim ORDER BY kata asc limit %s, %s;", (row, rowperpage))
            employeelist = cursor.fetchall()
        else:        
            cursor.execute("SELECT * FROM kamus_sinonim WHERE kata LIKE %s OR sinonim LIKE %s  limit %s, %s;", (likeString, likeString, row, rowperpage,))
            employeelist = cursor.fetchall()

        data = []
        for row in employeelist:
            data.append({
                'kata': row[1],
                'sinonim': row[2],
                'aksi': '<a href="" data-id="'+str(row[0])+'" data-kata="'+row[1]+'" data-sinonim="'+row[2]+'" class="btn-edit" ><i class="fa fa-edit text-success mr-2" ></i></a><a href="" data-id="'+str(row[0])+'" data-kata="'+row[1]+'" data-sinonim="'+row[2]+'" class="btn-delete"><i class="fa fa-trash text-danger"></i></a>',
                
            })

        response = {
            'draw': draw,
            'iTotalRecords': totalRecords,
            'iTotalDisplayRecords': totalRecordwithFilter,
            'aaData': data,
        }
        return jsonify(response)

@app.route("/ajaxkatadasar",methods=["POST","GET"])
def ajaxkatadasar():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        draw = request.form['draw'] 
        row = int(request.form['start'])
        rowperpage = int(request.form['length'])
        searchValue = request.form["search[value]"]
        print(draw)
        print(row)
        print(rowperpage)
        print(searchValue)

        ## Total number of records without filtering
        cursor.execute("select count(*) as allcount from kamus_sinonim")
        rsallcount = cursor.fetchone()
        totalRecords = rsallcount[0]
        print(totalRecords) 

        ## Total number of records with filtering
        likeString = "%" + searchValue +"%"
        cursor.execute("SELECT count(*) as allcount from kata_dasar WHERE kata LIKE %s", (likeString,))
        rsallcount = cursor.fetchone()
        totalRecordwithFilter = rsallcount[0]
        print(totalRecordwithFilter) 

        ## Fetch records
        if searchValue=='':
            cursor.execute("SELECT * FROM kata_dasar ORDER BY kata asc limit %s, %s;", (row, rowperpage))
            employeelist = cursor.fetchall()
        else:        
            cursor.execute("SELECT * FROM kata_dasar WHERE kata LIKE %s  limit %s, %s;", (likeString, row, rowperpage,))
            employeelist = cursor.fetchall()

        data = []
        for row in employeelist:
            data.append({
                'kata': row[1],
                'aksi': '<a href="" data-id="'+str(row[0])+'" data-kata="'+row[1]+'" class="btn-edit" ><i class="fa fa-edit text-success mr-2" ></i></a><a href="" data-id="'+str(row[0])+'" data-kata="'+row[1]+'" class="btn-delete"><i class="fa fa-trash text-danger"></i></a>',
                
            })

        response = {
            'draw': draw,
            'iTotalRecords': totalRecords,
            'iTotalDisplayRecords': totalRecordwithFilter,
            'aaData': data,
        }
        return jsonify(response)

        

if __name__ == '__main__':
    app.run(debug=True)
