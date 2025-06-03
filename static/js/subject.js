// 科目選択関数
function selectSubject(subject) {
    const button = event.target;
    const soundWave = button.querySelector('.sound-wave');

    // クリック効果
    button.classList.add('clicked');
    if (soundWave) {
        soundWave.classList.add('active');
    }

    // ボタンを一時的に無効化
    button.disabled = true;

    // 効果音の視覚的表現をリセット
    setTimeout(() => {
        button.classList.remove('clicked');
        if (soundWave) {
            soundWave.classList.remove('active');
        }
    }, 300);

    // 科目選択の処理
    setTimeout(() => {
        alert(`${subject}の冒険を始めます！\n準備はいいですか？`);

        // ここで実際のページ遷移やコンテンツ表示の処理を行う
        console.log(`選択された科目: ${subject}`);

        // 実際の遷移例（コメントアウト）
        // window.location.href = `${subject.toLowerCase()}.html`;

        // ボタンを再有効化
        button.disabled = false;
    }, 500);
}

// ページ読み込み時の初期化
window.addEventListener('load', () => {
    // ボタンの段階的表示
    const buttons = document.querySelectorAll('.subject-btn');
    buttons.forEach((btn, index) => {
        setTimeout(() => {
            btn.style.opacity = '1';
            btn.style.transform = 'translateY(0)';
        }, 300 * (index + 1));
    });

    // ウェルカムメッセージ（オプション）
    setTimeout(() => {
        console.log('🎮 RPG学習サイトへようこそ！');
        console.log('キーボードの矢印キーでナビゲーション、EnterまたはSpaceで選択できます。');
    }, 1000);
});

// キーボードナビゲーション
document.addEventListener('keydown', (e) => {
    const buttons = document.querySelectorAll('.subject-btn');
    let currentIndex = Array.from(buttons).findIndex(btn => btn === document.activeElement);

    switch(e.key) {
        case 'ArrowLeft':
            e.preventDefault();
            currentIndex = currentIndex > 0 ? currentIndex - 1 : buttons.length - 1;
            buttons[currentIndex].focus();
            break;

        case 'ArrowRight':
            e.preventDefault();
            currentIndex = currentIndex < buttons.length - 1 ? currentIndex + 1 : 0;
            buttons[currentIndex].focus();
            break;

        case 'ArrowUp':
        case 'ArrowDown':
            e.preventDefault();
            // 縦方向のナビゲーション（モバイル対応）
            if (window.innerWidth <= 768) {
                if (e.key === 'ArrowUp') {
                    currentIndex = currentIndex > 0 ? currentIndex - 1 : buttons.length - 1;
                } else {
                    currentIndex = currentIndex < buttons.length - 1 ? currentIndex + 1 : 0;
                }
                buttons[currentIndex].focus();
            }
            break;

        case 'Enter':
        case ' ':
            if (document.activeElement && document.activeElement.classList.contains('subject-btn')) {
                e.preventDefault();
                document.activeElement.click();
            }
            break;

        case 'Escape':
            // フォーカスを外す
            if (document.activeElement) {
                document.activeElement.blur();
            }
            break;
    }
});

// タッチデバイス対応
document.addEventListener('touchstart', (e) => {
    // タッチ開始時の処理
    if (e.target.classList.contains('subject-btn')) {
        e.target.style.transform = 'scale(0.95)';
    }
});

document.addEventListener('touchend', (e) => {
    // タッチ終了時の処理
    if (e.target.classList.contains('subject-btn')) {
        setTimeout(() => {
            e.target.style.transform = '';
        }, 100);
    }
});

// ウィンドウリサイズ対応
window.addEventListener('resize', () => {
    // レスポンシブ対応の追加処理があれば記述
    console.log(`画面サイズ: ${window.innerWidth} x ${window.innerHeight}`);
});

// デバッグ用関数
function debugInfo() {
    console.log('=== RPG学習サイト デバッグ情報 ===');
    console.log(`画面サイズ: ${window.innerWidth} x ${window.innerHeight}`);
    console.log(`ユーザーエージェント: ${navigator.userAgent}`);
    console.log(`タッチデバイス: ${('ontouchstart' in window) ? 'Yes' : 'No'}`);
    console.log('=====================================');
}

// エラーハンドリング
window.addEventListener('error', (e) => {
    console.error('エラーが発生しました:', e.error);
});

// 開発者向け：コンソールでdebugInfo()を呼び出せるようにグローバルに設定
window.debugInfo = debugInfo;