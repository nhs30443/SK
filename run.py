from flask import Flask, render_template, request, session, json
import mysql.connector
import re




app = Flask(__name__)
app.secret_key = "qawsedrftgyhujikolp"


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

# セッションクリア
@app.route('/clear')
def clear():
    session.clear()
    
    return render_template("login.html")



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
    
    # 登録完了ページへへリダイレクト
    return render_template("register_complete.html")



# ログインページ
@app.route('/login')
def login():
    return render_template("login.html")

# ログイン認証
@app.route('/login_check', methods = ['POST'])
def login_check():
    ary = []
    #login_form.htmlから渡された情報を格納
    emailAddress = request.form.get('emailAddress')
    password = request.form.get('password')

    con = conn_db()
    cur = con.cursor()
    sql = "select accountId from t_account where emailAddress = %s and password = %s"
    cur.execute(sql,[emailAddress , password])
    rows = cur.fetchall()
    for row in rows:
        ary.append(row)
        session["login_id"] = row[0]

    # aryDataをセッションに保存
    session["aryData"] = json.dumps(ary)  # リストをJSON形式で保存
    
    cur.close()
    con.close()
    
    
    if not ary :
        errors = {}
        errors["login"] = "メールアドレスとパスワードが一致しません。"
        return render_template("login.html", errors=errors)
    
    return render_template("main.html", aryData=ary)



# メインページ
@app.route('/main')
def main():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return render_template('login.html')
    
    return render_template("main.html")

#バッグ内
@app.route('/in_bag')
def in_bag():
    if userId is None:
        return render_template('login.html')
    
    return render_template("in_bag.html")


# 設定画面
@app.route('/config')
def config():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return render_template('login.html')
    
    return render_template("config.html")



#武器詳細
@app.route('/weapon-detail')
def weapon_detail():
    userId = session.get("login_id")
    if userId is None:
        return render_template('login.html')
        
    return render_template("weapon-detail.html")

# 問題画面
@app.route('/question')
def question():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return render_template('login.html')
    
    return render_template("question.html")



# マップ画面
@app.route('/map')
def map():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return render_template('login.html')
    
    return render_template("map.html")



# 科目選択画面
@app.route('/subject')
def subject():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return render_template('login.html')
    
    return render_template("subject.html")


# 設定画面
@app.route('/result')  # または既存のルート名
def result():
    # 既存のロジックがあればそのまま使用
    results_data = {
        'subjects': [
            {'name': '漢字', 'score': 10.0},
            {'name': '英語', 'score': 10.0},
            {'name': '算数', 'score': 10.0}
        ],
        'rank': 'A',
        'experience': 100000,
        'coins': 800
    }

    # 重要：dataパラメータを必ず渡す
    return render_template("result.html", data=results_data)













# デバッグ用
@app.route('/test')
def test():
    
    return render_template("xxx.html")





#実行制御
if __name__ ==  "__main__":
    app.run(debug=True)
