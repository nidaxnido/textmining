from flask import Flask, render_template, request,redirect, url_for, session
from distutils.log import debug
from fileinput import filename
from PyPDF2 import PdfReader
from flask_mysqldb import MySQL
 
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
    return render_template('user.html',tag='user', data=data)
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
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('stopwords.html',tag='stopwords')
@app.route('/kata-dasar/')
def katadasar():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('katadasar.html',tag='katadasar')
@app.route('/proses-deteksi/')
def deteksi():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('deteksi.html',tag='deteksi')
# @app.route('/hasil-deteksi/')
# def hasil():
#     return render_template('hasil.html',tag='hasil')
@app.route('/settings/')
def setting():
    if 'username' not in session:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM settings """)
    setting = cursor.fetchone()
    cursor.close()
    return render_template('setting.html',tag='setting', data=setting)
@app.route('/hasil-deteksi', methods = ['POST'])  
def hasil():  
    if request.method == 'POST':  
        files = request.files.getlist('file[]')
        # f.save(f.filename)
        isi = [];
        for x in files:
            reader = PdfReader(x)
            page = reader.pages[0]
            text = page.extract_text()    
            temp = { "filename" : x.filename, "text" : text}
            isi.append(temp)
        
        return render_template("hasil.html", tag='hasil', data = isi)  
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
if __name__ == '__main__':
    app.run(debug=True)
