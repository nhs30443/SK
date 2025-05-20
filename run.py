from flask import Flask , render_template , request
import mysql.connector



app = Flask(__name__)

# db接続用関数
def conn_db():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="ngr256256",
        db="2024py23db",
        charset="utf8"
    )
    return conn



############################################################################
### パスの定義
############################################################################

# TOP画面
@app.route('/')
def index():
    return render_template("top.html")


























#実行制御
if __name__ ==  "__main__":
    app.run(debug=True, port=2000)