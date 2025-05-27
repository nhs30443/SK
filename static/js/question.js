// 例：選択肢をクリックしたら表示する
document.querySelectorAll('.choice').forEach(choice => {
    choice.addEventListener('click', () => {
    alert(`「${choice.textContent}」が選ばれました`);
    });
});

// ハンバーガーメニュー開閉
document.getElementById("hamburger").addEventListener("click", () => {
    const menu = document.getElementById("menu");
    menu.style.display = (menu.style.display === "block") ? "none" : "block";
});
