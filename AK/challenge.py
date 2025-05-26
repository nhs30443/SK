import random
from fractions import Fraction
import json
import datetime
from collections import defaultdict


def generate_math_question(grade_level):
    """
    指定された学年レベルに適した算数問題を生成
    Args:
        grade_level (int): 1（小1）～6（小6）
    Returns:
        tuple: (問題文, 正解)
    """
    max_num = grade_level * 12  # 数値範囲を少し広めに

    # 学年に応じた演算子の重み付け
    op_weights = {
        '+': 0.35,
        '-': 0.35,
        '×': 0.25,
        '÷': 0.05 if grade_level <= 2 else 0.15 if grade_level <= 4 else 0.1
    }

    # 重みに基づいて演算子を選択
    op = random.choices(
        list(op_weights.keys()),
        weights=list(op_weights.values())
    )[0]

    # 問題生成ロジック
    if op == '+':
        a = random.randint(1, max_num)
        b = random.randint(1, max_num)
        answer = a + b
    elif op == '-':
        a = random.randint(1, max_num)
        b = random.randint(1, a)  # a >= b を保証
        answer = a - b
    elif op == '×':
        if grade_level <= 2:
            a = random.randint(1, 9)
            b = random.randint(1, 9)
        else:
            a = random.randint(1, max_num // 2)
            b = random.randint(1, max_num // 2)
        answer = a * b
    else:  # 割り算
        if grade_level <= 3:  # 低学年向け
            b = random.randint(1, 10)
            a = b * random.randint(1, 10)  # 必ず割り切れる
        else:  # 高学年向け
            b = random.randint(2, 12)
            upper_limit = b * 10
            a = random.randint(b, upper_limit)

            # 60%の確率で割り切れる問題に
            if random.random() < 0.6:
                a = b * random.randint(1, 10)

        answer = Fraction(a, b)

    question = f"{a} {op} {b} = ?"
    return question, str(answer)


def check_answer(user_input, correct_answer):
    """
    ユーザーの回答を検証（分数と整数の両方に対応）
    Args:
        user_input (str): ユーザー入力
        correct_answer (str): 正解
    Returns:
        bool: 正解かどうか
    """

    def parse_number(s):
        try:
            if ' ' in s:  # 帯分数 (例: 1 1/2)
                whole, frac = s.split(' ')
                num, den = map(int, frac.split('/'))
                return Fraction(whole) + Fraction(num, den)
            elif '/' in s:  # 分数 (例: 3/4)
                return Fraction(s)
            else:  # 整数
                return Fraction(int(s), 1)
        except:
            return None

    user_value = parse_number(user_input)
    correct_value = parse_number(correct_answer)

    return user_value == correct_value if (user_value and correct_value) else False


def save_test_result(grade, score, total):
    """
    テスト結果をJSONファイルに保存
    Args:
        grade (int): 学年
        score (int): 正解数
        total (int): 総問題数
    """
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
    """学年を日本語表記に変換"""
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
    """過去の成績統計を表示"""
    try:
        with open('math_quiz_results.json', 'r') as f:
            results = [json.loads(line) for line in f]

        if not results:
            print("まだ記録がありません")
            return

        print("\n📊 あなたの成績 📊")
        print("---------------------")

        # 学年別統計
        grade_stats = defaultdict(list)
        for r in results:
            grade_stats[r['grade']].append(r['percentage'])

        for grade, percentages in sorted(grade_stats.items()):
            avg = sum(percentages) / len(percentages)
            print(f"{get_level_description(grade)}: 平均 {avg:.1f}% ({len(percentages)}回)")

        # 全体統計
        total_avg = sum(r['percentage'] for r in results) / len(results)
        print(f"\n全体平均: {total_avg:.1f}%")
        best = max(results, key=lambda x: x['percentage'])
        print(f"最高記録: {best['percentage']}% ({best['date']})")

    except FileNotFoundError:
        print("成績ファイルが見つかりません")


def run_math_quiz():
    """クイズのメインループ"""
    print("✨ 算数マスター ✨")
    print("---------------------")

    # 学年選択
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
        question, answer = generate_math_question(grade)
        print(f"問題 {q_num}: {question}")

        attempts = 0
        max_attempts = 2

        while attempts < max_attempts:
            user_answer = input("答え: ").strip()

            if check_answer(user_answer, answer):
                print("正解！🎉\n")
                correct += 1
                break
            else:
                attempts += 1
                if attempts < max_attempts:
                    print("もう一度考えてみましょう！")
                else:
                    print(f"正解は {answer} でした\n")

    # 結果表示
    percentage = correct / question_count * 100
    print("\n⭐️ 結果 ⭐️")
    print(f"正解数: {correct}/{question_count}")
    print(f"得点率: {percentage:.1f}%")

    # 成績保存
    save_test_result(grade, correct, question_count)
    show_statistics()


def main():
    """プログラムのエントリーポイント"""
    while True:
        run_math_quiz()

        # 続けるか確認
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