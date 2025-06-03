from flask import Flask , render_template , request
import mysql.connector
import re




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

#アカウント新規作成処理
@app.route('/registerDB', methods=['POST'])
def registerDB():
    con = conn_db()
    cur = con.cursor()

    #ID作成
    cur.execute("SELECT MAX(accountId) FROM t_account")
    max_id = cur.fetchone()[0]
    if max_id:
        accountId = f"{int(max_id) + 1:05}"
    else:
        accountId = "00001"
        

    #入力画面から値の受け取り
    username = request.form.get('username')
    emailAddress = request.form.get('emailAddress')
    password = request.form.get('password')
    confirmPassword = request.form.get('confirmPassword')
    gender = request.form.get('gender')
    gradeSetting = request.form.get('gradeSetting')


    errors = {}
    
    
    # メールアドレスの重複チェック
    cur.execute("SELECT accountId FROM t_account WHERE emailAddress = %s", (emailAddress,))
    if cur.fetchone():
        errors["emailAddress"] = "メールアドレスは既に使われています。"

    # パスワードのバリデーション
    password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d).{8,}$"
    if not re.match(password_pattern, password):
        errors["password"] = "パスワードは半角英数字を含む8文字以上で構成してください。"
    elif password != confirmPassword:
        errors["confirmPassword"] = "パスワードが一致しません。"


    # エラーがある場合はテンプレート再表示
    if errors:
        return render_template('register.html', errors=errors)
    
    
    # データの挿入
    sql = """
        INSERT INTO t_account (
            accountId,
            username,
            emailAddress,
            password,
            gender,
            gradeSetting,
            coin,
            totalExperience,
            playerImage
        ) VALUES (
            %(accountId)s,
            %(username)s,
            %(emailAddress)s,
            %(password)s,
            %(gender)s,
            %(gradeSetting)s,
            %(coin)s,
            %(totalExperience)s,
            %(playerImage)s
        )
    """
    data = {
        'accountId': accountId,
        'username': username,
        'emailAddress': emailAddress,
        'password': password,
        'gender': gender,
        'gradeSetting': gradeSetting,
        'coin': 0,
        'totalExperience': 0,
        'playerImage': None
    }
    
    cur.execute(sql, data)
    
    
    con.commit()
    con.close()
    cur.close()
    
    # ログインページへリダイレクト
    return render_template("login.html")



# ログインページ
@app.route('/login')
def login():
    return render_template("login.html")



# 設定画面
@app.route('/config')
def config():
    return render_template("config.html")



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
    app.run(debug=True)