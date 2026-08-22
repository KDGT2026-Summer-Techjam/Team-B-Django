// static/js/new_event.js

document.addEventListener('DOMContentLoaded', () => {
    const btnComplete = document.getElementById('btn-complete');
    
    // 入力要素
    const inputTitle = document.getElementById('input-title');
    const inputDate = document.getElementById('input-date');
    const inputTime = document.getElementById('input-time');
    const inputLocation = document.getElementById('input-location');
    const inputAuthor = document.getElementById('input-author');
    
    const inputs = [inputTitle, inputDate, inputTime, inputLocation, inputAuthor];
  
    // 開催日の過去日選択不可対応
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
  
    // エラー表示をリセット
    function clearErrors() {
        document.querySelectorAll('.error-msg').forEach(el => {
            el.style.display = 'none';
            el.textContent = '';
        });
    }
  
    // エラー対象判定
    function errorTargetId(message) {
        if (message === '日付が不正です') return 'error-date';
        if (message === '投稿者名を入力してください') return 'error-author';
        return 'error-title';
    }
  
    // エラーメッセージを表示
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
                // 送信成功時
                const data = await response.json();

                // ==========================================================
                // ★ここから：LocalStorageへの保存処理（デバッグ強化版）★
                // ==========================================================
                console.group('=== LocalStorage 保存デバッグ ==='); // デバッグログをグループ化
                console.log("1. APIへのPOST送信が成功しました。");

                const savedData = localStorage.getItem('inby_saved_events');
                let events = [];
                if (savedData) {
                    try {
                        events = JSON.parse(savedData);
                        console.log("2. 既存のデータをLocalStorageから読み込みました。");
                    } catch(e) {
                        console.error("2. [エラー] データのJSON解析に失敗しました。", e);
                    }
                } else {
                    console.log("2. 既存のデータはありません。新規リストを作成します。");
                }
                
                // 一覧画面で表示するためのデータを構成
                const newSavedEvent = {
                    public_id: data.public_id,
                    title: payload.title,
                    date: payload.event_date.replace(/-/g, '/'), // ハイフンをスラッシュに変換
                    time: inputTime.value.trim(),
                    location: payload.location,
                    author: payload.organizer_name,
                    members: "" // 作成直後はメンバーがいないので空
                };
                
                // 配列に追加して保存
                events.push(newSavedEvent);
                
                console.log("3. 保存直前の配列（events）:", events);
                console.log("4. 保存するJSON文字列（キー: inby_saved_events）:", JSON.stringify(events));

                try {
                    localStorage.setItem('inby_saved_events', JSON.stringify(events));
                    console.log("5. LocalStorageへの保存が、エラーなく完了しました！");
                    
                    // 一時的に保存されたか確認
                    const checkSavedData = localStorage.getItem('inby_saved_events');
                    console.log("6. 保存直後のLocalStorageの内容:", checkSavedData);
                    
                } catch(e) {
                    // LocalStorageの容量制限や、プライベートモードなどでエラーになった場合にここに入る
                    console.error("5. [エラー] LocalStorageへの保存に失敗しました。", e);
                }
                
                console.groupEnd(); // グループ化を終了
                // ==========================================================

                // 保存が終わってから遷移
                window.location.href = `/e/${data.public_id}/done`;

            } else {
                // APIエラー時
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