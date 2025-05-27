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
    $('#overlay').fadeToggle(); // オーバーレイ表示切り替え
  });
});


  // オーバーレイをクリックしたらメニューを閉じる処理も追加
  $('#overlay').on('click', function() {
    $('#hamburger').removeClass("open");
    $('#header-menu').slideUp();
    $('#overlay').fadeOut();
  });
});
