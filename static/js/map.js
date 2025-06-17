// ステージボタンの配置座標（固定）
const stagePositions = [
    {x: 184, y: 163}, {x: 304, y: 177}, {x: 416, y: 157}, {x: 539, y: 125}, {x: 611, y: 403},
    {x: 665, y: 201}, {x: 498, y: 312}, {x: 392, y: 360}, {x: 248, y: 275}, {x: 156, y: 344}
];

// ステージの状態（0: ロック, 1: 解放, 2: クリア済み）- 10個に調整
const stageStatus = [
    2, 2, 1, 1, 0, 0, 0, 0, 0, 0
];

// ステージボタンを生成
function createStageButtons() {
    const container = document.querySelector('.stage-buttons');
    container.innerHTML = '';

    for (let i = 0; i < 10; i++) {
        const stageNum = i + 1;
        const button = document.createElement('div');
        button.className = 'stage-button';
        button.style.left = stagePositions[i].x + 'px';
        button.style.top = stagePositions[i].y + 'px';
        button.dataset.index = i;

        // ステージの状態に応じてスタイルを設定
        if (stageStatus[i] === 0) {
            // ロック済み
            button.classList.add('locked');
            button.innerHTML = '<span class="lock-icon">🔒</span>';
        } else if (stageStatus[i] === 2) {
            // クリア済み
            button.classList.add('cleared');
            button.innerHTML = stageNum + '<div class="star-icon">⭐</div>';
        } else {
            // 解放済み
            button.innerHTML = stageNum;
        }

        // クリックイベントを追加（通常のゲームプレイ用）
        if (stageStatus[i] > 0) {
            button.onclick = () => selectStage(stageNum);
        }

        container.appendChild(button);
    }
}

// ステージ選択時の処理
function selectStage(stageNum) {
    if (confirm(`ステージ ${stageNum} を始めますか？`)) {
        // 実際のFlaskアプリケーションでは以下のようにリダイレクト
        // window.location.href = `/question?stage=${stageNum}`;
        alert(`ステージ ${stageNum} を開始します！`);
    }
}

// 戻るボタンの処理
function goBack() {
    // 実際のFlaskアプリケーションでは以下のようにリダイレクト
    // window.location.href = '/main';
    alert('メイン画面に戻ります');
}

// ページ読み込み時にステージボタンを生成
document.addEventListener('DOMContentLoaded', function() {
    // 背景画像を設定
    if (window.backgroundImageUrl) {
        const background = document.querySelector('.background');
        background.style.backgroundImage = `url('${window.backgroundImageUrl}')`;
    }

    // ステージボタンを生成
    createStageButtons();
});