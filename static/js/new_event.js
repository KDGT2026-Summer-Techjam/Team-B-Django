document.addEventListener('DOMContentLoaded', () => {
  const btnComplete = document.getElementById('btn-complete');
  
  // 入力要素（時間は任意項目のためinputsには含めない）
  const inputTitle = document.getElementById('input-title');
  const inputDate = document.getElementById('input-date');
  const inputTime = document.getElementById('input-time');
  const inputLocation = document.getElementById('input-location');
  const inputAuthor = document.getElementById('input-author');

  const inputs = [inputTitle, inputDate, inputLocation, inputAuthor];

  // 画像アップロード関連の要素（画像は任意項目のためinputsには含めない）
  // 受け付ける形式・サイズ上限はevents/views_api.pyのPHOTO_DATA_URL_PREFIXES・PHOTO_MAX_LENGTHと合わせる
  const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  const IMAGE_MAX_LENGTH = 5 * 1024 * 1024;
  const imageSection = document.getElementById('image-section');
  const inputImage = document.getElementById('input-image');
  const imagePreview = document.getElementById('image-preview');
  const imagePlaceholderIcon = document.getElementById('image-placeholder-icon');
  const errorImage = document.getElementById('error-image');
  let selectedImageDataUrl = null;

  // 画像エリアのクリックでファイル選択ダイアログを開く
  imageSection.addEventListener('click', () => {
      inputImage.click();
  });

  function showImageError(message) {
      errorImage.textContent = message;
      errorImage.style.display = 'block';
      inputImage.value = '';
  }

  // ファイル選択時に形式・サイズを検証し、Base64へ変換してプレビュー表示する
  inputImage.addEventListener('change', () => {
      const file = inputImage.files[0];
      if (!file) {
          return;
      }

      errorImage.style.display = 'none';
      errorImage.textContent = '';

      if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
          showImageError('対応していない画像形式です（JPEG/PNG/WEBPのみ）');
          return;
      }

      const reader = new FileReader();
      reader.onload = () => {
          const dataUrl = reader.result;
          if (dataUrl.length > IMAGE_MAX_LENGTH) {
              showImageError('画像のサイズが大きすぎます（5MB以下にしてください）');
              return;
          }
          selectedImageDataUrl = dataUrl;
          imagePreview.src = selectedImageDataUrl;
          imagePreview.style.display = 'block';
          imagePlaceholderIcon.style.display = 'none';
      };
      reader.onerror = () => {
          showImageError('画像の読み込みに失敗しました');
      };
      reader.readAsDataURL(file);
  });

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

  // APIのエラーメッセージ文言から対象フィールドを判定する
  // ※ views_api.py は { "error": "..." } のみを返しフィールド名を含まないため、
  //   文言で一意に特定できるものだけ対応フィールドに出し、それ以外はタイトル欄に出す
  function errorTargetId(message) {
      if (message === '日付が不正です') return 'error-date';
      if (message === '投稿者名を入力してください') return 'error-author';
      return 'error-title';
  }

  // エラーメッセージを対象フィールドの下に表示する
  function showError(message) {
      const target = document.getElementById(errorTargetId(message));
      target.textContent = message;
      target.style.display = 'block';
  }

  // 完了ボタンクリック時の処理
  btnComplete.addEventListener('click', async () => {
      clearErrors();
      
      const payload = {
          title: inputTitle.value.trim(),
          event_date: inputDate.value,
          location: inputLocation.value.trim(),
          organizer_name: inputAuthor.value.trim()
      };

      // 時間・画像はともに任意項目のため、入力されている場合のみpayloadに含める
      if (inputTime.value) {
          payload.start_time = inputTime.value;
      }
      if (selectedImageDataUrl) {
          payload.image = selectedImageDataUrl;
      }

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
              // エラー時: メッセージ内容に応じた対象フィールドの下に赤字で表示
              const errorData = await response.json();

              if (errorData.error) {
                  showError(errorData.error);
              }
          }
      } catch (error) {
          console.error('API Error:', error);
          showError("通信エラーが発生しました。");
      }
  });
});