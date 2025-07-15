// 画面読み込み時に揺れエフェクトを発生
window.addEventListener('load', function() {
    document.body.classList.add('shake');
    setTimeout(() => {
        document.body.classList.remove('shake');
    }, 500);
});

// キーボードでも操作できるようにする
document.addEventListener('keydown', function(e) {
    if (e.key === 'r' || e.key === 'R') {
        window.location.href = '/question';
    } else if (e.key === 'h' || e.key === 'H') {
        window.location.href = '/';
    }
});