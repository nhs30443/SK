// グローバル変数
let currentQuestion = null;
let isAnswering = false;
let questionCount = 0; // 問題数をカウント

// プレイヤーのパラメータ
const maxPlayerHP = 40;
let playerHP = 40;

// 敵のパラメータ
const maxEnemyHP = window.enemyData?.hp ?? 100;
let enemyHP = window.enemyData?.hp ?? 100;
const EnemyAT = window.enemyData?.attack ?? -10;

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


$(document).ready(function() {
    if (startPhase === "move_select") {
        // 行動選択フェーズ表示
        $('#move-select-area').show();
        $('#quiz-area').hide();
        $('#subject-area').hide();
        $('#item-area').hide();
    }
});



// 問題を読み込む関数（改善版）
async function loadQuestion() {
    console.log(`新しい問題を読み込んでいます... (問題数: ${questionCount + 1})`);

    // 問題読み込み中の表示
    $('#question-text').text('問題を読み込み中...');
    $('.choice').text('').removeClass('correct incorrect disabled');

    const subject = window.currentSubject || 'math';
    console.log('科目:', subject);

    // 最大再試行回数
    const maxRetries = 3;
    let retryCount = 0;

    while (retryCount < maxRetries) {
        try {
            // キャッシュを避けるためにタイムスタンプを追加
            const timestamp = new Date().getTime();
            const response = await fetch(`/api/generate-question/${subject}?t=${timestamp}&retry=${retryCount}`, {
                method: 'GET',
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const questionData = await response.json();
            console.log('問題データを受信:', questionData);

            // レスポンスの検証
            if (!questionData || !questionData.question || !questionData.choices) {
                throw new Error('無効な問題データを受信しました');
            }

            // 同じ問題かチェック（簡易版）
            if (currentQuestion && currentQuestion.question === questionData.question) {
                console.warn('同じ問題が生成されました。再試行します...');
                retryCount++;
                if (retryCount < maxRetries) {
                    // 1秒待ってから再試行
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    continue;
                }
            }

            currentQuestion = questionData;
            questionCount++;

            // 問題を画面に表示
            displayQuestion(questionData);

            console.log(`問題の表示が完了しました (問題数: ${questionCount})`);
            return; // 成功時は関数を終了

        } catch (error) {
            console.error(`問題読み込みエラー (試行 ${retryCount + 1}/${maxRetries}):`, error);
            retryCount++;

            if (retryCount < maxRetries) {
                console.log(`${retryCount + 1}回目の再試行を行います...`);
                // 再試行前に少し待機
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
    }

    // すべての再試行が失敗した場合
    console.error('すべての再試行が失敗しました。フォールバック問題を表示します。');
    displayFallbackQuestion();
}

// 問題を画面に表示する関数
function displayQuestion(questionData) {
    console.log('問題を表示します:', questionData);

    // 問題文を表示（問題番号も追加）
    $('#question-text').text(`問題${questionCount}: ${questionData.question}`);

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

// フォールバック問題を表示する関数（改善版）
function displayFallbackQuestion() {
    const fallbackQuestions = {
        math: [
            {
                question: "8 + 5 = ?",
                choices: ["11", "12", "13", "14"],
                correct_answer: 2,
                explanation: "8に5を足すと13になります。"
            },
            {
                question: "15 - 7 = ?",
                choices: ["6", "7", "8", "9"],
                correct_answer: 2,
                explanation: "15から7を引くと8になります。"
            }
        ],
        kanji: [
            {
                question: "「つき」を漢字で書くとどれですか？",
                choices: ["日", "月", "星", "空"],
                correct_answer: 1,
                explanation: "「つき」は「月」と書きます。"
            }
        ],
        english: [
            {
                question: "「本」を英語で言うとどれですか？",
                choices: ["pen", "book", "desk", "chair"],
                correct_answer: 1,
                explanation: "「本」は英語で「book」です。"
            }
        ]
    };

    const subject = window.currentSubject || 'math';
    const subjectQuestions = fallbackQuestions[subject] || fallbackQuestions.math;
    const randomQuestion = subjectQuestions[Math.floor(Math.random() * subjectQuestions.length)];

    currentQuestion = randomQuestion;
    questionCount++;
    displayQuestion(randomQuestion);
}

// 回答をチェックする関数
async function checkAnswer(selectedIndex) {
    if (!currentQuestion || isAnswering) return;

    isAnswering = true;

    const isCorrect = selectedIndex === currentQuestion.correct_answer;

    // 回答結果を記録（科目名と正誤をlocalStorageに保存）
    const subject = window.currentSubject; 
    recordAnswer(subject, isCorrect);

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
        updateEnemyHP(PlayerAT);
        // 2秒後に敵からの反撃
        setTimeout(() => {
            if (!battleEnded) { // 戦闘が終わってなければ攻撃
                updatePlayerHP(EnemyAT);
            }
        }, 1000);
        // HPアニメーション完了後に次の問題ボタンを表示
        $('#enemy-hp').one('transitionend', function() {
            showNextQuestionButton();
        });
        // transitionendが発火しない場合のフォールバック
        setTimeout(showNextQuestionButton, 1000);
    } else {
        // 2秒後に敵からの反撃
        setTimeout(() => {
            if (!battleEnded) { // 戦闘が終わってなければ攻撃
                updatePlayerHP(EnemyAT);
            }
        }, 1000);
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

$(document).ready(async function () {
    // LocalStorageから復元（なければ初期値のまま）
    const savedPlayerHP = localStorage.getItem('playerHP');
    if (savedPlayerHP !== null) {
        playerHP = Number(savedPlayerHP);
    }

    const savedEnemyHP = localStorage.getItem('enemyHP');
    if (savedEnemyHP !== null) {
        enemyHP = Number(savedEnemyHP);
    }

    // 問題数をリセット
    questionCount = 0;

    updatePlayerHP(0);  // 表示更新（変化量0で現在値反映）
    updateEnemyHP(0);

    // 初回問題読み込み
    try {
        await loadQuestion();
        console.log('初回問題の読み込みが完了しました');
    } catch (error) {
        console.error('初回問題の読み込みでエラーが発生しました:', error);
        displayFallbackQuestion();
    }
});

function checkBattleEnd() {
    if (battleEnded) return;  // すでに終了してたら何もしない
    if (playerHP <= 0) {
        battleEnded = true;
        setTimeout(() => {
            // ゲームオーバー処理
            localStorage.clear();
            window.location.href = '/gameover';
        }, 1000);
    }
    if (enemyHP <= 0) {
        battleEnded = true;
        setTimeout(() => {
            // 勝利処理
            const answerHistory = localStorage.getItem('answerHistory') || '{}';
            const data = {
                history: answerHistory,
            };

            postAndRedirect('/result', data);
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

// 次の問題ボタンクリック時の処理（修正版）
$(document).on('click', '#next-question-btn', async function() {
    console.log('次の問題ボタンがクリックされました');

    if (battleEnded) {
        console.log('バトルが終了しているため、次の問題は読み込みません');
        return;
    }

    // ボタンを一時的に無効化
    $(this).prop('disabled', true).text('読み込み中...');

    // 次の問題ボタンを非表示
    $('.next-question-container').hide();

    try {
        $('#quiz-area').hide();
        $('#move-select-area').show();
    } catch (error) {
        console.error('次の問題の読み込みでエラーが発生しました:', error);
        // エラー時はフォールバック問題を表示
        displayFallbackQuestion();
    } finally {
        // 読み込み完了後にボタンを再有効化
        $('#next-question-btn').prop('disabled', false).text('次の問題');
    }
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





function selectMovement(action) {
    console.log('選択された行動:', action);

    if (action === 'attack') {
        $('#move-select-area').hide();
        $('#subject-area').show();
    } else if (action === 'item') {
        $('#move-select-area').hide();
        $('#item-area').show();
    }
}


function closeItemModal() {
    $('#item-area').hide();
    $('#move-select-area').show();
}


function selectItem(item) {
    console.log('選択されたアイテム:', item);

    if (item === '1') {

        $('#item-area').hide();
        $('#move-select-area').show();
    } else if (item === '2') {

        $('#item-area').hide();
        $('#move-select-area').show();
    } else if (item === '3') {

        $('#item-area').hide();
        $('#move-select-area').show();
    } else if (item === '4') {

        $('#item-area').hide();
        $('#move-select-area').show();
    } else if (item === '5') {

        $('#item-area').hide();
        $('#move-select-area').show();
    } else if (item === '6') {

        $('#item-area').hide();
        $('#move-select-area').show();
    }
}





// 回答結果を保存（subject: 科目名, isCorrect: true/false）
function recordAnswer(subject, isCorrect) {
    // 既存データを取得（なければ初期化）
    let data = localStorage.getItem('answerHistory');
    data = data ? JSON.parse(data) : { subjects: {} };

    // 科目別のカウント
    if (!data.subjects[subject]) {
        data.subjects[subject] = { correct: 0, total: 0 };
    }
    data.subjects[subject].total++;
    if (isCorrect) data.subjects[subject].correct++;

    // 保存
    localStorage.setItem('answerHistory', JSON.stringify(data));
}



function postAndRedirect(url, data) {
    // localStorageの全削除
    localStorage.clear();

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;

    // データをhiddenフィールドでセット
    for (const key in data) {
        if (data.hasOwnProperty(key)) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = data[key];
            form.appendChild(input);
        }
    }

    document.body.appendChild(form);
    form.submit();
}