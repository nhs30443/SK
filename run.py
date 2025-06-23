from flask import Flask, render_template, request, session, json, redirect, url_for
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
    
    return redirect(url_for("index"))



# 新規登録ページ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
        
        # 登録完了ページへリダイレクト
        return redirect(url_for("register_complete"))
    
    return render_template("register.html")

#アカウント新規作成完了画面
@app.route('/register_complete')
def register_complete():
    
    return render_template("register_complete.html")



# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
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
        
        return redirect(url_for("main"))
        
    return render_template("login.html")
    


# メインページ
@app.route('/main')
def main():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
    
    return render_template("main.html")



#バッグ内
@app.route('/in_bag')
def in_bag():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
    
    return render_template("in_bag.html")



# 設定画面
@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        con = conn_db()
        cur = con.cursor()
        
        
        #入力画面から値の受け取り
        username = request.form.get('username')
        gender = request.form.get('gender')
        gradeSetting = request.form.get('gradeSetting')
        userId = session.get("login_id")


        errors = {}


        # エラーがある場合はテンプレート再表示
        if errors:
            return render_template('register.html', errors=errors)
        
        
        # データの更新
        cur.execute('''
            UPDATE t_account
            SET username = %s, gender = %s, gradeSetting = %s
            WHERE accountId = %s
        ''', (username, gender, gradeSetting, userId))

        
        
        con.commit()
        con.close()
        cur.close()
        
        # メインへリダイレクト
        return redirect(url_for("main"))
        
        
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
    
    
    con = conn_db()
    cur = con.cursor()
    
    cur.execute('''
        SELECT accountId, username, gender, gradeSetting
        FROM t_account
        WHERE accountId = %s
    ''', (userId,))
    
    user = cur.fetchone()
    
    cur.close()
    con.close()
    
    return render_template("config.html", user=user)



#武器詳細
@app.route('/weapon-detail')
def weapon_detail():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
        
    return render_template("weapon-detail.html")


# アイテム詳細
@app.route('/item-detail')
def item_detail():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))

    return render_template("item-detail.html")


# 問題画面
@app.route('/question')
def question():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
    
    return render_template("question.html")



# マップ画面
@app.route('/map')
def map():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
    
    return render_template("map.html")



# 科目選択画面
@app.route('/subject')
def subject():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))
    
    return render_template("subject.html")



@app.route('/result')
def result():
    # セッション確認
    userId = session.get("login_id")
    if userId is None:
        return redirect(url_for("login"))

    # 成績データ（例）※総合は含めない
    subjects = [
        {'name': '漢字', 'score': 80.0},
        {'name': '英語', 'score': 80.0},
        {'name': '算数', 'score': 85.0},
    ]

    # 総合正解率（平均）を計算
    total_score = sum(s['score'] for s in subjects) / len(subjects)

    # subjects に総合スコアを追加
    subjects.append({'name': '総合', 'score': round(total_score, 1)})

    # 総合スコアを取得
    total_score = next((s['score'] for s in subjects if s['name'] == '総合'), None)

    # ランク計算関数
    def calculate_rank(score):
        if score is None:
            return 'E'  # 総合が無い場合は最低ランク
        elif score >= 95:
            return 'S'
        elif score >= 85:
            return 'A'
        elif score >= 75:
            return 'B'
        elif score >= 65:
            return 'C'
        elif score >= 55:
            return 'D'
        else:
            return 'E'

    def get_rank_color(rank):
        return {
            'S': 'gold',
            'A': 'red',
            'B': 'blue',
            'C': 'yellow',
            'D': 'green',
            'E': 'gray'
        }.get(rank, 'black')

    rank = calculate_rank(total_score)
    rank_color = get_rank_color(rank)

    results_data = {
        'subjects': subjects,
        'rank': rank,
        'rank_color': rank_color,
        'experience': 125000,
        'coins': 800
    }

    return render_template("result.html", data=results_data)















# デバッグ用
@app.route('/test')
def test():
    
    return render_template("xxx.html")





#実行制御
if __name__ ==  "__main__":
    app.run(debug=True)
