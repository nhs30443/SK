// 例：選択肢をクリックしたら表示する
document.querySelectorAll('.choice').forEach(choice => {
    choice.addEventListener('click', () => {
    alert(`「${choice.textContent}」が選ばれました`);
    });
});

$(function(){
  $('#hamburger').on('click',function(){
    $('#hamburger').toggleClass("open");
    $('#header-menu').slideToggle();
  });
});
