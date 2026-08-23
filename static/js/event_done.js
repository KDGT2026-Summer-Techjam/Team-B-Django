document.addEventListener('DOMContentLoaded', async () => {
  // 1. HTMLのbodyタグから public_id を取得
  const body = document.querySelector('body');
  const publicId = body.dataset.publicId;

  // このページに title を表示する場所があるか（完了ページか）チェック
  const doneTitle = document.getElementById('done-title');

  if (publicId && doneTitle) {
      try {
          // 2. GETリクエストでイベントデータを取得 (views_api.py の get_event に対応)
          const response = await fetch(`/api/events/${publicId}`);

          if (response.ok) {
              const eventData = await response.json();

              // 3. 取得したデータを各HTML要素にセットする
              document.getElementById('done-title').textContent = eventData.title;

              // 日付のハイフン(YYYY-MM-DD)をスラッシュ(YYYY/MM/DD)に置換
              document.getElementById('done-date').textContent = eventData.event_date.replace(/-/g, '/');

              // 時間は任意項目のため、設定されている場合のみ表示する（未設定なら非表示のまま）
              const doneTime = document.getElementById('done-time');
              if (eventData.start_time) {
                  doneTime.textContent = eventData.start_time.slice(0, 5);
                  doneTime.hidden = false;
              }

              document.getElementById('done-location').textContent = eventData.location;
              document.getElementById('done-author').textContent = eventData.organizer_name;

              // 4. メンバーのリスト処理
              const membersContainer = document.getElementById('done-members');
              membersContainer.innerHTML = ''; // 「読み込み中...」の文字をクリア

              if (eventData.participants && eventData.participants.length > 0) {
                  // 参加者がいる場合はループして追加
                  // 参加者名はユーザー入力のため、textContent + <br>要素でエスケープして描画する
                  eventData.participants.forEach(participant => {
                      membersContainer.appendChild(document.createTextNode(`・${participant.name}`));
                      membersContainer.appendChild(document.createElement('br'));
                  });
              } else {
                  // 参加者がいない場合
                  membersContainer.textContent = '・まだメンバーはいません';
              }

          } else {
              console.error("データの取得に失敗しました。ステータスコード:", response.status);
              doneTitle.textContent = "データを読み込めませんでした";
          }
      } catch (error) {
          console.error("通信エラーが発生しました:", error);
          doneTitle.textContent = "通信エラー";
      }
  }
});
