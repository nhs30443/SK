from flask import Flask , render_template , request
import mysql.connector



app = Flask(__name__)

# db接続用関数
def conn_db():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="root",
        db="cqDB",
        charset="utf8"
    )
    return conn



############################################################################
### パスの定義
############################################################################

# トップページ
@app.route('/')
def index():
    return render_template("top.html")


# 新規登録ページ
@app.route('/register')
def register():
    return render_template("register.html")


# ログインページ
@app.route('/login')
def login():
    return render_template("login.html")


# メインページ
@app.route('/main')
def main():
    return render_template("main.html")


# 問題画面
@app.route('/question')
def question():
    return render_template("question.html")


























#実行制御
if __name__ ==  "__main__":
    app.run(debug=True, port=2000)