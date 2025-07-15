from flask import Flask, render_template, request, session, json, redirect, url_for, jsonify
import mysql.connector
import re
from functools import wraps
import google.generativeai as genai
import json
import random
import time
import hashlib

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


# 問題生成統計を追跡するクラス
class QuestionGenerationStats:
    def __init__(self):
        self.stats = {
            'total_generated': 0,
            'successful_generations': 0,
            'fallback_used': 0,
            'subjects': {'math': 0, 'kanji': 0, 'english': 0},
            'grades': {}
        }

    def record_generation(self, subject, grade, success=True, fallback=False):
        self.stats['total_generated'] += 1
        if success:
            self.stats['successful_generations'] += 1
        if fallback:
            self.stats['fallback_used'] += 1

        self.stats['subjects'][subject] = self.stats['subjects'].get(subject, 0) + 1
        self.stats['grades'][grade] = self.stats['grades'].get(grade, 0) + 1

    def get_success_rate(self):
        if self.stats['total_generated'] == 0:
            return 0
        return (self.stats['successful_generations'] / self.stats['total_generated']) * 100


# グローバル統計インスタンス
generation_stats = QuestionGenerationStats()


# 高度な問題生成関数
def generate_question(subject, grade="小学6年生"):
    """
    高度な自動問題生成システム
    """
    # ランダム要素の強化
    random_seed = int(time.time() * 1000000) % 1000000
    random.seed(random_seed)

    # 学年に応じた難易度設定
    grade_levels = {
        "1": "とても簡単で基礎的な",
        "2": "簡単で身近な",
        "3": "普通の",
        "4": "少し考える必要がある",
        "5": "難しめの",
        "6": "高度な"
    }

    grade_num = grade.replace("小学", "").replace("年生", "")
    difficulty_desc = grade_levels.get(grade_num, "普通の")

    # 科目別の詳細なパターン
    subject_details = {
        'math': {
            'patterns': [
                f"{random.randint(1, 20)} + {random.randint(1, 20)} のような足し算",
                f"{random.randint(10, 50)} - {random.randint(1, 20)} のような引き算",
                f"{random.randint(2, 9)} × {random.randint(2, 9)} のような掛け算",
                f"{random.randint(2, 9) * random.randint(2, 9)} ÷ {random.randint(2, 9)} のような割り算",
                f"りんご{random.randint(3, 15)}個とみかん{random.randint(2, 10)}個の文章問題",
                f"{random.randint(100, 500)}円の買い物の計算問題",
                f"{random.randint(1, 12)}時{random.randint(10, 50)}分の時間計算",
                f"{random.randint(10, 100)}cmを{random.choice(['m', 'mm'])}に変換する問題"
            ],
            'focus': "計算力と数的思考力"
        },
        'kanji': {
            'patterns': [
                f"「{random.choice(['やま', 'かわ', 'うみ', 'そら', 'はな', 'き', 'みず', 'ひ'])}」の漢字の読み書き",
                f"「{random.choice(['がっこう', 'せんせい', 'ともだち', 'かぞく', 'いえ'])}」の漢字の読み書き",
                f"「{random.choice(['あかい', 'おおきい', 'ちいさい', 'たかい', 'ひくい'])}」の漢字変換",
                f"「{random.choice(['はしる', 'およぐ', 'とぶ', 'あるく', 'たつ'])}」の動詞の漢字",
                f"反対の意味を持つ漢字の組み合わせ",
                f"同じ部首を持つ漢字のグループ",
                f"日常生活でよく使う漢字の意味"
            ],
            'focus': "漢字の読み書きと意味理解"
        },
        'english': {
            'patterns': [
                f"「{random.choice(['りんご', 'みかん', 'バナナ', 'ぶどう'])}」などの果物の英単語",
                f"「{random.choice(['いぬ', 'ねこ', 'うさぎ', 'とり'])}」などの動物の英単語",
                f"「{random.choice(['あか', 'あお', 'きいろ', 'みどり'])}」などの色の英単語",
                f"「{random.choice(['おはよう', 'こんにちは', 'ありがとう', 'さようなら'])}」などの挨拶の英語",
                f"「{random.choice(['がっこう', 'いえ', 'こうえん', 'びょういん'])}」などの場所の英単語",
                f"1から{random.randint(10, 20)}までの数字の英語",
                f"「{random.choice(['げつようび', 'かようび', 'すいようび'])}」などの曜日の英語"
            ],
            'focus': "基本英単語と発音"
        }
    }

    # ランダムパターン選択
    selected_pattern = random.choice(subject_details[subject]['patterns'])
    focus_area = subject_details[subject]['focus']

    # 時間ベースのユニーク要素
    current_time = int(time.time())
    unique_elements = [
        random.randint(1, 100),
        random.choice(['A', 'B', 'C', 'D']),
        current_time % 1000
    ]

    # 超詳細プロンプト
    enhanced_prompt = f"""
あなたは{grade}の児童向け問題作成の専門家です。以下の詳細な指示に従って、完全にオリジナルな問題を作成してください。

【基本設定】
- 対象: {grade}の児童
- 科目: {subject}
- 難易度: {difficulty_desc}レベル
- 重点分野: {focus_area}
- 問題パターン: {selected_pattern}

【ユニーク要素】
- 問題作成ID: Q{random_seed}
- タイムスタンプ: {current_time}
- ランダム要素: {unique_elements}
- バリエーション番号: {random.randint(1000, 9999)}

【絶対遵守事項】
1. 🔄 毎回必ず異なる数値・単語・シチュエーションを使用
2. 📚 {grade}の学習指導要領に準拠した内容
3. 🎯 4択で1つだけが正解、他の3つは合理的な間違い選択肢
4. 👶 小学生が理解できる平易な言葉遣い
5. 🌟 興味を引く身近な話題を取り入れる

【特別指示】
- 数学: 答えは必ず整数になるよう調整
- 漢字: {grade}配当漢字を中心に使用
- 英語: 基本語彙500語以内で構成
- 全科目: 問題文は1文で完結させる

【創造性の要求】
この問題は今まで作成したどの問題とも異なる、完全にオリジナルな内容にしてください。
同じような計算式、同じような単語、同じようなシチュエーションは避けてください。

【出力フォーマット（必須）】
```json
{{
    "question": "問題文（50文字以内で具体的に）",
    "choices": [
        "選択肢1（簡潔で明確）",
        "選択肢2（紛らわしいが間違い）",
        "選択肢3（もっともらしい間違い）",
        "選択肢4（一般的な間違い）"
    ],
    "correct_answer": 0,
    "explanation": "{grade}児童向けの丁寧で分かりやすい解説（30文字以内）"
}}
```

今すぐ、上記の全ての条件を満たした新しい問題を1つ作成してください。
"""

    try:
        # 最高レベルの創造性設定
        generation_config = {
            "temperature": 1.2,  # 創造性最大
            "top_p": 0.9,
            "top_k": 50,
            "max_output_tokens": 1024,
        }

        model = genai.GenerativeModel(
            model_name='models/gemini-1.5-flash',
            safety_settings=[
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            ]
        )

        response = model.generate_content(
            enhanced_prompt,
            generation_config=generation_config
        )

        # partsがあるか確認してから抽出
        if response.candidates and response.candidates[0].content.parts:
            response_text = response.candidates[0].content.parts[0].text.strip()
        else:
            raise ValueError("生成結果が空、または安全フィルターでブロックされました")


        # JSON抽出の改善
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()

        # JSON解析
        question_data = json.loads(response_text)

        # 厳密な検証
        validation_errors = []

        if not question_data.get('question'):
            validation_errors.append("問題文が空です")
        if not isinstance(question_data.get('choices'), list) or len(question_data['choices']) != 4:
            validation_errors.append("選択肢は4つ必要です")
        if not isinstance(question_data.get('correct_answer'), int) or not (0 <= question_data['correct_answer'] <= 3):
            validation_errors.append("正解インデックスが無効です")
        if not question_data.get('explanation'):
            validation_errors.append("解説が空です")

        if validation_errors:
            raise ValueError(f"検証エラー: {', '.join(validation_errors)}")

        # メタデータ追加
        question_data.update({
            'generation_id': random_seed,
            'pattern': selected_pattern,
            'timestamp': current_time,
            'subject': subject,
            'grade': grade
        })

        print(f"✅ 高度な問題生成成功: {subject} - ID:{random_seed}")
        return question_data

    except Exception as e:
        print(f"❌ 高度な問題生成エラー: {e}")
        # より充実したフォールバック
        return get_smart_fallback_question(subject, grade)


def get_smart_fallback_question(subject, grade="小学6年生"):
    """
    スマートフォールバック問題システム
    """
    grade_num = int(grade.replace("小学", "").replace("年生", ""))
    current_time = int(time.time())

    # 動的フォールバック問題生成
    if subject == 'math':
        if grade_num <= 2:
            num1, num2 = random.randint(1, 10), random.randint(1, 5)
            answer = num1 + num2
            choices = [str(answer - 1), str(answer), str(answer + 1), str(answer + 2)]
            random.shuffle(choices)
            correct_idx = choices.index(str(answer))

            return {
                "question": f"{num1} + {num2} = ?",
                "choices": choices,
                "correct_answer": correct_idx,
                "explanation": f"{num1}に{num2}を足すと{answer}になります。",
                "generation_id": f"fallback_{current_time}",
                "subject": subject,
                "grade": grade
            }
        else:
            num1, num2 = random.randint(2, 12), random.randint(2, 12)
            answer = num1 * num2
            wrong_answers = [answer - 1, answer + 1, answer + num1, answer - num2]
            choices = [str(answer)] + [str(max(1, w)) for w in wrong_answers[:3]]
            random.shuffle(choices)
            correct_idx = choices.index(str(answer))

            return {
                "question": f"{num1} × {num2} = ?",
                "choices": choices,
                "correct_answer": correct_idx,
                "explanation": f"{num1}に{num2}をかけると{answer}になります。",
                "generation_id": f"fallback_{current_time}",
                "subject": subject,
                "grade": grade
            }

    elif subject == 'kanji':
        kanji_pairs = [
            ("やま", "山", ["川", "海", "空"]),
            ("みず", "水", ["火", "土", "風"]),
            ("はな", "花", ["草", "木", "葉"]),
            ("そら", "空", ["雲", "星", "月"]),
            ("いし", "石", ["土", "砂", "岩"])
        ]

        selected = random.choice(kanji_pairs)
        hiragana, correct_kanji, wrong_options = selected
        choices = [correct_kanji] + wrong_options
        random.shuffle(choices)
        correct_idx = choices.index(correct_kanji)

        return {
            "question": f"「{hiragana}」を漢字で書くとどれですか？",
            "choices": choices,
            "correct_answer": correct_idx,
            "explanation": f"「{hiragana}」は「{correct_kanji}」と書きます。",
            "generation_id": f"fallback_{current_time}",
            "subject": subject,
            "grade": grade
        }

    else:  # english
        english_pairs = [
            ("りんご", "apple", ["orange", "banana", "grape"]),
            ("いぬ", "dog", ["cat", "bird", "fish"]),
            ("あか", "red", ["blue", "green", "yellow"]),
            ("ほん", "book", ["pen", "desk", "chair"]),
            ("がっこう", "school", ["house", "park", "store"])
        ]

        selected = random.choice(english_pairs)
        japanese, correct_english, wrong_options = selected
        choices = [correct_english] + wrong_options
        random.shuffle(choices)
        correct_idx = choices.index(correct_english)

        return {
            "question": f"「{japanese}」を英語で言うとどれですか？",
            "choices": choices,
            "correct_answer": correct_idx,
            "explanation": f"「{japanese}」は英語で「{correct_english}」です。",
            "generation_id": f"fallback_{current_time}",
            "subject": subject,
            "grade": grade
        }


# 問題品質チェック関数
def validate_question_quality(question_data):
    """
    生成された問題の品質をチェック
    """
    issues = []

    question = question_data.get('question', '')
    choices = question_data.get('choices', [])

    # 基本チェック
    if len(question) < 5:
        issues.append("問題文が短すぎます")
    if len(question) > 100:
        issues.append("問題文が長すぎます")

    # 選択肢チェック
    if len(set(choices)) != 4:
        issues.append("選択肢に重複があります")

    for i, choice in enumerate(choices):
        if len(choice) < 1:
            issues.append(f"選択肢{i + 1}が空です")
        if len(choice) > 20:
            issues.append(f"選択肢{i + 1}が長すぎます")

    return issues


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


# 問題生成API（高度版）
@app.route('/api/generate-question/<subject>')
@login_required
def api_generate_question(subject):
    """
    高度な自動問題生成API
    """
    try:
        # データベース接続
        con = conn_db()
        cur = con.cursor()

        accountId = session.get("login_id")
        cur.execute("SELECT gradeSetting FROM t_account WHERE accountId = %s", (accountId,))
        result = cur.fetchone()

        grade_setting = result[0] if result else "3"
        grade = f"小学{grade_setting}年生"

        cur.close()
        con.close()

        # リクエスト情報の取得
        retry_count = request.args.get('retry', '0')
        timestamp = request.args.get('t', str(int(time.time())))

        print(f"🎯 問題生成開始: 科目={subject}, 学年={grade}, 再試行={retry_count}, 時刻={timestamp}")

        # 問題生成実行
        question_data = generate_question(subject, grade)

        # 成功ログ
        question_preview = question_data.get('question', '')[:30] + "..." if len(
            question_data.get('question', '')) > 30 else question_data.get('question', '')
        print(f"✅ 問題生成完了: [{question_data.get('generation_id', 'unknown')}] {question_preview}")

        # 追加のメタデータ
        question_data['api_timestamp'] = timestamp
        question_data['retry_count'] = retry_count

        return jsonify(question_data)

    except Exception as e:
        print(f"❌ API致命的エラー: {str(e)}")

        # 緊急フォールバック
        emergency_fallback = get_smart_fallback_question(subject,
                                                         f"小学{grade_setting if 'grade_setting' in locals() else '3'}年生")

        return jsonify({
            "error": "問題生成中にエラーが発生しました",
            "fallback_used": True,
            **emergency_fallback
        }), 200  # エラーでも200で返してフロントエンドで処理継続


# 回答チェックAPI
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


# デバッグ用エンドポイント（開発時のみ使用）
@app.route('/api/debug/question-stats')
@login_required
def debug_question_stats():
    """
    問題生成の統計情報を表示（デバッグ用）
    """
    return jsonify({
        'stats': generation_stats.stats,
        'success_rate': f"{generation_stats.get_success_rate():.2f}%"
    })


# 手動問題リフレッシュエンドポイント
@app.route('/api/refresh-question/<subject>')
@login_required
def refresh_question(subject):
    """
    強制的に新しい問題を生成
    """
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

        print(f"🔄 手動リフレッシュ: {subject} - {grade}")

        # 強制的に新しい問題を生成（複数回試行）
        for attempt in range(3):
            try:
                question_data = generate_question(subject, grade)

                # 品質チェック
                quality_issues = validate_question_quality(question_data)
                if not quality_issues:
                    generation_stats.record_generation(subject, grade, success=True)
                    return jsonify(question_data)
                else:
                    print(f"⚠️ 品質問題あり (試行{attempt + 1}): {quality_issues}")

            except Exception as e:
                print(f"❌ 生成試行{attempt + 1}失敗: {e}")

        # すべて失敗した場合はフォールバック
        print("🔄 フォールバックを使用")
        fallback_question = get_smart_fallback_question(subject, grade)
        generation_stats.record_generation(subject, grade, success=False, fallback=True)

        return jsonify(fallback_question)

    except Exception as e:
        print(f"❌ リフレッシュAPI エラー: {e}")
        return jsonify({'error': 'リフレッシュに失敗しました'}), 500


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
        {'name': '総合', 'score': 85.0}
    ]

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

    total_score = next((s['score'] for s in subjects if s['name'] == '総合'), None)
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



# gaeover
@app.route('/gameover')
def gameover():
    return render_template("gameover.html")


# デバッグ用
@app.route('/test')
def test():
    return render_template("xxx.html")


# 実行制御
if __name__ == "__main__":
    app.run(debug=True)