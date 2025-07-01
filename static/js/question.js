document.querySelectorAll('.choice').forEach(choice => {
    choice.addEventListener('click', () => {
        const text = `「${choice.textContent}」が選ばれました`;
        const resultBox = document.getElementById('result-box');
        $(resultBox).stop(true, true).text(text).fadeIn().delay(1500).fadeOut();
    });
});

$(function() {
    $('#hamburger').on('click', function() {
        $(this).toggleClass("open");
        $('#header-menu').fadeToggle();
        $('#overlay').fadeToggle();
    });

    $('#overlay').on('click', function() {
        $('#hamburger').removeClass("open");
        $('#header-menu').fadeOut();
        $('#overlay').fadeOut();
    });
});

