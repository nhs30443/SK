// グローバル変数
let currentQuestion = null;
let isAnswering = false;

// プレイヤーの最大HPと現在HP
const maxPlayerHP = 40;
let playerHP = 40;

// 敵の最大HPと現在HP
const maxEnemyHP = 120;
let enemyHP = 120;

let battleEnded = false;

function getHPColor(hpPercent) {
    if (hpPercent > 50) {
        return '#00cc00';  // 緑
    } else if (hpPercent > 25) {
        return '#ffcc00';  // 黄
    } else {
        return '#e60000';  // 赤
    }
}

// 問題を読み込む関数
async function loadQuestion() {
    console.log('新しい問題を読み込んでいます...');

    // 問題読み込み中の表示
    $('#question-text').text('問題を読み込み中...');
    $('.choice').text('').removeClass('correct incorrect disabled');

    try {
        const subject = window.currentSubject || 'math';
        console.log('科目:', subject);

        const response = await fetch(`/api/generate-question/${subject}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const questionData = await response.json();
        console.log('問題データを受信:', questionData);

        currentQuestion = questionData;

        // 問題を画面に表示
        displayQuestion(questionData);

        console.log('問題の表示が完了しました');

    } catch (error) {
        console.error('問題読み込みエラー:', error);
        // エラー時はフォールバック問題を表示
        displayFallbackQuestion();
    }
}

// 問題を画面に表示する関数
function displayQuestion(questionData) {
    console.log('問題を表示します:', questionData);

    // 問題文を表示
    $('#question-text').text(questionData.question);

    // 選択肢を表示
    $('.choice').each(function(index) {
        $(this).text(questionData.choices[index]);
        $(this).removeClass('correct incorrect disabled');
        $(this).css({
            'pointer-events': 'auto',
            'opacity': '1'
        });
    });

    // 結果表示エリアを非表示
    $('#result-box').hide();
    $('.next-question-container').hide();

    // 回答状態をリセット
    isAnswering = false;

    console.log('問題表示完了');
}

// フォールバック問題を表示する関数
function displayFallbackQuestion() {
    const fallbackQuestion = {
        question: "5 + 3 = ?",
        choices: ["6", "7", "8", "9"],
        correct_answer: 2,
        explanation: "5に3を足すと8になります。"
    };

    currentQuestion = fallbackQuestion;
    displayQuestion(fallbackQuestion);
}

// 回答をチェックする関数
async function checkAnswer(selectedIndex) {
    if (!currentQuestion || isAnswering) return;

    isAnswering = true;

    const isCorrect = selectedIndex === currentQuestion.correct_answer;

    // 選択した選択肢をハイライト
    $('.choice').each(function(index) {
        if (index === selectedIndex) {
            $(this).addClass(isCorrect ? 'correct' : 'incorrect');
        }
        $(this).css('pointer-events', 'none');
    });

    // 正解の選択肢をハイライト（間違った場合）
    if (!isCorrect) {
        $('.choice').eq(currentQuestion.correct_answer).addClass('correct');
    }

    // 結果メッセージを表示
    const resultMessage = isCorrect ?
        `正解です！${currentQuestion.explanation}` :
        `不正解です。正解は「${currentQuestion.choices[currentQuestion.correct_answer]}」です。${currentQuestion.explanation}`;

    $('#result-box').text(resultMessage).fadeIn();

    // HPの更新（戦闘終了判定も含む）
    if (isCorrect) {
        // 正解時は敵にダメージ
        updateEnemyHP(-20);
        // HPアニメーション完了後に次の問題ボタンを表示
        $('#enemy-hp').one('transitionend', function() {
            showNextQuestionButton();
        });
        // transitionendが発火しない場合のフォールバック
        setTimeout(showNextQuestionButton, 1000);
    } else {
        // 不正解時はプレイヤーにダメージ
        updatePlayerHP(-10);
        // HPアニメーション完了後に次の問題ボタンを表示
        $('#player-hp').one('transitionend', function() {
            showNextQuestionButton();
        });
        // transitionendが発火しない場合のフォールバック
        setTimeout(showNextQuestionButton, 1000);
    }
}

// 次の問題ボタンを表示する関数
function showNextQuestionButton() {
    if (!battleEnded) {
        console.log('次の問題ボタンを表示します');
        $('.next-question-container').fadeIn();
    }
}

$(document).ready(function () {
    // LocalStorageから復元（なければ初期値のまま）
    const savedPlayerHP = localStorage.getItem('playerHP');
    if (savedPlayerHP !== null) {
        playerHP = Number(savedPlayerHP);
    }

    const savedEnemyHP = localStorage.getItem('enemyHP');
    if (savedEnemyHP !== null) {
        enemyHP = Number(savedEnemyHP);
    }

    updatePlayerHP(0);  // 表示更新（変化量0で現在値反映）
    updateEnemyHP(0);

    // 初回問題読み込み
    loadQuestion();
});

function checkBattleEnd() {
    if (battleEnded) return;  // すでに終了してたら何もしない
    if (playerHP <= 0) {
        battleEnded = true;
        setTimeout(() => {
            alert("あなたはやられてしまいました…");
            // ゲームオーバー処理
            localStorage.removeItem('playerHP');
            localStorage.removeItem('enemyHP');
            window.location.href = '/map';  // マップ画面に戻る
        }, 1000);
    }
    if (enemyHP <= 0) {
        battleEnded = true;
        setTimeout(() => {
            alert("敵を倒しました！勝利です！");
            // 勝利処理
            localStorage.removeItem('playerHP');
            localStorage.removeItem('enemyHP');
            window.location.href = '/result';  // リザルト画面に移動
        }, 1000);
    }
}

function updatePlayerHP(amount) {
    playerHP = Math.max(0, Math.min(maxPlayerHP, playerHP + amount));
    const hpPercent = (playerHP / maxPlayerHP) * 100;
    $('#player-hp').css('width', hpPercent + '%');
    const color = getHPColor(hpPercent);
    $('#player-hp').css('background-color', color);

    localStorage.setItem('playerHP', playerHP);

    // HP更新後にバトル終了チェック（少し遅延させる）
    setTimeout(() => {
        checkBattleEnd();
    }, 300);
}

function updateEnemyHP(amount) {
    enemyHP = Math.max(0, Math.min(maxEnemyHP, enemyHP + amount));
    const hpPercent = (enemyHP / maxEnemyHP) * 100;
    $('#enemy-hp').css('width', hpPercent + '%');
    const color = getHPColor(hpPercent);
    $('#enemy-hp').css('background-color', color);

    localStorage.setItem('enemyHP', enemyHP);

    // HP更新後にバトル終了チェック（少し遅延させる）
    setTimeout(() => {
        checkBattleEnd();
    }, 300);
}

// 選択肢クリック時の処理
$(document).on('click', '.choice', function() {
    console.log('選択肢がクリックされました');
    console.log('battleEnded:', battleEnded);
    console.log('isAnswering:', isAnswering);

    if (battleEnded || isAnswering) {
        console.log('クリックを無視します');
        return;
    }

    const selectedIndex = parseInt($(this).data('index'));
    console.log('選択されたインデックス:', selectedIndex);

    checkAnswer(selectedIndex);
});

// 次の問題ボタンクリック時の処理
$(document).on('click', '#next-question-btn', function() {
    console.log('次の問題ボタンがクリックされました');

    if (battleEnded) {
        console.log('バトルが終了しているため、次の問題は読み込みません');
        return;
    }

    // ボタンを一時的に無効化
    $(this).prop('disabled', true).text('読み込み中...');

    // 次の問題ボタンを非表示
    $('.next-question-container').hide();

    // 新しい問題を読み込み
    loadQuestion().then(() => {
        // 読み込み完了後にボタンを再有効化
        $('#next-question-btn').prop('disabled', false).text('次の問題');
    }).catch(() => {
        // エラー時もボタンを再有効化
        $('#next-question-btn').prop('disabled', false).text('次の問題');
    });
});

// ハンバーガーメニューの処理
$(function() {
    $('#hamburger').on('click', function() {
        $(this).toggleClass("open");
        $('#header-menu').fadeToggle();
        $('#overlay').fadeToggle();
    });

    $('#overlay').on('click', function() {
        $('#hamburger').removeClass("open");
        $('#header-menu').fadeOut();
        $('#overlay').fadeOut();
    });
});