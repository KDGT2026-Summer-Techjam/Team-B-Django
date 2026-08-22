document.addEventListener('DOMContentLoaded', async () => {
    // 1. HTMLのbodyタグから public_id を取得
    const body = document.querySelector('body');
    const publicId = body.dataset.publicId;
    
    // このページに title を表示する場所があるかチェック
    const doneTitle = document.getElementById('done-title');
    
    if (publicId && doneTitle) {
        try {
            // 2. GETリクエストでイベントデータを取得
            const response = await fetch(`/api/events/${publicId}`);
            
            if (response.ok) {
                const eventData = await response.json();
                
                // 3. 取得したデータを各HTML要素にセットする
                document.getElementById('done-title').textContent = eventData.title;
                document.getElementById('done-date').textContent = eventData.event_date.replace(/-/g, '/');
                document.getElementById('done-location').textContent = eventData.location;
                document.getElementById('done-author').textContent = eventData.organizer_name;
  
                // 4. メンバーのリスト処理
                const membersContainer = document.getElementById('done-members');
                membersContainer.innerHTML = ''; 
  
                if (eventData.participants && eventData.participants.length > 0) {
                    eventData.participants.forEach(participant => {
                        membersContainer.appendChild(document.createTextNode(`・${participant.name}`));
                        membersContainer.appendChild(document.createElement('br'));
                    });
                } else {
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
  
    // ★ここから追加：戻るボタンの処理★
    const btnReturn = document.getElementById('btn-return');
    if (btnReturn) {
        btnReturn.addEventListener('click', () => {
            // url.pyの my_events_list のURL（/myevents）へ遷移させる
            window.location.href = '/myevents';
        });
    }
    // ★追加ここまで★
  });