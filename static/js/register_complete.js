let seconds = 5;
const countdownElement = document.getElementById("countdown");
const loginUrl = countdownElement.dataset.loginUrl;

const interval = setInterval(() => {
    seconds--;
    countdownElement.innerHTML = `${seconds}秒後に <a href="${loginUrl}">ログインページ</a> へリダイレクトします`;

    if (seconds <= 0) {
        clearInterval(interval);
        window.location.href = loginUrl;
    }
}, 1000);
