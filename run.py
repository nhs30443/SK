from flask import Flask, render_template, request, session, json, redirect, url_for, jsonify
import mysql.connector
import re
from functools import wraps
import google.generativeai as genai
import json
import random

app = Flask(__name__)
app.secret_key = "qawsedrftgyhujikolp"

# Gemini API設定
GEMINI_API_KEY = "AIzaSyBI4JzjwaPUV38U6DxbcUi5J5BKdN-cS3o"
genai.configure(api_key=GEMINI_API_KEY)


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


# ログイン確認
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "login_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


# 問題生成関数
def generate_question(subject, grade="小学3年生"):
    """
    Gemini APIを使って科目別の4択問題を生成
    """
    subject_prompts = {
        'math': f"""
{grade}レベルの算数の問題を1問作成してください。
計算問題、文章問題、図形問題などバラエティに富んだ内容にしてください。
難易度は{grade}に適したレベルにしてください。
""",
        'kanji': f"""
{grade}レベルの漢字の問題を1問作成してください。
漢字の読み方、書き方、意味、熟語などの問題にしてください。
{grade}で習う漢字を中心に出題してください。
""",
        'english': f"""
{grade}レベルの英語の問題を1問作成してください。
英単語、簡単な英文、アルファベットなど{grade}に適したレベルの問題にしてください。
"""
    }

    base_prompt = f"""
以下の条件で問題を作成してください：

1. {subject_prompts.get(subject, '一般的な')}
2. 4択の選択肢を作成してください
3. 正解は1つだけにしてください
4. 間違いの選択肢も自然で紛らわしいものにしてください
5. 小学生にも分かりやすい文章にしてください

以下のJSON形式で回答してください：
{{
    "question": "問題文",
    "choices": [
        "選択肢1",
        "選択肢2", 
        "選択肢3",
        "選択肢4"
    ],
    "correct_answer": 0,
    "explanation": "解説"
}}

correct_answerは正解の選択肢のインデックス（0-3）を指定してください。
"""

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(base_prompt)

        response_text = response.text

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        question_data = json.loads(response_text.strip())

        if not all(key in question_data for key in ['question', 'choices', 'correct_answer', 'explanation']):
            raise ValueError("必要なキーが不足しています")

        if len(question_data['choices']) != 4:
            raise ValueError("選択肢は4つである必要があります")

        if not (0 <= question_data['correct_answer'] <= 3):
            raise ValueError("correct_answerは0-3の範囲である必要があります")

        return question_data

    except Exception as e:
        print(f"問題生成エラー: {e}")
        return get_fallback_question(subject)


def get_fallback_question(subject):
    """API失敗時のフォールバック問題"""
    fallback_questions = {
        'math': {
            "question": "5 + 3 = ?",
            "choices": ["6", "7", "8", "9"],
            "correct_answer": 2,
            "explanation": "5に3を足すと8になります。"
        },
        'kanji': {
            "question": "「やま」を漢字で書くとどれですか？",
            "choices": ["川", "山", "海", "空"],
            "correct_answer": 1,
            "explanation": "「やま」は「山」と書きます。"
        },
        'english': {
            "question": "「りんご」を英語で言うとどれですか？",
            "choices": ["orange", "apple", "banana", "grape"],
            "correct_answer": 1,
            "explanation": "「りんご」は英語で「apple」です。"
        }
    }

    return fallback_questions.get(subject, fallback_questions['math'])


############################################################################
### パスの定義
############################################################################

# トップページ
@app.route('/')
def index():
    return render_template("top.html")


# ログアウト
@app.route('/logout')
def clear():
    session.clear()
    return redirect(url_for("index"))


# 新規登録ページ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        con = conn_db()
        cur = con.cursor()

        # ID作成
        cur.execute("SELECT MAX(accountId) FROM t_account")
        max_id = cur.fetchone()[0]
        if max_id:
            accountId = f"{int(max_id) + 1:05}"
        else:
            accountId = "00001"

        # 入力画面から値の受け取り
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
              INSERT INTO t_account (accountId, \
                                     username, \
                                     emailAddress, \
                                     password, \
                                     gender, \
                                     gradeSetting, \
                                     coin, \
                                     totalExperience, \
                                     playerImage) \
              VALUES (%(accountId)s, \
                      %(username)s, \
                      %(emailAddress)s, \
                      %(password)s, \
                      %(gender)s, \
                      %(gradeSetting)s, \
                      %(coin)s, \
                      %(totalExperience)s, \
                      %(playerImage)s) \
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

        return redirect(url_for("register_complete"))

    return render_template("register.html")


# アカウント新規作成完了画面
@app.route('/register_complete')
def register_complete():
    return render_template("register_complete.html")


# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ary = []
        emailAddress = request.form.get('emailAddress')
        password = request.form.get('password')

        con = conn_db()
        cur = con.cursor()
        sql = "select accountId from t_account where emailAddress = %s and password = %s"
        cur.execute(sql, [emailAddress, password])
        rows = cur.fetchall()
        for row in rows:
            ary.append(row)
            session["login_id"] = row[0]

        session["aryData"] = json.dumps(ary)
        cur.close()
        con.close()

        if not ary:
            errors = {}
            errors["login"] = "メールアドレスとパスワードが一致しません。"
            return render_template("login.html", errors=errors)

        return redirect(url_for("main"))

    return render_template("login.html")


# メインページ
@app.route('/main')
@login_required
def main():
    con = conn_db()
    cur = con.cursor()

    accountId = session.get("login_id")
    sql = " SELECT COIN FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()

    coin = result[0] if result else 0
    cur.close()
    con.close()

    return render_template("main.html", coin=coin)


# ショップ
@app.route('/shop')
@login_required
def shop():
    con = conn_db()
    cur = con.cursor()

    accountId = session.get("login_id")
    sql = " SELECT COIN FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()

    coin = result[0] if result else 0
    cur.close()
    con.close()
    return render_template("shop.html", coin=coin)


# ショップアイテム購入
@app.route('/buy-shop', methods=["POST"])
@login_required
def buy_shop():
    con = conn_db()
    cur = con.cursor()

    potion_low = request.form.get('potion_low')
    potion_mid = request.form.get('potion_mid')
    potion_high = request.form.get('potion_high')
    buf_jp = request.form.get('buf_jp')
    buf_mt = request.form.get('buf_mt')
    buf_en = request.form.get('buf_en')

    accountId = session.get("login_id")
    sql = " SELECT COIN FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()

    coin = result[0] if result else 0
    cur.close()
    con.close()
    return render_template("shop.html", coin=coin)


# バッグ内
@app.route('/in_bag')
@login_required
def in_bag():
    con = conn_db()
    cur = con.cursor()

    accountId = session.get("login_id")
    sql = " SELECT COIN FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()

    coin = result[0] if result else 0
    cur.close()
    con.close()
    return render_template("in_bag.html", coin=coin)


# 設定画面
@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'POST':
        con = conn_db()
        cur = con.cursor()

        username = request.form.get('username')
        gender = request.form.get('gender')
        gradeSetting = request.form.get('gradeSetting')
        userId = session.get("login_id")

        errors = {}

        if errors:
            return render_template('register.html', errors=errors)

        cur.execute('''
                    UPDATE t_account
                    SET username     = %s,
                        gender       = %s,
                        gradeSetting = %s
                    WHERE accountId = %s
                    ''', (username, gender, gradeSetting, userId))

        con.commit()
        con.close()
        cur.close()

        return redirect(url_for("main"))

    con = conn_db()
    cur = con.cursor()

    userId = session.get("login_id")

    cur.execute('''
                SELECT accountId, username, gender, gradeSetting
                FROM t_account
                WHERE accountId = %s
                ''', (userId,))

    user = cur.fetchone()

    cur.close()
    con.close()

    return render_template("config.html", user=user)


# 武器詳細
@app.route('/weapon-detail')
@login_required
def weapon_detail():
    con = conn_db()
    cur = con.cursor()

    accountId = session.get("login_id")
    sql = " SELECT COIN FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()

    coin = result[0] if result else 0
    cur.close()
    con.close()
    return render_template("weapon-detail.html", coin=coin)


# アイテム詳細
@app.route('/item-detail')
@login_required
def item_detail():
    con = conn_db()
    cur = con.cursor()

    accountId = session.get("login_id")
    sql = " SELECT COIN FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()

    coin = result[0] if result else 0
    cur.close()
    con.close()
    return render_template("item-detail.html", coin=coin)


# 問題画面（従来）
@app.route('/question')
@login_required
def question():
    return render_template("question.html")


# 科目指定付きの問題画面（新規）
@app.route('/question/<subject>')
@login_required
def question_with_subject(subject):
    """科目指定付きの問題画面"""
    return render_template("question.html", subject=subject)


# 問題生成API（新規）
@app.route('/api/generate-question/<subject>')
@login_required
def api_generate_question(subject):
    """問題生成API"""
    try:
        con = conn_db()
        cur = con.cursor()

        accountId = session.get("login_id")
        cur.execute("SELECT gradeSetting FROM t_account WHERE accountId = %s", (accountId,))
        result = cur.fetchone()

        grade_setting = result[0] if result else "3"
        grade = f"小学{grade_setting}年生"

        cur.close()
        con.close()

        question_data = generate_question(subject, grade)
        return jsonify(question_data)

    except Exception as e:
        print(f"API エラー: {e}")
        return jsonify(get_fallback_question(subject)), 500


# 回答チェックAPI（新規）
@app.route('/api/check-answer', methods=['POST'])
@login_required
def api_check_answer():
    """回答チェックAPI"""
    try:
        data = request.get_json()
        selected_answer = data.get('selected_answer')
        correct_answer = data.get('correct_answer')

        is_correct = selected_answer == correct_answer

        # 正解時の処理（経験値やコイン追加など）
        if is_correct:
            # ここで経験値やコインを追加する処理を実装
            pass

        return jsonify({
            'is_correct': is_correct,
            'message': '正解です！' if is_correct else '不正解です。'
        })

    except Exception as e:
        print(f"回答チェックエラー: {e}")
        return jsonify({'error': 'エラーが発生しました'}), 500


# マップ画面
@app.route('/map')
@login_required
def map():
    return render_template("map.html")


# 科目選択画面
@app.route('/subject')
@login_required
def subject():
    return render_template("subject.html")


# リザルト画面
@app.route('/result')
@login_required
def result():
    subjects = [
        {'name': '漢字', 'score': 80.0},
        {'name': '英語', 'score': 80.0},
        {'name': '算数', 'score': 85.0},
    ]

    total_score = sum(s['score'] for s in subjects) / len(subjects)
    subjects.append({'name': '総合', 'score': round(total_score, 1)})
    total_score = next((s['score'] for s in subjects if s['name'] == '総合'), None)

    def calculate_rank(score):
        if score is None:
            return 'E'
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


# 実行制御
if __name__ == "__main__":
    app.run(debug=True)