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

              // 画像は任意項目のため、設定されている場合のみ表示し、無ければプレースホルダーのままにする
              const doneImage = document.getElementById('done-image');
              const doneImagePlaceholder = document.getElementById('done-image-placeholder');
              if (eventData.image) {
                  doneImage.src = eventData.image;
                  doneImage.style.display = 'block';
                  doneImagePlaceholder.style.display = 'none';
              }

              document.getElementById('done-location').textContent = eventData.location;
              document.getElementById('done-author').textContent = eventData.organizer_name;

              // コピー・シェアボタン（script.js）に渡す共有用テキストとURLを組み立てる
              // event_date は "YYYY-MM-DD" 形式のため、月・日を取り出して定型文に埋め込む
              const [, month, day] = eventData.event_date.split('-').map(Number);
              window.eventShareText = `${month}月${day}日は空いてる？みんなで一緒に${eventData.title}に行こう！`;
              // 末尾スラッシュ必須（events/urls.pyのルーティングに合わせる）
              window.eventShareUrl = `${window.location.origin}/e/${publicId}/`;

              // 共有データの組み立てが終わるまでは、コピー・シェアボタンを無効のままにする。
              // 取得前に押されると空文字や誤ったURLがコピー・共有されてしまうため
              const btnCopy = document.getElementById('btn-copy');
              const btnShare = document.getElementById('btn-share');
              if (btnCopy) btnCopy.disabled = false;
              if (btnShare) btnShare.disabled = false;

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
