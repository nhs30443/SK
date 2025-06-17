// ステージボタンの配置座標（パーセンテージ）- 800x600マップに対する相対位置
const stagePositions = [
    {x: 23.0, y: 27.17}, // 184/800 * 100, 163/600 * 100
    {x: 38.0, y: 29.5},  // 304/800 * 100, 177/600 * 100
    {x: 52.0, y: 26.17}, // 416/800 * 100, 157/600 * 100
    {x: 67.38, y: 20.83}, // 539/800 * 100, 125/600 * 100
    {x: 76.38, y: 67.17}, // 611/800 * 100, 403/600 * 100
    {x: 83.13, y: 33.5},  // 665/800 * 100, 201/600 * 100
    {x: 62.25, y: 52.0},  // 498/800 * 100, 312/600 * 100
    {x: 49.0, y: 60.0},   // 392/800 * 100, 360/600 * 100
    {x: 31.0, y: 45.83},  // 248/800 * 100, 275/600 * 100
    {x: 19.5, y: 57.33}   // 156/800 * 100, 344/600 * 100
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

        // パーセンテージで位置を設定
        button.style.left = stagePositions[i].x + '%';
        button.style.top = stagePositions[i].y + '%';
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

// ウィンドウリサイズ時の処理は削除
// updateButtonSizes関数も削除

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