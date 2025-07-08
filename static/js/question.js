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
    try {
        const subject = window.currentSubject || 'math';
        const response = await fetch(`/api/generate-question/${subject}`);
        
        if (!response.ok) {
            throw new Error('問題の取得に失敗しました');
        }
        
        const questionData = await response.json();
        currentQuestion = questionData;
        
        // 問題を画面に表示
        displayQuestion(questionData);
        
    } catch (error) {
        console.error('問題読み込みエラー:', error);
        // エラー時はフォールバック問題を表示
        displayFallbackQuestion();
    }
}

// 問題を画面に表示する関数
function displayQuestion(questionData) {
    // 問題文を表示
    $('#question-text').text(questionData.question);
    
    // 選択肢を表示
    $('.choice').each(function(index) {
        $(this).text(questionData.choices[index]);
        $(this).removeClass('correct incorrect disabled');
        $(this).css('pointer-events', 'auto');
    });
    
    // 結果表示エリアを非表示
    $('#result-box').hide();
    $('.next-question-container').hide();
    
    isAnswering = false;
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
    
    // HPの更新
    if (isCorrect) {
        // 正解時は敵にダメージ
        updateEnemyHP(-20);
    } else {
        // 不正解時はプレイヤーにダメージ
        updatePlayerHP(-10);
    }
    
    // 少し待ってから次の問題ボタンを表示
    setTimeout(() => {
        if (!battleEnded) {
            $('.next-question-container').fadeIn();
        }
    }, 2000);
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

    $('#player-hp').one('transitionend', function() {
        checkBattleEnd();
    });
}

function updateEnemyHP(amount) {
    enemyHP = Math.max(0, Math.min(maxEnemyHP, enemyHP + amount));
    const hpPercent = (enemyHP / maxEnemyHP) * 100;
    $('#enemy-hp').css('width', hpPercent + '%');
    const color = getHPColor(hpPercent);
    $('#enemy-hp').css('background-color', color);

    localStorage.setItem('enemyHP', enemyHP);

    $('#enemy-hp').one('transitionend', function() {
        checkBattleEnd();
    });
}

// 選択肢クリック時の処理
$(document).on('click', '.choice', function() {
    if (battleEnded || isAnswering) return;
    
    const selectedIndex = parseInt($(this).data('index'));
    checkAnswer(selectedIndex);
});

// 次の問題ボタンクリック時の処理
$(document).on('click', '#next-question-btn', function() {
    if (battleEnded) return;
    
    loadQuestion();
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