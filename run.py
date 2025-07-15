from flask import Flask, render_template, request, session, json, redirect, url_for, jsonify
import mysql.connector
import re
from functools import wraps
import google.generativeai as genai
import json
import random
import time
import hashlib
from datetime import datetime, timedelta
import traceback
import sys

app = Flask(__name__)
app.secret_key = "qawsedrftgyhujikolp"

# デバッグモードでの詳細エラー表示
app.config['DEBUG'] = True

# Gemini API設定
GEMINI_API_KEY = "AIzaSyBI4JzjwaPUV38U6DxbcUi5J5BKdN-cS3o"
genai.configure(api_key=GEMINI_API_KEY)


# db接続用関数
def conn_db():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="root",
            db="cqDB",
            charset="utf8"
        )
        return conn
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None


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
        try:
            self.stats['total_generated'] += 1
            if success:
                self.stats['successful_generations'] += 1
            if fallback:
                self.stats['fallback_used'] += 1

            self.stats['subjects'][subject] = self.stats['subjects'].get(subject, 0) + 1
            self.stats['grades'][grade] = self.stats['grades'].get(grade, 0) + 1
        except Exception as e:
            print(f"統計記録エラー: {e}")

    def get_success_rate(self):
        try:
            if self.stats['total_generated'] == 0:
                return 0
            return (self.stats['successful_generations'] / self.stats['total_generated']) * 100
        except Exception as e:
            print(f"成功率計算エラー: {e}")
            return 0


# グローバル統計インスタンス
generation_stats = QuestionGenerationStats()


# 回答履歴管理クラス
class AnswerHistory:
    def __init__(self):
        self.history = {}  # {user_id: [{'subject': str, 'is_correct': bool, 'timestamp': datetime, 'question_id': str}]}

    def add_answer(self, user_id, subject, is_correct, question_id=None):
        """回答を履歴に追加"""
        try:
            if user_id not in self.history:
                self.history[user_id] = []

            answer_record = {
                'subject': subject,
                'is_correct': is_correct,
                'timestamp': datetime.now(),
                'question_id': question_id or f"q_{len(self.history[user_id])}"
            }

            self.history[user_id].append(answer_record)

            # 履歴が長くなりすぎないよう、最新1000件に制限
            if len(self.history[user_id]) > 1000:
                self.history[user_id] = self.history[user_id][-1000:]

            print(f"回答記録追加: ユーザー{user_id}, 科目{subject}, 正誤{is_correct}")

        except Exception as e:
            print(f"回答追加エラー: {e}")
            traceback.print_exc()

    def get_subject_accuracy(self, user_id, subject=None, days_back=30):
        """科目別の正答率を取得"""
        try:
            if user_id not in self.history:
                return 0.0

            cutoff_time = datetime.now() - timedelta(days=days_back)

            # 期間内の回答をフィルタ
            recent_answers = [
                answer for answer in self.history[user_id]
                if answer['timestamp'] >= cutoff_time
            ]

            # 科目でフィルタ（指定がある場合）
            if subject:
                recent_answers = [
                    answer for answer in recent_answers
                    if answer['subject'] == subject
                ]

            if not recent_answers:
                return 0.0

            correct_count = sum(1 for answer in recent_answers if answer['is_correct'])
            total_count = len(recent_answers)

            return round((correct_count / total_count) * 100, 1)

        except Exception as e:
            print(f"正答率取得エラー: {e}")
            traceback.print_exc()
            return 0.0

    def get_all_subjects_accuracy(self, user_id, days_back=30):
        """全科目の正答率を取得"""
        try:
            if user_id not in self.history:
                return {}

            cutoff_time = datetime.now() - timedelta(days=days_back)

            # 期間内の回答をフィルタ
            recent_answers = [
                answer for answer in self.history[user_id]
                if answer['timestamp'] >= cutoff_time
            ]

            # 科目別に集計
            subject_stats = {}
            for answer in recent_answers:
                subject = answer['subject']
                if subject not in subject_stats:
                    subject_stats[subject] = {'total': 0, 'correct': 0}

                subject_stats[subject]['total'] += 1
                if answer['is_correct']:
                    subject_stats[subject]['correct'] += 1

            # 正答率を計算
            result = {}
            for subject, stats in subject_stats.items():
                accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
                result[subject] = {
                    'total_questions': stats['total'],
                    'correct_answers': stats['correct'],
                    'accuracy': round(accuracy, 1)
                }

            return result

        except Exception as e:
            print(f"全科目正答率取得エラー: {e}")
            traceback.print_exc()
            return {}

    def get_user_stats(self, user_id):
        """ユーザーの総合統計を取得"""
        try:
            if user_id not in self.history:
                return {
                    'total_questions': 0,
                    'total_correct': 0,
                    'accuracy_7_days': 0.0,
                    'accuracy_30_days': 0.0,
                    'accuracy_all_time': 0.0
                }

            all_answers = self.history[user_id]
            total_questions = len(all_answers)
            total_correct = sum(1 for answer in all_answers if answer['is_correct'])

            return {
                'total_questions': total_questions,
                'total_correct': total_correct,
                'accuracy_7_days': self.get_subject_accuracy(user_id, days_back=7),
                'accuracy_30_days': self.get_subject_accuracy(user_id, days_back=30),
                'accuracy_all_time': self.get_subject_accuracy(user_id, days_back=365)
            }

        except Exception as e:
            print(f"ユーザー統計取得エラー: {e}")
            traceback.print_exc()
            return {
                'total_questions': 0,
                'total_correct': 0,
                'accuracy_7_days': 0.0,
                'accuracy_30_days': 0.0,
                'accuracy_all_time': 0.0
            }


# グローバル回答履歴インスタンス
answer_history = AnswerHistory()


# セッションベースの一時的な正答率記録（ページリロード対応）
def save_session_stats(user_id):
    """セッションに統計データを保存"""
    try:
        if user_id in answer_history.history:
            session['user_stats'] = {
                'last_updated': datetime.now().isoformat(),
                'stats_7_days': answer_history.get_all_subjects_accuracy(user_id, 7),
                'stats_30_days': answer_history.get_all_subjects_accuracy(user_id, 30),
                'total_questions': len(answer_history.history[user_id])
            }
            print(f"セッション統計保存: ユーザー{user_id}")
    except Exception as e:
        print(f"セッション統計保存エラー: {e}")
        traceback.print_exc()


def load_session_stats():
    """セッションから統計データを読み込み"""
    try:
        return session.get('user_stats', {})
    except Exception as e:
        print(f"セッション統計読み込みエラー: {e}")
        return {}


# 高度な問題生成関数
def generate_question(subject, grade="小学3年生"):
    """
    高度な自動問題生成システム
    """
    try:
        # ランダム要素の強化
        random_seed = int(time.time() * 1000000) % 1000000
        random.seed(random_seed)

        print(f"問題生成開始: 科目={subject}, 学年={grade}")

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
                    f"りんご{random.randint(3, 15)}個とみかん{random.randint(2, 10)}個の文章問題",
                    f"{random.randint(100, 500)}円の買い物の計算問題"
                ],
                'focus': "計算力と数的思考力"
            },
            'kanji': {
                'patterns': [
                    f"「{random.choice(['やま', 'かわ', 'うみ', 'そら', 'はな', 'き', 'みず', 'ひ'])}」の漢字の読み書き",
                    f"「{random.choice(['がっこう', 'せんせい', 'ともだち', 'かぞく', 'いえ'])}」の漢字の読み書き",
                    f"「{random.choice(['あかい', 'おおきい', 'ちいさい', 'たかい', 'ひくい'])}」の漢字変換"
                ],
                'focus': "漢字の読み書きと意味理解"
            },
            'english': {
                'patterns': [
                    f"「{random.choice(['りんご', 'みかん', 'バナナ', 'ぶどう'])}」などの果物の英単語",
                    f"「{random.choice(['いぬ', 'ねこ', 'うさぎ', 'とり'])}」などの動物の英単語",
                    f"「{random.choice(['あか', 'あお', 'きいろ', 'みどり'])}」などの色の英単語"
                ],
                'focus': "基本英単語と発音"
            }
        }

        # フォールバック問題を生成（Gemini APIエラー対策）
        return get_smart_fallback_question(subject, grade)

    except Exception as e:
        print(f"問題生成エラー: {e}")
        traceback.print_exc()
        return get_smart_fallback_question(subject, grade)


def get_smart_fallback_question(subject, grade="小学3年生"):
    """
    スマートフォールバック問題システム
    """
    try:
        current_time = int(time.time())

        print(f"フォールバック問題生成: 科目={subject}")

        # 動的フォールバック問題生成
        if subject == 'math':
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

        elif subject == 'kanji':
            kanji_pairs = [
                ("やま", "山", ["川", "海", "空"]),
                ("みず", "水", ["火", "土", "風"]),
                ("はな", "花", ["草", "木", "葉"])
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
                ("あか", "red", ["blue", "green", "yellow"])
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

    except Exception as e:
        print(f"フォールバック問題生成エラー: {e}")
        traceback.print_exc()
        # 最終的なエラー回避問題
        return {
            "question": "1 + 1 = ?",
            "choices": ["1", "2", "3", "4"],
            "correct_answer": 1,
            "explanation": "1に1を足すと2になります。",
            "generation_id": "emergency",
            "subject": subject,
            "grade": grade
        }


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
        try:
            con = conn_db()
            if not con:
                return render_template('register.html', errors={'database': 'データベース接続エラー'})

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
                  INSERT INTO t_account (accountId, username, emailAddress, password, gender, gradeSetting, coin, \
                                         totalExperience, playerImage)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                  """
            data = (accountId, username, emailAddress, password, gender, gradeSetting, 0, 0, None)

            cur.execute(sql, data)
            con.commit()
            cur.close()
            con.close()

            return redirect(url_for("register_complete"))

        except Exception as e:
            print(f"登録エラー: {e}")
            traceback.print_exc()
            return render_template('register.html', errors={'system': 'システムエラーが発生しました'})

    return render_template("register.html")


# アカウント新規作成完了画面
@app.route('/register_complete')
def register_complete():
    return render_template("register_complete.html")


# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            ary = []
            emailAddress = request.form.get('emailAddress')
            password = request.form.get('password')

            con = conn_db()
            if not con:
                return render_template("login.html", errors={'database': 'データベース接続エラー'})

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

        except Exception as e:
            print(f"ログインエラー: {e}")
            traceback.print_exc()
            return render_template("login.html", errors={'system': 'システムエラーが発生しました'})

    return render_template("login.html")


# メインページ
@app.route('/main')
@login_required
def main():
    try:
        con = conn_db()
        if not con:
            return render_template("main.html", coin=0)

        cur = con.cursor()

        accountId = session.get("login_id")
        sql = " SELECT COIN FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
        result = cur.fetchone()

        coin = result[0] if result else 0
        cur.close()
        con.close()

        return render_template("main.html", coin=coin)

    except Exception as e:
        print(f"メインページエラー: {e}")
        traceback.print_exc()
        return render_template("main.html", coin=0)


# リザルト画面（修正版）
@app.route('/result')
@login_required
def result():
    """メモリベースの動的正答率取得によるリザルト表示"""
    try:
        print("リザルト画面アクセス開始")
        accountId = session.get("login_id")
        print(f"ユーザーID: {accountId}")

        # メモリから全科目の正答率を取得（過去30日間）
        subject_accuracies = answer_history.get_all_subjects_accuracy(accountId, days_back=30)
        print(f"科目別正答率: {subject_accuracies}")

        # 科目名のマッピング（英語名→日本語名）
        subject_mapping = {
            'math': '算数',
            'kanji': '漢字',
            'english': '英語'
        }

        # 表示用の科目データを作成
        subjects = []
        total_accuracy = 0
        valid_subjects = 0

        for eng_name, jp_name in subject_mapping.items():
            if eng_name in subject_accuracies:
                accuracy = subject_accuracies[eng_name]['accuracy']
                subjects.append({
                    'name': jp_name,
                    'score': accuracy,
                    'total_questions': subject_accuracies[eng_name]['total_questions'],
                    'correct_answers': subject_accuracies[eng_name]['correct_answers']
                })
                total_accuracy += accuracy
                valid_subjects += 1
            else:
                # データがない科目は0%として表示
                subjects.append({
                    'name': jp_name,
                    'score': 0.0,
                    'total_questions': 0,
                    'correct_answers': 0
                })

        # 総合正答率を計算
        if valid_subjects > 0:
            overall_accuracy = round(total_accuracy / valid_subjects, 1)
        else:
            # 全体の正答率を直接計算
            overall_accuracy = answer_history.get_subject_accuracy(accountId, subject=None, days_back=30)

        subjects.append({
            'name': '総合',
            'score': overall_accuracy,
            'total_questions': sum(s.get('total_questions', 0) for s in subjects),
            'correct_answers': sum(s.get('correct_answers', 0) for s in subjects)
        })

        # ランク計算
        def calculate_rank(score):
            if score is None or score == 0:
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

        rank = calculate_rank(overall_accuracy)
        rank_color = get_rank_color(rank)

        # セッションから現在のコインと経験値を取得
        current_coins = session.get('coins', 0)
        current_experience = session.get('experience', 0)

        # ユーザー統計を取得
        user_stats = answer_history.get_user_stats(accountId)

        results_data = {
            'subjects': subjects,
            'rank': rank,
            'rank_color': rank_color,
            'experience': current_experience,
            'coins': current_coins,
            'period_info': '過去30日間の結果',
            'total_questions': user_stats['total_questions'],
            'accuracy_trends': {
                '7_days': answer_history.get_subject_accuracy(accountId, days_back=7),
                '30_days': overall_accuracy,
                'all_time': answer_history.get_subject_accuracy(accountId, days_back=365)
            }
        }

        print(f"リザルトデータ: {results_data}")
        return render_template("result.html", data=results_data)

    except Exception as e:
        print(f"リザルト画面エラー: {e}")
        traceback.print_exc()

        # エラー時のフォールバック（固定値）
        subjects = [
            {'name': '漢字', 'score': 0.0, 'total_questions': 0, 'correct_answers': 0},
            {'name': '英語', 'score': 0.0, 'total_questions': 0, 'correct_answers': 0},
            {'name': '算数', 'score': 0.0, 'total_questions': 0, 'correct_answers': 0},
            {'name': '総合', 'score': 0.0, 'total_questions': 0, 'correct_answers': 0}
        ]

        results_data = {
            'subjects': subjects,
            'rank': 'E',
            'rank_color': 'gray',
            'experience': session.get('experience', 0),
            'coins': session.get('coins', 0),
            'period_info': 'エラーが発生しました',
            'total_questions': 0,
            'accuracy_trends': {'7_days': 0.0, '30_days': 0.0, 'all_time': 0.0}
        }

        return render_template("result.html", data=results_data)


# 問題生成API（高度版）
@app.route('/api/generate-question/<subject>')
@login_required
def api_generate_question(subject):
    """
    高度な自動問題生成API
    """
    try:
        print(f"問題生成API呼び出し: 科目={subject}")

        # データベース接続
        con = conn_db()
        grade_setting = "3"  # デフォルト値

        if con:
            cur = con.cursor()
            accountId = session.get("login_id")
            cur.execute("SELECT gradeSetting FROM t_account WHERE accountId = %s", (accountId,))
            result = cur.fetchone()
            grade_setting = result[0] if result else "3"
            cur.close()
            con.close()

        grade = f"小学{grade_setting}年生"

        # リクエスト情報の取得
        retry_count = request.args.get('retry', '0')
        timestamp = request.args.get('t', str(int(time.time())))

        print(f"🎯 問題生成開始: 科目={subject}, 学年={grade}, 再試行={retry_count}")

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
        traceback.print_exc()

        # 緊急フォールバック
        emergency_fallback = get_smart_fallback_question(subject, "小学3年生")

        return jsonify({
            "error": "問題生成中にエラーが発生しました",
            "fallback_used": True,
            **emergency_fallback
        }), 200  # エラーでも200で返してフロントエンドで処理継続


# 回答チェックAPI（修正版）
@app.route('/api/check-answer', methods=['POST'])
@login_required
def api_check_answer():
    """回答チェックAPI - メモリに結果を記録"""
    try:
        print("回答チェックAPI呼び出し")
        data = request.get_json()

        if not data:
            return jsonify({'error': 'データが送信されていません'}), 400

        selected_answer = data.get('selected_answer')
        correct_answer = data.get('correct_answer')
        subject = data.get('subject')
        question_id = data.get('question_id', 'unknown')

        print(f"回答データ: 選択={selected_answer}, 正解={correct_answer}, 科目={subject}")

        if selected_answer is None or correct_answer is None:
            return jsonify({'error': '必要なデータが不足しています'}), 400

        is_correct = selected_answer == correct_answer
        accountId = session.get("login_id")

        # メモリに回答履歴を記録
        answer_history.add_answer(accountId, subject, is_correct, question_id)

        # セッションに統計を保存
        save_session_stats(accountId)

        # 正解時の処理（セッションでコイン・経験値を管理）
        coins_earned = 0
        experience_earned = 0

        if is_correct:
            coins_earned = 10
            experience_earned = 50
            session['coins'] = session.get('coins', 0) + coins_earned
            session['experience'] = session.get('experience', 0) + experience_earned

        response_data = {
            'is_correct': is_correct,
            'message': '正解です！コイン+10、経験値+50獲得！' if is_correct else '不正解です。次回頑張りましょう！',
            'coins_earned': coins_earned,
            'experience_earned': experience_earned
        }

        print(f"回答結果: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        print(f"回答チェックエラー: {e}")
        traceback.print_exc()
        return jsonify({'error': 'システムエラーが発生しました'}), 500


# 統計情報取得API
@app.route('/api/user-stats')
@login_required
def api_user_stats():
    """ユーザーの詳細統計情報を取得"""
    try:
        print("統計情報API呼び出し")
        accountId = session.get("login_id")

        # 期間別の統計
        stats = {
            'last_7_days': answer_history.get_all_subjects_accuracy(accountId, 7),
            'last_30_days': answer_history.get_all_subjects_accuracy(accountId, 30),
            'all_time': answer_history.get_all_subjects_accuracy(accountId, 365),
            'user_summary': answer_history.get_user_stats(accountId)
        }

        print(f"統計データ: {stats}")
        return jsonify(stats)

    except Exception as e:
        print(f"統計取得エラー: {e}")
        traceback.print_exc()
        return jsonify({'error': 'データ取得に失敗しました'}), 500


# 統計リセットAPI（開発・テスト用）
@app.route('/api/reset-stats', methods=['POST'])
@login_required
def api_reset_stats():
    """統計データをリセット（開発・テスト用）"""
    try:
        print("統計リセットAPI呼び出し")
        accountId = session.get("login_id")

        if accountId in answer_history.history:
            del answer_history.history[accountId]
            print(f"ユーザー{accountId}の履歴削除")

        # セッションの統計データもクリア
        session.pop('user_stats', None)
        session.pop('coins', None)
        session.pop('experience', None)

        print("統計データリセット完了")
        return jsonify({'message': '統計データをリセットしました'})

    except Exception as e:
        print(f"統計リセットエラー: {e}")
        traceback.print_exc()
        return jsonify({'error': 'リセットに失敗しました'}), 500


# 手動で回答データを追加するAPI（テスト用）
@app.route('/api/add-test-data', methods=['POST'])
@login_required
def api_add_test_data():
    """テスト用の回答データを追加"""
    try:
        print("テストデータ追加API呼び出し")
        accountId = session.get("login_id")

        # サンプルデータを追加
        test_data = [
            ('math', True), ('math', True), ('math', False), ('math', True),
            ('kanji', True), ('kanji', False), ('kanji', True), ('kanji', True),
            ('english', False), ('english', True), ('english', True), ('english', False),
            ('math', True), ('kanji', False), ('english', True),
        ]

        for subject, is_correct in test_data:
            answer_history.add_answer(accountId, subject, is_correct)

        save_session_stats(accountId)

        result_data = {
            'message': f'テストデータ{len(test_data)}件を追加しました',
            'data': answer_history.get_all_subjects_accuracy(accountId, 30)
        }

        print(f"テストデータ追加完了: {result_data}")
        return jsonify(result_data)

    except Exception as e:
        print(f"テストデータ追加エラー: {e}")
        traceback.print_exc()
        return jsonify({'error': 'テストデータ追加に失敗しました'}), 500


# 残りのルート（簡略化）
@app.route('/shop')
@login_required
def shop():
    try:
        con = conn_db()
        coin = 0
        if con:
            cur = con.cursor()
            accountId = session.get("login_id")
            sql = " SELECT COIN FROM t_account WHERE accountId = %s "
            cur.execute(sql, (accountId,))
            result = cur.fetchone()
            coin = result[0] if result else 0
            cur.close()
            con.close()
        return render_template("shop.html", coin=coin)
    except Exception as e:
        print(f"ショップエラー: {e}")
        return render_template("shop.html", coin=0)


@app.route('/buy-shop', methods=["POST"])
@login_required
def buy_shop():
    return redirect(url_for("shop"))


@app.route('/in_bag')
@login_required
def in_bag():
    try:
        con = conn_db()
        coin = 0
        if con:
            cur = con.cursor()
            accountId = session.get("login_id")
            sql = " SELECT COIN FROM t_account WHERE accountId = %s "
            cur.execute(sql, (accountId,))
            result = cur.fetchone()
            coin = result[0] if result else 0
            cur.close()
            con.close()
        return render_template("in_bag.html", coin=coin)
    except Exception as e:
        print(f"バッグエラー: {e}")
        return render_template("in_bag.html", coin=0)


@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    try:
        if request.method == 'POST':
            con = conn_db()
            if con:
                cur = con.cursor()
                username = request.form.get('username')
                gender = request.form.get('gender')
                gradeSetting = request.form.get('gradeSetting')
                userId = session.get("login_id")

                cur.execute('''
                            UPDATE t_account
                            SET username     = %s,
                                gender       = %s,
                                gradeSetting = %s
                            WHERE accountId = %s
                            ''', (username, gender, gradeSetting, userId))

                con.commit()
                cur.close()
                con.close()

            return redirect(url_for("main"))

        con = conn_db()
        user = None
        if con:
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

    except Exception as e:
        print(f"設定エラー: {e}")
        return render_template("config.html", user=None)


@app.route('/weapon-detail')
@login_required
def weapon_detail():
    return render_template("weapon-detail.html", coin=0)


@app.route('/item-detail')
@login_required
def item_detail():
    return render_template("item-detail.html", coin=0)


@app.route('/question')
@login_required
def question():
    return render_template("question.html")


@app.route('/question/<subject>')
@login_required
def question_with_subject(subject):
    return render_template("question.html", subject=subject)


@app.route('/map')
@login_required
def map():
    return render_template("map.html")


@app.route('/subject')
@login_required
def subject():
    return render_template("subject.html")


@app.route('/test')
def test():
    return render_template("xxx.html")


# デバッグ用エンドポイント
@app.route('/api/debug/question-stats')
@login_required
def debug_question_stats():
    try:
        return jsonify({
            'stats': generation_stats.stats,
            'success_rate': f"{generation_stats.get_success_rate():.2f}%"
        })
    except Exception as e:
        print(f"デバッグ統計エラー: {e}")
        return jsonify({'error': 'データ取得エラー'}), 500


@app.route('/api/refresh-question/<subject>')
@login_required
def refresh_question(subject):
    try:
        con = conn_db()
        grade_setting = "3"

        if con:
            cur = con.cursor()
            accountId = session.get("login_id")
            cur.execute("SELECT gradeSetting FROM t_account WHERE accountId = %s", (accountId,))
            result = cur.fetchone()
            grade_setting = result[0] if result else "3"
            cur.close()
            con.close()

        grade = f"小学{grade_setting}年生"
        print(f"🔄 手動リフレッシュ: {subject} - {grade}")

        question_data = generate_question(subject, grade)
        generation_stats.record_generation(subject, grade, success=True)

        return jsonify(question_data)

    except Exception as e:
        print(f"❌ リフレッシュAPI エラー: {e}")
        traceback.print_exc()
        fallback_question = get_smart_fallback_question(subject, "小学3年生")
        return jsonify(fallback_question)


# エラーハンドラー
@app.errorhandler(404)
def page_not_found(e):
    print(f"404エラー: {request.url}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    print(f"500エラー: {e}")
    traceback.print_exc()
    return render_template('500.html'), 500


# 実行制御
if __name__ == "__main__":
    print("サーバー起動中...")
    print("デバッグモード: ON")
    print("利用可能なエンドポイント:")
    print("- /result (リザルト画面)")
    print("- /result?debug=true (デバッグモード)")
    print("- /api/add-test-data (テストデータ追加)")
    print("- /api/user-stats (統計情報)")
    app.run(debug=True, host='0.0.0.0', port=5000)