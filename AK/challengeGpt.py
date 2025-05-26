import random
from fractions import Fraction
import json
import datetime
from collections import defaultdict


def generate_math_question(grade_level):
    """
    指定された学年レベルに適した算数問題を生成
    Returns:
        tuple: (問題文, 正解, 選択肢リスト)
    """
    max_num = grade_level * 12

    op_weights = {
        '+': 0.35,
        '-': 0.35,
        '×': 0.25,
        '÷': 0.05 if grade_level <= 2 else 0.15 if grade_level <= 4 else 0.1
    }

    op = random.choices(list(op_weights.keys()), weights=list(op_weights.values()))[0]

    def generate_choices(correct):
        choices = set()
        while len(choices) < 3:
            delta = random.randint(-5, 5)
            if delta == 0:
                continue
            fake = correct + delta
            if isinstance(correct, Fraction):
                fake = Fraction(fake).limit_denominator()
            choices.add(fake)
        choices = list(choices)
        choices.append(correct)
        random.shuffle(choices)
        return [str(c) for c in choices]

    if op == '+':
        a = random.randint(1, max_num)
        b = random.randint(1, max_num)
        answer = a + b
    elif op == '-':
        a = random.randint(1, max_num)
        b = random.randint(1, a)
        answer = a - b
    elif op == '×':
        if grade_level >= 5 and random.random() < 0.3:
            # 小5以上で分数の掛け算
            num1 = Fraction(random.randint(1, 9), random.randint(2, 9))
            num2 = Fraction(random.randint(1, 9), random.randint(2, 9))
            answer = num1 * num2
            question = f"{num1} × {num2} = ?"
            return question, str(answer), generate_choices(answer)
        else:
            a = random.randint(1, max_num // 2)
            b = random.randint(1, max_num // 2)
            answer = a * b
    elif op == '÷':
        pattern = random.choice(['exact', 'remainder', 'fraction', 'reduce'])
        if pattern == 'exact':
            b = random.randint(1, 12)
            a = b * random.randint(1, 10)
            answer = Fraction(a, b)
        elif pattern == 'remainder':
            b = random.randint(2, 12)
            a = random.randint(b + 1, b * 10)
            if a % b == 0:
                a += 1
            answer = Fraction(a, b)
        elif pattern == 'fraction':
            a = random.randint(1, 10)
            b = random.randint(2, 10)
            answer = Fraction(a, b)
        else:  # reduce
            common = random.randint(2, 5)
            num = common * random.randint(2, 5)
            den = common * random.randint(2, 5)
            answer = Fraction(num, den)
        question = f"{a} ÷ {b} = ?"
        return question, str(answer), generate_choices(answer)

    question = f"{a} {op} {b} = ?"
    return question, str(answer), generate_choices(answer)


def check_answer(user_input, correct_answer):
    def parse_number(s):
        try:
            if ' ' in s:
                whole, frac = s.split(' ')
                num, den = map(int, frac.split('/'))
                return Fraction(int(whole)) + Fraction(num, den)
            elif '/' in s:
                return Fraction(s)
            else:
                return Fraction(int(s), 1)
        except:
            return None

    user_value = parse_number(user_input)
    correct_value = parse_number(correct_answer)
    return user_value == correct_value if user_value is not None and correct_value is not None else False


def save_test_result(grade, score, total):
    result = {
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'grade': grade,
        'score': score,
        'percentage': round(score / total * 100, 1),
        'level': get_level_description(grade)
    }
    try:
        with open('math_quiz_results.json', 'a') as f:
            json.dump(result, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        print(f"結果の保存に失敗しました: {e}")


def get_level_description(grade):
    levels = {
        1: "小学1年生",
        2: "小学2年生",
        3: "小学3年生",
        4: "小学4年生",
        5: "小学5年生",
        6: "小学6年生"
    }
    return levels.get(grade, f"小学{grade}年生")


def show_statistics():
    try:
        with open('math_quiz_results.json', 'r') as f:
            results = [json.loads(line) for line in f]

        if not results:
            print("まだ記録がありません")
            return

        print("\n📊 あなたの成績 📊")
        print("---------------------")

        grade_stats = defaultdict(list)
        for r in results:
            grade_stats[r['grade']].append(r['percentage'])

        for grade, percentages in sorted(grade_stats.items()):
            avg = sum(percentages) / len(percentages)
            print(f"{get_level_description(grade)}: 平均 {avg:.1f}% ({len(percentages)}回)")

        total_avg = sum(r['percentage'] for r in results) / len(results)
        print(f"\n全体平均: {total_avg:.1f}%")
        best = max(results, key=lambda x: x['percentage'])
        print(f"最高記録: {best['percentage']}% ({best['date']})")

    except FileNotFoundError:
        print("成績ファイルが見つかりません")


def run_math_quiz():
    print("✨ 算数マスター ✨")
    print("---------------------")

    while True:
        try:
            grade = int(input("学年を選んでください (1-6): "))
            if 1 <= grade <= 6:
                break
            print("1から6の数字を入力してください")
        except ValueError:
            print("数字を入力してください")

    question_count = 5
    correct = 0

    print(f"\n{get_level_description(grade)}レベルで{question_count}問出題します！\n")

    for q_num in range(1, question_count + 1):
        question, answer, choices = generate_math_question(grade)
        print(f"問題 {q_num}: {question}")

        for idx, choice in enumerate(choices, 1):
            print(f"{idx}. {choice}")

        attempts = 0
        max_attempts = 2

        while attempts < max_attempts:
            try:
                user_input = input("番号で答えてください (1-4): ").strip()
                selected = int(user_input)
                if 1 <= selected <= 4:
                    if check_answer(choices[selected - 1], answer):
                        print("正解！🎉\n")
                        correct += 1
                        break
                    else:
                        attempts += 1
                        if attempts < max_attempts:
                            print("もう一度考えてみましょう！")
                        else:
                            print(f"正解は {answer} でした\n")
                    break
                else:
                    print("1〜4の数字を入力してください")
            except ValueError:
                print("数字で入力してください")

    percentage = correct / question_count * 100
    print("\n⭐️ 結果 ⭐️")
    print(f"正解数: {correct}/{question_count}")
    print(f"得点率: {percentage:.1f}%")

    save_test_result(grade, correct, question_count)
    show_statistics()


def main():
    while True:
        run_math_quiz()
        while True:
            choice = input("\nもう一度プレイしますか？ (y/n): ").lower()
            if choice in ['y', 'n']:
                break
            print("y か n を入力してください")
        if choice == 'n':
            print("また挑戦してくださいね！")
            break


if __name__ == "__main__":
    main()