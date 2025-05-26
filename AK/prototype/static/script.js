// jQueryの読み込み完了を確認
$(document).ready(function() {
  console.log("jQuery ready"); // デバッグ用

  // スタートボタン処理
  $('#start-button').off('click').on('click', function() {
    console.log("Start button clicked"); // デバッグ用

    $.ajax({
      url: '/get_question',
      type: 'POST',
      dataType: 'json', // 明示的にJSONを指定
      data: {
        grade: $('#grade').val()
      },
      success: function(data) {
        console.log("問題取得成功:", data); // デバッグ用

        // 問題文表示
        $('#question').text(data.question || "問題文がありません");

        // 選択肢ボタン初期化
        $('.option-button').each(function(index) {
          if(data.options && data.options[index]) {
            $(this)
              .text(data.options[index])
              .data('answer', data.options[index])
              .prop('disabled', false)
              .show();
          }
        });

        // 正解データ保存（2重保険）
        if(data.correct_answer) {
          $('#correct-answer')
            .data('correct-answer', data.correct_answer)
            .attr('data-correct', data.correct_answer);
        }
      },
      error: function(xhr, status, error) {
        console.error("Error:", status, error); // 詳細エラー表示
        alert('問題取得に失敗しました\n' + error);
      }
    });
  });

  // 解答ボタン処理（動的要素対応版）
  $(document).off('click', '.option-button').on('click', '.option-button', function() {
    var $btn = $(this);
    console.log("解答ボタンクリック:", $btn.data('answer')); // デバッグ用

    $btn.prop('disabled', true);

    // 正解データ取得（2通りで保険）
    var correctAnswer = $('#correct-answer').data('correct-answer') ||
                       $('#correct-answer').attr('data-correct');

    if(!correctAnswer) {
      alert('正解データが読み込まれていません');
      $btn.prop('disabled', false);
      return;
    }

    $.ajax({
      url: '/check_answer',
      type: 'POST',
      dataType: 'json',
      data: {
        user_answer: $btn.data('answer'),
        correct_answer: correctAnswer
      },
      success: function(data) {
        console.log("判定結果:", data); // デバッグ用

        var resultHtml = data.correct ?
          '<span style="color:green">✅ 正解!</span>' :
          '<span style="color:red">❌ 不正解! 正解は ' + correctAnswer + '</span>';

        $('#result')
          .html(resultHtml)
          .css({display: 'block', opacity: 0})
          .animate({opacity: 1}, 500);
      },
      error: function(xhr, status, error) {
        console.error("判定エラー:", status, error);
        alert('判定に失敗しました\n' + error);
        $btn.prop('disabled', false);
      },
      complete: function() {
        console.log("処理完了");
      }
    });
  });
});