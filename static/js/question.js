document.querySelectorAll('.choice').forEach(choice => {
    choice.addEventListener('click', () => {
        const text = `「${choice.textContent}」が選ばれました`;
        const resultBox = document.getElementById('result-box');
        $(resultBox).stop(true, true).text(text).fadeIn().delay(1500).fadeOut();
    });
});

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
});

function checkBattleEnd() {
    if (battleEnded) return;  // すでに終了してたら何もしない
    if (playerHP <= 0) {
        battleEnded = true;
        alert("あなたはやられてしまいました…");
        // ここにゲームオーバー処理やリセット処理など入れる
        $('.choice').off('click'); // 選択肢を無効化する例
        localStorage.removeItem('playerHP');
        localStorage.removeItem('enemyHP');

    }
    if (enemyHP <= 0) {
        battleEnded = true;
        alert("敵を倒しました！");
        // ここに勝利処理や次のステージ移動など入れる
        $('.choice').off('click'); // 選択肢を無効化する例
        localStorage.removeItem('playerHP');
        localStorage.removeItem('enemyHP');
    }
}

function updatePlayerHP(amount) {
    playerHP = Math.max(0, Math.min(maxPlayerHP, playerHP + amount));
    const hpPercent = (playerHP / maxPlayerHP) * 100;
    $('#player-hp').css('width', hpPercent + '%');
    $('#player-hp-text').text(`${playerHP} / ${maxPlayerHP}`);
    const color = getHPColor(hpPercent);
    $('#player-hp').css('background-color', color);

    localStorage.setItem('playerHP', playerHP);  // ← 追加

    $('#player-hp').one('transitionend', function() {
        checkBattleEnd();
    });
}

function updateEnemyHP(amount) {
    enemyHP = Math.max(0, Math.min(maxEnemyHP, enemyHP + amount));
    const hpPercent = (enemyHP / maxEnemyHP) * 100;
    $('#enemy-hp').css('width', hpPercent + '%');
    $('#enemy-hp-text').text(`${enemyHP} / ${maxEnemyHP}`);
    const color = getHPColor(hpPercent);
    $('#enemy-hp').css('background-color', color);

    localStorage.setItem('enemyHP', enemyHP);  // ← 追加

    $('#enemy-hp').one('transitionend', function() {
        checkBattleEnd();
    });
}


$('.choice').on('click', function () {
    if (battleEnded) return;

    battleEnded = true;

    const isCorrect = $(this).data('correct'); // true か false が入る

    if (isCorrect) {
        // 正解の処理
        updateEnemyHP(-20);
        checkBattleEnd();

        $('#enemy-hp').one('transitionend', function () {
            setTimeout(() => {
                updatePlayerHP(-10);

                // プレイヤーHP減少アニメ終了後にbattleEnded解除
                $('#player-hp').one('transitionend', function () {
                    battleEnded = false;
                    checkBattleEnd();
                });
            }, 1000);
        });
    } else {
        // 間違いの処理
        setTimeout(() => {
            updatePlayerHP(-10);

            $('#player-hp').one('transitionend', function () {
                battleEnded = false;
                checkBattleEnd();
            });
        }, 1000);
    }
});







