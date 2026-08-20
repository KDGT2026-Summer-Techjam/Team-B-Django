document.addEventListener('DOMContentLoaded', () => {
  const btnComplete = document.getElementById('btn-complete');
  
  // 入力要素
  const inputTitle = document.getElementById('input-title');
  const inputDate = document.getElementById('input-date');
  const inputTime = document.getElementById('input-time');
  const inputLocation = document.getElementById('input-location');
  const inputAuthor = document.getElementById('input-author');
  
  const inputs = [inputTitle, inputDate, inputTime, inputLocation, inputAuthor];

  // 開催日の過去日選択不可対応 (min属性に今日の日付をセット)
  const today = new Date().toISOString().split('T')[0];
  inputDate.setAttribute('min', today);

  // 未入力チェックと完了ボタンの有効/無効切り替え
  function validateForm() {
      const isAllFilled = inputs.every(input => input.value.trim() !== '');
      btnComplete.disabled = !isAllFilled;
  }

  // 各入力欄の値が変わるたびにチェックを実行
  inputs.forEach(input => {
      input.addEventListener('input', validateForm);
  });

  // CookieからCSRFトークンを取得する関数
  function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }

  // エラー表示をリセットする関数
  function clearErrors() {
      document.querySelectorAll('.error-msg').forEach(el => {
          el.style.display = 'none';
          el.textContent = '';
      });
  }

  // 完了ボタンクリック時の処理
  btnComplete.addEventListener('click', async () => {
      clearErrors();
      
      const payload = {
          title: inputTitle.value.trim(),
          event_date: inputDate.value,
          // ※注意: モデルに時間が無いためバックエンドの仕様によっては inputTime.value は送信不要な場合があります
          location: inputLocation.value.trim(),
          organizer_name: inputAuthor.value.trim()
      };

      try {
          const response = await fetch('/api/events', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCookie('csrftoken')
              },
              body: JSON.stringify(payload)
          });

          if (response.ok) {
              // 送信成功時: 完了画面へ遷移
              const data = await response.json();
              window.location.href = `/e/${data.public_id}/done`;
          } else {
              // エラー時: 赤字で表示（APIから返るエラーメッセージの構造に合わせて調整してください）
              const errorData = await response.json();
              
              // 簡易的な全体エラー表示の例
              if (errorData.error) {
                  const titleError = document.getElementById('error-title');
                  titleError.textContent = errorData.error;
                  titleError.style.display = 'block';
              }
          }
      } catch (error) {
          console.error('API Error:', error);
          const titleError = document.getElementById('error-title');
          titleError.textContent = "通信エラーが発生しました。";
          titleError.style.display = 'block';
      }
  });
});