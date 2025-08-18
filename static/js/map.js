// ステージボタンの配置座標（パーセンテージ）- 800x600マップに対する相対位置
const stagePositions = [
    {x: 23.0, y: 27.17}, // 184/800 * 100, 163/600 * 100
    {x: 19.5, y: 57.33},  // 156/800 * 100, 344/600 * 100
    {x: 31.0, y: 45.83},  // 248/800 * 100, 275/600 * 100
    {x: 38.0, y: 29.5},  // 304/800 * 100, 177/600 * 100
    {x: 52.0, y: 26.17}, // 416/800 * 100, 157/600 * 100
    {x: 67.38, y: 20.83}, // 539/800 * 100, 125/600 * 100
    {x: 83.13, y: 33.5},  // 665/800 * 100, 201/600 * 100
    {x: 62.25, y: 52.0},  // 498/800 * 100, 312/600 * 100
    {x: 49.0, y: 60.0},   // 392/800 * 100, 360/600 * 100
    {x: 76.38, y: 67.17}, // 611/800 * 100, 403/600 * 100
];

// ステージの状態（0: ロック, 1: 解放, 2: クリア済み）- 10個に調整
const stageStatus = window.stageStatus;

// モーダル要素を作成
function createModal() {
    const modalHTML = `
        <div class="modal-overlay" id="stageModal">
            <div class="modal-content">
                <div class="modal-stage-icon" id="modalStageIcon"></div>
                <div class="modal-title" id="modalTitle">ステージを開始</div>
                <div class="modal-message" id="modalMessage">このステージに挑戦しますか？</div>
                <div class="modal-buttons">
                    <button class="modal-btn start" id="startBtn">開始</button>
                    <button class="modal-btn cancel" id="cancelBtn">キャンセル</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // イベントリスナーを追加
    const modal = document.getElementById('stageModal');
    const startBtn = document.getElementById('startBtn');
    const cancelBtn = document.getElementById('cancelBtn');

    // キャンセルボタン
    cancelBtn.addEventListener('click', hideModal);

    // モーダル外をクリックして閉じる
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            hideModal();
        }
    });

    // ESCキーで閉じる
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            hideModal();
        }
    });
}

// モーダルを表示
function showModal(stageNum) {
    const modal = document.getElementById('stageModal');
    const modalStageIcon = document.getElementById('modalStageIcon');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const startBtn = document.getElementById('startBtn');

    // ステージの状態に応じて表示を変更
    const stageIndex = stageNum - 1;
    const status = stageStatus[stageIndex];

    modalStageIcon.textContent = stageNum;
    modalStageIcon.className = 'modal-stage-icon';

    if (status === 2) {
        modalStageIcon.classList.add('cleared');
        modalTitle.textContent = `ステージ ${stageNum} (クリア済み)`;
        modalMessage.textContent = 'このステージは既にクリア済みです。もう一度挑戦しますか？';
    } else {
        modalTitle.textContent = `ステージ ${stageNum}`;
        modalMessage.textContent = 'このステージに挑戦しますか？';
    }

    // 開始ボタンのイベントを設定
    startBtn.onclick = () => {
        hideModal();
        startStage(stageNum);
    };

    modal.classList.add('show');
}

// モーダルを非表示
function hideModal() {
    const modal = document.getElementById('stageModal');
    modal.classList.remove('show');
}

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
            button.onclick = () => showModal(stageNum);
        }

        container.appendChild(button);
    }
}

// ステージ開始処理
function startStage(stageNum) {
    // アニメーション効果を追加
    const container = document.querySelector('.container');
    container.style.transform = 'scale(0.95)';
    container.style.opacity = '0.8';
    container.style.transition = 'all 0.3s ease';

    setTimeout(() => {
        // 実際のFlaskアプリケーションでリダイレクト
        window.location.href = `/question?stage=${stageNum}`;
    }, 300);
}

// 戻るボタンの処理
function goBack() {
    const container = document.querySelector('.container');
    container.style.transform = 'scale(1.05)';
    container.style.opacity = '0.8';
    container.style.transition = 'all 0.2s ease';

    setTimeout(() => {
        // 実際のFlaskアプリケーションでリダイレクト
        window.location.href = '/main';
    }, 200);
}

// ページ読み込み時にステージボタンを生成
document.addEventListener('DOMContentLoaded', function() {
    // 背景画像を設定
    if (window.backgroundImageUrl) {
        const background = document.querySelector('.background');
        background.style.backgroundImage = `url('${window.backgroundImageUrl}')`;
    }

    // モーダルを作成
    createModal();

    // ステージボタンを生成
    createStageButtons();
});