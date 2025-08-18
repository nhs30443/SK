// 画面読み込み時に紙吹雪アニメーションを強調
window.addEventListener('load', function() {
    document.body.classList.add('celebrate');
    setTimeout(() => {
        document.body.classList.remove('celebrate');
    }, 1000);
});

// キーボード操作
document.addEventListener('keydown', function(e) {
    if (e.key === 'r' || e.key === 'R') {
        window.location.href = '/question';
    } else if (e.key === 'h' || e.key === 'H') {
        window.location.href = '/';
    }
});
