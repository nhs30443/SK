import random

def generate_question():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    op = random.choice(['+', '-', '×'])

    if op == '+':
        correct = a + b
    elif op == '-':
        correct = a - b
    else:
        correct = a * b

    question = f"{a} {op} {b} = ?"

    # 正解＋ダミー選択肢作成
    choices = set()
    choices.add(correct)
    while len(choices) < 4:
        delta = random.randint(-10, 10)
        if delta != 0:
            choices.add(correct + delta)

    choices = list(choices)
    random.shuffle(choices)

    return question, choices, correct

def export_to_html(question, choices, correct):
    labels = ['A', 'B', 'C', 'D']
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>算数クイズ</title>
    <style>
        body {{ font-family: sans-serif; padding: 30px; }}
        .question {{ font-size: 24px; margin-bottom: 20px; }}
        .choice {{ margin: 10px 0; }}
        #result {{ font-weight: bold; font-size: 20px; margin-top: 20px; }}
        .correct {{ color: green; }}
        .wrong {{ color: red; }}
    </style>
</head>
<body>
    <h1>🎲 算数クイズ 🎲</h1>
    <div class="question">{question}</div>
    <form id="quizForm">
"""

    for i, (label, choice) in enumerate(zip(labels, choices)):
        html_content += f"""
        <div class="choice">
            <label>
                <input type="radio" name="answer" value="{choice}"> {label}. {choice}
            </label>
        </div>"""

    html_content += f"""
        <button type="button" onclick="checkAnswer()">答え合わせ</button>
        <div id="result"></div>
    </form>

    <script>
    function checkAnswer() {{
        const radios = document.getElementsByName("answer");
        let selected = null;
        for (const r of radios) {{
            if (r.checked) {{
                selected = parseInt(r.value);
                break;
            }}
        }}

        const resultDiv = document.getElementById("result");

        if (selected === null) {{
            resultDiv.textContent = "選択肢を選んでください。";
            resultDiv.className = "";
        }} else if (selected === {correct}) {{
            resultDiv.textContent = "⭕ 正解です！";
            resultDiv.className = "correct";
        }} else {{
            resultDiv.textContent = "❌ 不正解です。";
            resultDiv.className = "wrong";
        }}
    }}
    </script>
</body>
</html>
"""

    with open("quiz.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✔ quiz.html を出力しました（選択肢：A～D）")

# 実行部分
question, choices, correct = generate_question()
export_to_html(question, choices, correct)
