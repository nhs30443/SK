from flask import Flask, render_template, jsonify, request
import random
from fractions import Fraction

app = Flask(__name__)


def generate_fraction_problem(grade):
    """信頼性の高い分数問題生成"""
    max_attempts = 10
    for _ in range(max_attempts):
        try:
            if grade == 5:
                denominator = random.randint(2, 5)
                numerator1 = random.randint(1, denominator * 2)
                numerator2 = random.randint(1, denominator * 2)
            else:  # grade 6
                denominator = random.randint(3, 9)
                numerator1 = random.randint(1, denominator * 2)
                numerator2 = random.randint(1, denominator * 2)

            if random.random() > 0.5:
                answer = Fraction(numerator1, denominator) + Fraction(numerator2, denominator)
                op = "+"
            else:
                a, b = max(numerator1, numerator2), min(numerator1, numerator2)
                answer = Fraction(a, denominator) - Fraction(b, denominator)
                op = "-"

            # 問題文生成
            def format_fraction(num, den):
                if grade == 6 and num > den:
                    whole = num // den
                    remainder = num % den
                    return f"{whole} {remainder}/{den}" if remainder != 0 else f"{whole}"
                return f"{num}/{den}"

            question = f"{format_fraction(numerator1, denominator)} {op} {format_fraction(numerator2, denominator)} = ?"

            if answer.numerator > 0:  # 有効な答えのみ返す
                return question, answer.lowest_terms()

        except:
            continue

    # デフォルトの安全な問題
    return "1/2 + 1/2 = ?", Fraction(1, 1)


@app.route('/generate_problem')
def generate_problem():
    grade = request.args.get('grade', '1')
    grade = int(grade)

    try:
        if grade == 1:
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            if random.random() > 0.5:
                answer = a + b
                question = f"{a} + {b} = ?"
            else:
                answer = max(a, b) - min(a, b)
                question = f"{max(a, b)} - {min(a, b)} = ?"

        elif grade in [2, 3]:
            a = random.randint(1, 9) if grade == 3 else random.randint(1, 5)
            b = random.randint(1, 9) if grade == 3 else random.randint(1, 5)
            answer = a * b
            question = f"{a} × {b} = ?"

        elif grade == 4:
            b = random.randint(1, 9)
            answer = random.randint(1, 9)
            a = answer * b
            question = f"{a} ÷ {b} = ?"

        elif grade == 5:
            if random.random() > 0.5:
                question, answer = generate_fraction_problem(grade)
            else:
                # 小数問題（安全な生成）
                for _ in range(10):
                    a = round(random.uniform(0.5, 2.0), 1)
                    b = round(random.uniform(0.5, 2.0), 1)
                    if random.random() > 0.5:
                        answer = a + b
                        question = f"{a} + {b} = ?"
                    else:
                        answer = max(a, b) - min(a, b)
                        question = f"{max(a, b)} - {min(a, b)} = ?"

                    if answer > 0.1:  # 0にならないように
                        answer = int(answer) if answer.is_integer() else round(answer, 1)
                        break
                else:
                    question, answer = "0.5 + 0.5 = ?", 1.0

        elif grade == 6:
            problem_type = random.choice(['fraction', 'decimal', 'mixed'])

            if problem_type == 'fraction':
                question, answer = generate_fraction_problem(grade)
            elif problem_type == 'decimal':
                for _ in range(10):
                    a = round(random.uniform(0.5, 5.0), 1)
                    b = round(random.uniform(0.5, 5.0), 1)
                    answer = round(a * b, 2)
                    if answer >= 0.5:  # 小さすぎる値を避ける
                        answer = int(answer) if answer.is_integer() else answer
                        question = f"{a} × {b} = ?"
                        break
                else:
                    question, answer = "1.0 × 2.0 = ?", 2
            else:
                a = random.randint(2, 9)
                b = random.randint(2, 9)
                c = random.randint(2, 9)
                answer = (a * b) + c
                question = f"({a} × {b}) + {c} = ?"

        # オプション生成
        options = generate_options(answer, grade)
        return jsonify({
            'question': question,
            'options': options,
            'answer': str(answer)
        })

    except Exception as e:
        # エラー時のデフォルト問題
        return jsonify({
            'question': "1 + 1 = ?",
            'options': ["1", "2", "3", "4"],
            'answer': "2"
        })


def generate_options(answer, grade):
    """安全なオプション生成"""
    try:
        # 答えの形式統一
        if isinstance(answer, Fraction):
            answer_str = str(answer.lowest_terms())
        elif isinstance(answer, float):
            answer_str = str(int(answer)) if answer.is_integer() else str(answer)
        else:
            answer_str = str(answer)

        options = [answer_str]
        seen = set([answer_str])

        # 適切な誤答生成
        def generate_wrong():
            if grade in [1, 2, 3, 4]:
                return str(int(answer) + random.choice([-2, -1, 1, 2]))
            elif grade == 5:
                if isinstance(answer, Fraction):
                    f = answer.lowest_terms()
                    if random.random() > 0.5:
                        return f"{f.numerator + random.choice([-1, 1])}/{f.denominator}"
                    return f"{f.numerator}/{f.denominator + random.choice([-1, 1])}"
                else:
                    diff = random.choice([-0.5, -0.1, 0.1, 0.5])
                    wrong = float(answer_str) + diff
                    return str(int(wrong)) if wrong.is_integer() else str(round(wrong, 1))
            else:  # grade 6
                if isinstance(answer, Fraction):
                    return str(answer + random.choice([Fraction(1, 1), Fraction(-1, 1)]))
                elif isinstance(answer, float):
                    diff = random.choice([-0.25, -0.1, 0.1, 0.25])
                    wrong = answer + diff
                    return str(int(wrong)) if wrong.is_integer() else str(round(wrong, 2))
                else:
                    return str(int(answer) + random.choice([-2, -1, 1, 2]))

        # 3つの誤答を生成
        while len(options) < 4:
            wrong = generate_wrong()
            if wrong not in seen:
                options.append(wrong)
                seen.add(wrong)

        random.shuffle(options)
        return options

    except:
        # エラー時のデフォルトオプション
        return ["1", "2", "3", "4"]


@app.route('/')
def index():
    return render_template('grade_select.html')


@app.route('/quiz')
def quiz():
    grade = request.args.get('grade', '1')
    return render_template('quiz.html', grade=grade)


if __name__ == '__main__':
    app.run(debug=True)