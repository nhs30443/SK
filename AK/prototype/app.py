from flask import Flask, render_template, request, redirect, url_for, flash
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


def generate_choices(answer):
    """ 正解を含む4つの選択肢を生成 """
    if isinstance(answer, int):
        # 整数の場合
        choices = [answer]
        while len(choices) < 4:
            offset = random.randint(1, 10)
            wrong = answer + offset if random.choice([True, False]) else answer - offset
            if wrong > 0 and wrong not in choices:
                choices.append(wrong)
    else:
        # 分数の場合 (例: "3/4")
        a, b = map(int, answer.split('/'))
        choices = [answer]
        while len(choices) < 4:
            if random.choice([True, False]):
                # 分母を変更
                wrong = f"{a}/{b + random.randint(1, 3)}"
            else:
                # 分子を変更
                wrong = f"{a + random.randint(1, 3)}/{b}"
            if wrong not in choices:
                choices.append(wrong)

    random.shuffle(choices)
    return choices


def generate_math_question(grade):
    """ 学年別に算数問題と4択を生成 """
    if grade == "小1":
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        answer = a + b
        return f"{a} + {b} = ?", answer, generate_choices(answer)
    elif grade == "小2":
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        answer = a + b
        return f"{a} + {b} = ?", answer, generate_choices(answer)
    elif grade == "小3":
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        answer = a * b
        return f"{a} × {b} = ?", answer, generate_choices(answer)
    elif grade == "小4":
        a = random.randint(10, 99)
        b = random.randint(1, 9)
        answer = a * b
        return f"{a} × {b} = ?", answer, generate_choices(answer)
    elif grade == "小5":
        denom = random.randint(2, 9)
        numer = random.randint(1, denom - 1)
        answer = f"{numer * 2}/{denom}"
        return f"{numer}/{denom} + {numer}/{denom} = ?", answer, generate_choices(answer)
    elif grade == "小6":
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        answer = f"{a * a}/{b * b}"
        return f"{a}/{b} ÷ {b}/{a} = ?", answer, generate_choices(answer)
    else:
        return None, None, None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/select_grade', methods=['POST'])
def select_grade():
    grade = request.form.get('grade')
    valid_grades = ["小1", "小2", "小3", "小4", "小5", "小6"]
    if grade not in valid_grades:
        flash("無効な学年です", "error")
        return redirect(url_for('index'))
    return redirect(url_for('question', grade=grade))


@app.route('/question/<grade>')
def question(grade):
    question, answer, choices = generate_math_question(grade)
    if not question:
        flash("問題生成に失敗しました", "error")
        return redirect(url_for('index'))
    # 答えを文字列型に統一
    return render_template('question.html',
                         grade=grade,
                         question=question,
                         answer=str(answer),
                         choices=[str(c) for c in choices])


if __name__ == '__main__':
    app.run(debug=True)