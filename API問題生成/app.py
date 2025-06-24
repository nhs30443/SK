from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
import random
import json
import os
from datetime import datetime
import time
import re
import hashlib

app = Flask(__name__)

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class ImprovedGeminiQuestionGenerator:
    def __init__(self):
        # Geminiモデルを初期化
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config=genai.types.GenerationConfig(
                    temperature=1.2,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=1024,
                    candidate_count=1
                )
            )
        else:
            self.model = None

        # 生成済み問題のハッシュを保存（重複防止）
        self.generated_questions = set()

        # 学年別カリキュラム設定
        self.grade_curriculum = self.initialize_curriculum()

        # フォールバック用データ（学年別）
        self.fallback_data = self.initialize_fallback_data()

    def initialize_curriculum(self):
        """学年別カリキュラムを初期化"""
        return {
            "math": {
                1: {
                    "operations": ["addition", "subtraction"],
                    "max_num": 20,
                    "concepts": ["1桁の足し算", "1桁の引き算", "10までの数"],
                    "keywords": ["かんたん", "はじめて", "すうじ"]
                },
                2: {
                    "operations": ["addition", "subtraction", "simple_multiplication"],
                    "max_num": 100,
                    "concepts": ["2桁の足し算", "2桁の引き算", "かけ算の基礎", "九九"],
                    "keywords": ["きほん", "れんしゅう", "ひょう"]
                },
                3: {
                    "operations": ["addition", "subtraction", "multiplication", "simple_division"],
                    "max_num": 1000,
                    "concepts": ["3桁の計算", "九九の完成", "わり算の基礎", "分数の導入"],
                    "keywords": ["おぼえる", "けいさん", "ぶんすう"]
                },
                4: {
                    "operations": ["addition", "subtraction", "multiplication", "division"],
                    "max_num": 10000,
                    "concepts": ["4桁の計算", "小数の基礎", "分数の計算", "面積"],
                    "keywords": ["しょうすう", "めんせき", "たんい"]
                },
                5: {
                    "operations": ["addition", "subtraction", "multiplication", "division", "fractions"],
                    "max_num": 100000,
                    "concepts": ["小数の計算", "分数の計算", "割合", "体積"],
                    "keywords": ["わりあい", "たいせき", "こうやく"]
                },
                6: {
                    "operations": ["addition", "subtraction", "multiplication", "division", "fractions", "ratios"],
                    "max_num": 1000000,
                    "concepts": ["分数の四則計算", "比と比の値", "円の面積", "速さ"],
                    "keywords": ["ひ", "はやさ", "えんしゅうりつ"]
                }
            },
            "english": {
                1: ["apple", "cat", "dog", "red", "blue", "one", "two"],
                2: ["book", "pen", "car", "big", "small", "three", "four"],
                3: ["school", "teacher", "friend", "happy", "sad", "five", "six"],
                4: ["family", "mother", "father", "birthday", "present", "seven", "eight"],
                5: ["weather", "sunny", "rainy", "vacation", "hobby", "nine", "ten"],
                6: ["nature", "mountain", "ocean", "environment", "culture", "eleven", "twelve"]
            },
            "kanji": {
                1: ["一", "二", "三", "人", "大", "小", "山", "川", "木", "火"],
                2: ["東", "西", "南", "北", "雨", "雪", "町", "村", "色", "形"],
                3: ["県", "都", "市", "区", "島", "橋", "神", "様", "物", "事"],
                4: ["都道府県", "歴史", "地理", "科学", "実験", "観察", "調査", "発見"],
                5: ["政治", "経済", "社会", "文化", "伝統", "技術", "産業", "環境"],
                6: ["憲法", "民主主義", "国際", "平和", "人権", "責任", "協力", "尊重"]
            }
        }

    def initialize_fallback_data(self):
        """学年別フォールバック問題データを初期化"""
        return {
            "math": {
                1: [
                    {"question": "2 + 3 = ?", "answer": 5, "choices": [5, 4, 6, 3]},
                    {"question": "5 - 2 = ?", "answer": 3, "choices": [3, 2, 4, 1]},
                    {"question": "1 + 4 = ?", "answer": 5, "choices": [5, 6, 4, 3]}
                ],
                2: [
                    {"question": "12 + 8 = ?", "answer": 20, "choices": [20, 19, 21, 18]},
                    {"question": "3 × 4 = ?", "answer": 12, "choices": [12, 10, 14, 8]},
                    {"question": "25 - 7 = ?", "answer": 18, "choices": [18, 17, 19, 16]}
                ],
                3: [
                    {"question": "123 + 45 = ?", "answer": 168, "choices": [168, 165, 170, 163]},
                    {"question": "7 × 8 = ?", "answer": 56, "choices": [56, 54, 58, 52]},
                    {"question": "81 ÷ 9 = ?", "answer": 9, "choices": [9, 8, 10, 7]}
                ],
                # ... 4-6年生の問題も同様に定義
            }
        }

    def create_diverse_prompt(self, subject, grade, attempt=0):
        """学年別に最適化されたプロンプトを生成"""
        current_time = datetime.now()
        random_seed = current_time.microsecond

        grade_names = {1: "1年生", 2: "2年生", 3: "3年生", 4: "4年生", 5: "5年生", 6: "6年生"}
        grade_name = grade_names.get(grade, "1年生")

        if subject == 'math':
            curriculum = self.grade_curriculum["math"].get(grade, self.grade_curriculum["math"][1])
            operations = curriculum["operations"]
            max_num = curriculum["max_num"]
            concepts = curriculum["concepts"]

            operation_type = random.choice(operations)
            concept = random.choice(concepts)

            prompt = f"""
小学校{grade_name}向けの算数問題を1問作成してください。

重要な条件:
- 学年: 小学校{grade_name}
- 対象概念: {concept}
- 使用する数の範囲: 1～{max_num}
- 問題の種類: {operation_type}
- 難易度: {grade_name}レベルに適切
- ランダムシード: {random_seed}
- 試行回数: {attempt + 1}

学習指導要領に基づく{grade_name}の算数内容:
{', '.join(concepts)}

以下のJSON形式のみで回答してください:
```json
{{
    "question": "計算問題（{grade_name}レベル）",
    "choices": [数値1, 数値2, 数値3, 数値4],
    "correct_answer": 正解のインデックス番号（0-3）,
    "explanation": "詳しい解説文（{grade_name}にわかりやすく）",
    "grade_level": {grade},
    "concept": "{concept}"
}}
```

{grade_name}の児童にとって適切な難易度で、理解しやすい問題を作成してください。
"""

        elif subject == 'english':
            words = self.grade_curriculum["english"].get(grade, self.grade_curriculum["english"][1])
            word = random.choice(words)

            prompt = f"""
小学校{grade_name}向けの英語問題を1問作成してください。

重要な条件:
- 学年: 小学校{grade_name}
- 対象単語レベル: {grade_name}で学習する英単語
- 基本単語例: {', '.join(words[:5])}
- ランダムシード: {random_seed}
- 試行回数: {attempt + 1}

以下のJSON形式のみで回答してください:
```json
{{
    "question": "「英単語」の意味は何ですか？",
    "choices": ["日本語1", "日本語2", "日本語3", "日本語4"],
    "correct_answer": 正解のインデックス番号（0-3）,
    "explanation": "「英単語」は「意味」という意味です。{grade_name}で習う大切な単語です。",
    "grade_level": {grade},
    "word_category": "基本単語"
}}
```

{grade_name}の児童が知っている範囲の英単語で問題を作成してください。
"""

        elif subject == 'kanji':
            kanji_list = self.grade_curriculum["kanji"].get(grade, self.grade_curriculum["kanji"][1])
            target_kanji = random.choice(kanji_list)

            prompt = f"""
小学校{grade_name}向けの漢字問題を1問作成してください。

重要な条件:
- 学年: 小学校{grade_name}
- 対象漢字レベル: {grade_name}配当漢字
- 漢字例: {', '.join(kanji_list[:5])}
- ランダムシード: {random_seed}
- 試行回数: {attempt + 1}

以下のJSON形式のみで回答してください:
```json
{{
    "question": "「漢字」の読み方は何ですか？",
    "choices": ["ひらがな1", "ひらがな2", "ひらがな3", "ひらがな4"],
    "correct_answer": 正解のインデックス番号（0-3）,
    "explanation": "「漢字」は「よみかた」と読みます。{grade_name}で習う漢字です。",
    "grade_level": {grade},
    "kanji_category": "{grade_name}配当漢字"
}}
```

{grade_name}で習う漢字を使って、適切な難易度の問題を作成してください。
"""

        return prompt

    def generate_question_hash(self, question_data):
        """問題のハッシュを生成して重複チェック"""
        question_str = f"{question_data.get('question', '')}{question_data.get('choices', [])}"
        return hashlib.md5(question_str.encode()).hexdigest()

    def extract_json_from_response(self, response_text):
        """レスポンステキストからJSONを抽出"""
        patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*"question"[^{}]*"choices"[^{}]*"correct_answer"[^{}]*"explanation"[^{}]*\})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    cleaned_json = match.strip()
                    if not cleaned_json.endswith('}'):
                        cleaned_json += '}'

                    parsed = json.loads(cleaned_json)
                    if self.validate_question_data(parsed):
                        return parsed
                except:
                    continue

        return None

    def generate_math_question_ai(self, grade=1):
        """学年対応算数問題生成"""
        if not self.model:
            return self.generate_fallback_math_question(grade)

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                prompt = self.create_diverse_prompt('math', grade, attempt)
                response = self.model.generate_content(prompt)
                content = response.text.strip()

                question_data = self.extract_json_from_response(content)

                if question_data:
                    question_hash = self.generate_question_hash(question_data)
                    if question_hash not in self.generated_questions:
                        self.generated_questions.add(question_hash)
                        question_data['grade'] = grade  # 学年情報を追加
                        return question_data
                    else:
                        time.sleep(0.5)
                        continue

            except Exception as e:
                print(f"Gemini生成エラー（算数{grade}年、試行 {attempt + 1}）: {e}")
                time.sleep(1)
                continue

        return self.generate_fallback_math_question(grade)

    def generate_english_question_ai(self, grade=1):
        """学年対応英語問題生成"""
        if not self.model:
            return self.generate_fallback_english_question(grade)

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                prompt = self.create_diverse_prompt('english', grade, attempt)
                response = self.model.generate_content(prompt)
                content = response.text.strip()

                question_data = self.extract_json_from_response(content)

                if question_data:
                    question_hash = self.generate_question_hash(question_data)
                    if question_hash not in self.generated_questions:
                        self.generated_questions.add(question_hash)
                        question_data['grade'] = grade
                        return question_data
                    else:
                        time.sleep(0.5)
                        continue

            except Exception as e:
                print(f"Gemini生成エラー（英語{grade}年、試行 {attempt + 1}）: {e}")
                time.sleep(1)
                continue

        return self.generate_fallback_english_question(grade)

    def generate_kanji_question_ai(self, grade=1):
        """学年対応漢字問題生成"""
        if not self.model:
            return self.generate_fallback_kanji_question(grade)

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                prompt = self.create_diverse_prompt('kanji', grade, attempt)
                response = self.model.generate_content(prompt)
                content = response.text.strip()

                question_data = self.extract_json_from_response(content)

                if question_data:
                    question_hash = self.generate_question_hash(question_data)
                    if question_hash not in self.generated_questions:
                        self.generated_questions.add(question_hash)
                        question_data['grade'] = grade
                        return question_data
                    else:
                        time.sleep(0.5)
                        continue

            except Exception as e:
                print(f"Gemini生成エラー（漢字{grade}年、試行 {attempt + 1}）: {e}")
                time.sleep(1)
                continue

        return self.generate_fallback_kanji_question(grade)

    def generate_fallback_math_question(self, grade=1):
        """学年別フォールバック算数問題"""
        curriculum = self.grade_curriculum["math"].get(grade, self.grade_curriculum["math"][1])
        operations = curriculum["operations"]
        max_num = curriculum["max_num"]

        operation = random.choice(operations)

        if operation == "addition":
            if grade <= 2:
                a = random.randint(1, min(20, max_num))
                b = random.randint(1, min(20, max_num))
            else:
                a = random.randint(1, max_num // 10)
                b = random.randint(1, max_num // 10)

            question = f"{a} + {b} = ?"
            correct_answer = a + b

        elif operation == "subtraction":
            if grade <= 2:
                a = random.randint(5, min(20, max_num))
                b = random.randint(1, a)
            else:
                a = random.randint(max_num // 20, max_num // 5)
                b = random.randint(1, a)

            question = f"{a} - {b} = ?"
            correct_answer = a - b

        elif operation == "multiplication" or operation == "simple_multiplication":
            if grade <= 3:
                a = random.randint(2, 9)
                b = random.randint(2, 9)
            else:
                a = random.randint(2, 12)
                b = random.randint(2, 12)

            question = f"{a} × {b} = ?"
            correct_answer = a * b

        elif operation == "division" or operation == "simple_division":
            if grade <= 3:
                b = random.randint(2, 9)
                correct_answer = random.randint(2, 9)
            else:
                b = random.randint(2, 12)
                correct_answer = random.randint(2, 12)

            a = b * correct_answer
            question = f"{a} ÷ {b} = ?"

        else:  # その他の場合は足し算にフォールバック
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            question = f"{a} + {b} = ?"
            correct_answer = a + b

        # 間違い選択肢を生成
        choices = [correct_answer]
        for _ in range(3):
            while True:
                if operation in ["addition", "multiplication"]:
                    wrong = correct_answer + random.randint(-5, 5)
                else:
                    wrong = correct_answer + random.randint(-3, 3)

                if wrong > 0 and wrong not in choices:
                    choices.append(wrong)
                    break

        random.shuffle(choices)
        correct_index = choices.index(correct_answer)

        return {
            "question": question,
            "choices": choices,
            "correct_answer": correct_index,
            "explanation": f"正解は {correct_answer} です。",
            "grade": grade,
            "grade_level": grade
        }

    def generate_fallback_english_question(self, grade=1):
        """学年別フォールバック英語問題"""
        words_by_grade = {
            1: {"cat": "ねこ", "dog": "いぬ", "red": "あか", "blue": "あお"},
            2: {"book": "ほん", "pen": "ペン", "big": "おおきい", "small": "ちいさい"},
            3: {"school": "がっこう", "happy": "うれしい", "friend": "ともだち", "teacher": "せんせい"},
            4: {"family": "かぞく", "mother": "おかあさん", "father": "おとうさん", "birthday": "たんじょうび"},
            5: {"weather": "てんき", "sunny": "はれ", "rainy": "あめ", "vacation": "やすみ"},
            6: {"nature": "しぜん", "mountain": "やま", "ocean": "うみ", "environment": "かんきょう"}
        }

        grade_words = words_by_grade.get(grade, words_by_grade[1])
        word = random.choice(list(grade_words.keys()))
        correct_meaning = grade_words[word]

        # 他の学年の単語から間違い選択肢を生成
        all_meanings = []
        for g_words in words_by_grade.values():
            all_meanings.extend(g_words.values())

        choices = [correct_meaning]
        while len(choices) < 4:
            wrong_meaning = random.choice(all_meanings)
            if wrong_meaning not in choices:
                choices.append(wrong_meaning)

        random.shuffle(choices)
        correct_index = choices.index(correct_meaning)

        return {
            "question": f"「{word}」の意味は何ですか？",
            "choices": choices,
            "correct_answer": correct_index,
            "explanation": f"「{word}」は「{correct_meaning}」という意味です。",
            "grade": grade,
            "grade_level": grade
        }

    def generate_fallback_kanji_question(self, grade=1):
        """学年別フォールバック漢字問題"""
        kanji_by_grade = {
            1: {"山": "やま", "川": "かわ", "人": "ひと", "大": "おお"},
            2: {"東": "ひがし", "西": "にし", "南": "みなみ", "北": "きた"},
            3: {"県": "けん", "市": "し", "町": "まち", "村": "むら"},
            4: {"都": "と", "府": "ふ", "区": "く", "島": "しま"},
            5: {"政": "せい", "治": "じ", "経": "けい", "済": "ざい"},
            6: {"憲": "けん", "法": "ほう", "民": "みん", "主": "しゅ"}
        }

        grade_kanji = kanji_by_grade.get(grade, kanji_by_grade[1])
        kanji = random.choice(list(grade_kanji.keys()))
        correct_reading = grade_kanji[kanji]

        # 間違い選択肢を生成
        all_readings = []
        for g_kanji in kanji_by_grade.values():
            all_readings.extend(g_kanji.values())

        choices = [correct_reading]
        while len(choices) < 4:
            wrong_reading = random.choice(all_readings)
            if wrong_reading not in choices:
                choices.append(wrong_reading)

        random.shuffle(choices)
        correct_index = choices.index(correct_reading)

        return {
            "question": f"「{kanji}」の読み方は何ですか？",
            "choices": choices,
            "correct_answer": correct_index,
            "explanation": f"「{kanji}」は「{correct_reading}」と読みます。",
            "grade": grade,
            "grade_level": grade
        }

    def validate_question_data(self, data):
        """問題データの検証"""
        try:
            required_keys = ["question", "choices", "correct_answer", "explanation"]
            for key in required_keys:
                if key not in data:
                    return False

            if not isinstance(data["choices"], list) or len(data["choices"]) != 4:
                return False

            if not isinstance(data["correct_answer"], int) or not (0 <= data["correct_answer"] <= 3):
                return False

            return True
        except:
            return False


# グローバルインスタンス
improved_generator = ImprovedGeminiQuestionGenerator()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/subject/<subject>')
def subject_page(subject):
    if subject not in ['math', 'english', 'kanji']:
        return redirect(url_for('index'))

    subject_names = {'math': '算数', 'english': '英語', 'kanji': '漢字'}

    return render_template('subject.html',
                           subject=subject,
                           subject_name=subject_names[subject])


@app.route('/api/generate_question', methods=['POST'])
def generate_question():
    data = request.json
    subject = data.get('subject')
    grade = data.get('grade', 1)  # level → grade に変更

    try:
        start_time = time.time()

        if subject == 'math':
            question_data = improved_generator.generate_math_question_ai(grade)
        elif subject == 'english':
            question_data = improved_generator.generate_english_question_ai(grade)
        elif subject == 'kanji':
            question_data = improved_generator.generate_kanji_question_ai(grade)
        else:
            return jsonify({"error": "Invalid subject"}), 400

        generation_time = time.time() - start_time

        return jsonify({
            "success": True,
            "question": question_data,
            "generation_time": round(generation_time, 2),
            "generated_by": "Gemini AI Enhanced" if GEMINI_API_KEY and improved_generator.model else "Enhanced Fallback",
            "grade": grade
        })

    except Exception as e:
        print(f"問題生成エラー: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    user_answer = data.get('answer')
    correct_answer = data.get('correct_answer')
    explanation = data.get('explanation', '')
    grade = data.get('grade', 1)

    is_correct = user_answer == correct_answer

    grade_messages = {
        1: {"correct": "せいかいです！すごいね！🌟", "incorrect": "がんばろう！つぎはできるよ！😊"},
        2: {"correct": "正解です！よくできました！🎉", "incorrect": "おしい！もう一度チャレンジ！😊"},
        3: {"correct": "正解！すばらしいです！✨", "incorrect": "いい線いってる！がんばろう！😊"},
        4: {"correct": "正解です！とても良くできました！🌟", "incorrect": "あと少し！がんばって！😊"},
        5: {"correct": "正解！優秀です！🎊", "incorrect": "もう一度考えてみよう！😊"},
        6: {"correct": "正解！素晴らしい理解力です！🏆", "incorrect": "良い思考です！もう一度挑戦！😊"}
    }

    messages = grade_messages.get(grade, grade_messages[1])
    message = messages["correct"] if is_correct else messages["incorrect"]

    return jsonify({
        "correct": is_correct,
        "explanation": explanation,
        "message": message,
        "grade": grade
    })


@app.route('/api/status')
def api_status():
    return jsonify({
        "gemini_configured": bool(GEMINI_API_KEY and improved_generator.model),
        "status": "ready",
        "fallback_available": True,
        "api_provider": "Google Gemini Enhanced",
        "supported_grades": list(range(1, 7)),
        "unique_questions_generated": len(improved_generator.generated_questions)
    })


@app.route('/api/clear_cache', methods=['POST'])
def clear_question_cache():
    """生成済み問題キャッシュをクリア"""
    improved_generator.generated_questions.clear()
    return jsonify({
        "success": True,
        "message": "問題キャッシュをクリアしました",
        "cache_size": len(improved_generator.generated_questions)
    })


# app.pyに以下のコードを追加（既存のコードの最後、if __name__ == '__main__':の前に追加）

from flask import send_from_directory, make_response
import os


@app.route('/favicon.ico')
def favicon():
    """
    favicon.icoのリクエストを処理
    staticフォルダにfavicon.icoがある場合はそれを返し、
    ない場合は絵文字ベースのSVGアイコンを返す
    """
    favicon_path = os.path.join(app.root_path, 'static', 'favicon.ico')

    if os.path.exists(favicon_path):
        # staticフォルダにfavicon.icoがある場合
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    else:
        # ない場合は絵文字ベースのSVGアイコンを生成
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="100" height="100" fill="#667eea"/>
            <text x="50" y="70" font-size="60" text-anchor="middle" fill="white">📚</text>
        </svg>'''

        response = make_response(svg_content)
        response.headers['Content-Type'] = 'image/svg+xml'
        response.headers['Cache-Control'] = 'max-age=86400'  # 24時間キャッシュ
        return response


@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """
    Apple Touch Iconの処理
    """
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180">
        <rect width="180" height="180" fill="#667eea" rx="20"/>
        <text x="90" y="125" font-size="100" text-anchor="middle" fill="white">📚</text>
    </svg>'''

    response = make_response(svg_content)
    response.headers['Content-Type'] = 'image/svg+xml'
    response.headers['Cache-Control'] = 'max-age=86400'
    return response


@app.route('/manifest.json')
def manifest():
    """
    PWA対応のためのmanifest.json
    """
    manifest_data = {
        "name": "小学生学習サイト",
        "short_name": "学習サイト",
        "description": "小学生向けAI問題生成学習サイト",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#667eea",
        "icons": [
            {
                "src": "/apple-touch-icon.png",
                "sizes": "180x180",
                "type": "image/svg+xml"
            }
        ]
    }

    response = make_response(manifest_data)
    response.headers['Content-Type'] = 'application/json'
    return response


# ロボット対応
@app.route('/robots.txt')
def robots():
    """
    robots.txtの処理
    """
    robots_content = """User-agent: *
Allow: /
Sitemap: /sitemap.xml
"""
    response = make_response(robots_content)
    response.headers['Content-Type'] = 'text/plain'
    return response


# セキュリティヘッダーの追加
@app.after_request
def after_request(response):
    """
    セキュリティヘッダーを追加
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# エラーハンドラーの追加
@app.errorhandler(404)
def not_found_error(error):
    """
    404エラーページ
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    500エラーページ
    """
    return render_template('500.html'), 500



if __name__ == '__main__':
    if GEMINI_API_KEY:
        print("✅ Google Gemini API設定済み - 学年別AI問題生成が利用可能です")
        print("📚 対応学年: 小学1年生〜6年生")
        print("🎯 学習指導要領対応カリキュラム搭載")
    else:
        print("⚠️  Gemini APIキーが設定されていません - 学年別フォールバック問題を使用します")
        print("   環境変数 GEMINI_API_KEY を設定してください")

    app.run(debug=True, host='0.0.0.0', port=5000)