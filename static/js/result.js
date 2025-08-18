// result.js - 結果画面専用JavaScript

// グローバル変数
let statsCache = null;
let lastStatsUpdate = 0;
const STATS_CACHE_DURATION = 30000; // 30秒

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('結果画面を初期化中...');

    // 初期アニメーション実行
    initializeAnimations();

    // 統計データの初期ロード
    loadUserStats();

    // デバッグモードの初期化
    initializeDebugMode();

    console.log('結果画面の初期化完了');
});

// 初期アニメーション
function initializeAnimations() {
    // スコア行のアニメーション
    const scoreRows = document.querySelectorAll('.score-row');
    scoreRows.forEach((row, index) => {
        // 初期状態を設定
        row.style.opacity = '0';
        row.style.transform = 'translateX(-30px)';

        // 順次アニメーション実行
        setTimeout(() => {
            row.style.transition = 'all 0.6s ease-out';
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, index * 150 + 500); // 0.5秒後から開始
    });

    // ランクグレードのアニメーション
    const rankGrade = document.querySelector('.rank-grade');
    if (rankGrade) {
        rankGrade.style.opacity = '0';
        rankGrade.style.transform = 'scale(0.5)';

        setTimeout(() => {
            rankGrade.style.transition = 'all 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
            rankGrade.style.opacity = '1';
            rankGrade.style.transform = 'scale(1)';
        }, 1000);
    }

    // 統計アイテムのアニメーション
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(30px)';

        setTimeout(() => {
            item.style.transition = 'all 0.6s ease-out';
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, index * 200 + 1500);
    });
}

// ランクに応じた効果音（将来の拡張用）
function playRankSound(rank) {
    // 効果音の処理をここに追加可能
    console.log(`Rank achieved: ${rank}`);

    // ランクに応じた視覚効果
    const rankElement = document.querySelector('.rank-grade');
    if (rankElement && rank === 'S') {
        // Sランクの特別エフェクト
        rankElement.style.animation = 'rankPulse 0.5s ease-in-out 3';
        rankElement.style.textShadow = '0 0 20px gold, 0 0 40px gold';
    }
}

// 統計データの動的更新
async function loadUserStats() {
    const now = Date.now();

    // キャッシュが有効な場合はスキップ
    if (statsCache && (now - lastStatsUpdate) < STATS_CACHE_DURATION) {
        console.log('統計データをキャッシュから使用');
        return statsCache;
    }

    try {
        console.log('統計データを取得中...');
        const response = await fetch('/api/user-stats', {
            method: 'GET',
            cache: 'no-cache'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const stats = await response.json();
        console.log('最新統計データ:', stats);

        // キャッシュを更新
        statsCache = stats;
        lastStatsUpdate = now;

        // 必要に応じて画面の更新
        updateStatsDisplay(stats);

        return stats;

    } catch (error) {
        console.error('統計データの取得に失敗:', error);
        return null;
    }
}

// 統計表示の更新
function updateStatsDisplay(stats) {
    // ヘッダーの統計情報を更新（存在する場合）
    const statsElement = document.getElementById('current-stats');
    if (statsElement && stats.user_summary) {
        statsElement.innerHTML = `
            <span class="stat-item-mini">
                <i class="icon-questions"></i>
                総問題数: ${stats.user_summary.total_questions}
            </span>
            <span class="stat-item-mini">
                <i class="icon-accuracy"></i>
                正答率: ${stats.user_summary.accuracy_30_days}%
            </span>
        `;
    }

    // トレンドデータの更新（存在する場合）
    updateTrendsDisplay(stats);
}

// トレンド表示の更新
function updateTrendsDisplay(stats) {
    const trendsSection = document.querySelector('.trends-section');
    if (!trendsSection || !stats) return;

    // 各期間の統計を更新
    const periods = [
        { key: 'last_7_days', selector: '.trend-item:nth-child(1) .trend-score', label: '7日間' },
        { key: 'last_30_days', selector: '.trend-item:nth-child(2) .trend-score', label: '30日間' },
        { key: 'all_time', selector: '.trend-item:nth-child(3) .trend-score', label: '全期間' }
    ];

    periods.forEach(period => {
        const element = document.querySelector(period.selector);
        if (element && stats[period.key]) {
            const accuracy = calculateOverallAccuracy(stats[period.key]);
            element.textContent = `${accuracy}%`;

            // 数値に応じて色を変更
            if (accuracy >= 80) {
                element.style.color = '#00cc00';
            } else if (accuracy >= 60) {
                element.style.color = '#ffcc00';
            } else {
                element.style.color = '#e60000';
            }
        }
    });
}

// 全体正答率の計算
function calculateOverallAccuracy(subjectStats) {
    if (!subjectStats || Object.keys(subjectStats).length === 0) return 0;

    let totalQuestions = 0;
    let totalCorrect = 0;

    Object.values(subjectStats).forEach(stats => {
        totalQuestions += stats.total_questions || 0;
        totalCorrect += stats.correct_answers || 0;
    });

    return totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;
}

// テストデータ追加関数
async function addTestData() {
    try {
        showLoading('テストデータを追加中...');

        const response = await fetch('/api/add-test-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('テストデータ追加成功:', result);

        showSuccess('テストデータを追加しました');

        // 統計キャッシュをクリア
        statsCache = null;

        // ページをリロードして結果を反映
        setTimeout(() => {
            location.reload();
        }, 1500);

    } catch (error) {
        console.error('テストデータ追加エラー:', error);
        showError('テストデータの追加に失敗しました');
    } finally {
        hideLoading();
    }
}

// 統計リセット関数
async function resetStats() {
    if (!confirm('統計データをリセットしますか？この操作は元に戻せません。')) {
        return;
    }

    try {
        showLoading('統計データをリセット中...');

        const response = await fetch('/api/reset-stats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('統計リセット成功:', result);

        showSuccess('統計データをリセットしました');

        // 統計キャッシュをクリア
        statsCache = null;

        // ページをリロードして結果を反映
        setTimeout(() => {
            location.reload();
        }, 1500);

    } catch (error) {
        console.error('統計リセットエラー:', error);
        showError('統計リセットに失敗しました');
    } finally {
        hideLoading();
    }
}

// 統計更新関数
async function updateStats() {
    try {
        showLoading('統計データを更新中...');

        // キャッシュを強制クリア
        statsCache = null;
        lastStatsUpdate = 0;

        // 最新データを取得
        const stats = await loadUserStats();

        if (stats) {
            showSuccess('統計データを更新しました');
        } else {
            showError('統計データの更新に失敗しました');
        }

    } catch (error) {
        console.error('統計更新エラー:', error);
        showError('統計データの更新に失敗しました');
    } finally {
        hideLoading();
    }
}

// デバッグモードの初期化
function initializeDebugMode() {
    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.get('debug') === 'true') {
        console.log('デバッグモードを有効化');
        createDebugPanel();
    }
}

// デバッグパネルの作成
function createDebugPanel() {
    const debugPanel = document.createElement('div');
    debugPanel.id = 'debug-panel';
    debugPanel.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 15px;
        border-radius: 10px;
        font-family: monospace;
        font-size: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    `;

    debugPanel.innerHTML = `
        <div style="margin-bottom: 10px; font-weight: bold; color: #00ff00;">
            🔧 Debug Panel
        </div>
        <button onclick="addTestData()" style="margin: 3px; padding: 8px 12px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
            📊 テストデータ追加
        </button>
        <button onclick="resetStats()" style="margin: 3px; padding: 8px 12px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
            🗑️ 統計リセット
        </button>
        <button onclick="updateStats()" style="margin: 3px; padding: 8px 12px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
            🔄 統計更新
        </button>
        <button onclick="toggleDebugInfo()" style="margin: 3px; padding: 8px 12px; background: #FF9800; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
            📋 詳細情報
        </button>
        <div id="debug-info" style="margin-top: 10px; font-size: 10px; color: #ccc; display: none;">
            <div>Cache Status: <span id="cache-status">-</span></div>
            <div>Last Update: <span id="last-update">-</span></div>
            <div>User Agent: <span id="user-agent">${navigator.userAgent.substring(0, 30)}...</span></div>
        </div>
    `;

    document.body.appendChild(debugPanel);

    // キャッシュ状態の更新
    updateDebugInfo();

    // 定期的にデバッグ情報を更新
    setInterval(updateDebugInfo, 5000);
}

// デバッグ情報の更新
function updateDebugInfo() {
    const cacheStatusEl = document.getElementById('cache-status');
    const lastUpdateEl = document.getElementById('last-update');

    if (cacheStatusEl) {
        cacheStatusEl.textContent = statsCache ? '✅ Cached' : '❌ No Cache';
    }

    if (lastUpdateEl) {
        lastUpdateEl.textContent = lastStatsUpdate > 0 ?
            new Date(lastStatsUpdate).toLocaleTimeString() : 'Never';
    }
}

// デバッグ詳細情報の表示切り替え
function toggleDebugInfo() {
    const debugInfo = document.getElementById('debug-info');
    if (debugInfo) {
        debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
    }
}

// 通知システム
function showLoading(message = 'Loading...') {
    removeNotifications();

    const loading = document.createElement('div');
    loading.className = 'notification loading';
    loading.innerHTML = `
        <div class="notification-content">
            <div class="spinner"></div>
            <span>${message}</span>
        </div>
    `;

    addNotificationStyles();
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.querySelector('.notification.loading');
    if (loading) {
        loading.remove();
    }
}

function showSuccess(message) {
    showNotification(message, 'success', '✅');
}

function showError(message) {
    showNotification(message, 'error', '❌');
}

function showNotification(message, type, icon) {
    removeNotifications();

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icon}</span>
            <span class="notification-message">${message}</span>
        </div>
    `;

    addNotificationStyles();
    document.body.appendChild(notification);

    // 自動で削除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }
    }, 3000);
}

function removeNotifications() {
    document.querySelectorAll('.notification').forEach(n => n.remove());
}

// 通知用スタイルの追加
function addNotificationStyles() {
    if (document.getElementById('notification-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'notification-styles';
    styles.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10001;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: notificationSlideIn 0.3s ease-out;
            transition: opacity 0.3s ease;
        }
        
        .notification.success {
            background: linear-gradient(135deg, #4CAF50, #45a049);
        }
        
        .notification.error {
            background: linear-gradient(135deg, #f44336, #d32f2f);
        }
        
        .notification.loading {
            background: linear-gradient(135deg, #2196F3, #1976D2);
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes notificationSlideIn {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;

    document.head.appendChild(styles);
}

// 定期的な統計更新（オプション）
setInterval(async function() {
    // バックグラウンドで統計を更新（ユーザーに通知しない）
    try {
        await loadUserStats();
    } catch (error) {
        console.error('バックグラウンド統計更新エラー:', error);
    }
}, 60000); // 1分ごと

// ページの可視性変更時の処理
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // ページが再表示された時に統計を更新
        loadUserStats();
    }
});

// エラーハンドリング
window.addEventListener('error', function(event) {
    console.error('JavaScript エラー:', event.error);
    showError('予期しないエラーが発生しました');
});

// Promise の未処理拒否をキャッチ
window.addEventListener('unhandledrejection', function(event) {
    console.error('未処理の Promise 拒否:', event.reason);
    showError('ネットワークエラーが発生しました');
});

// ページアンロード時のクリーンアップ
window.addEventListener('beforeunload', function() {
    // 必要に応じてクリーンアップ処理を追加
    console.log('結果画面をアンロード中...');
});

// 数秒後に「タップでホームに」を表示
setTimeout(() => {
    const tapHome = document.getElementById('tap-home');
    const resultsPanel = document.querySelector('.results-panel');
    if (tapHome) {
        tapHome.classList.add('show');
    }
}, 3000); // 3秒後

document.addEventListener("DOMContentLoaded", () => {
    const resultsPanel = document.querySelector('.results-panel');
    if (resultsPanel) {
        // 最初は無効化
        resultsPanel.style.pointerEvents = 'none';

        setTimeout(() => {
            resultsPanel.style.pointerEvents = 'auto';
            resultsPanel.style.cursor = 'pointer';

            resultsPanel.addEventListener('click', () => {
                window.location.href = '/main';
            });
        }, 3000); // 3秒後に有効化
    }
});

