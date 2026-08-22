
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('events-container');
    const savedData = localStorage.getItem('inby_saved_events');
    let events = [];

    if (savedData) {
        try {
            events = JSON.parse(savedData);
        } catch(e) {
            console.error("データの読み込みに失敗しました");
        }
    }

    if (events.length === 0) {
        container.innerHTML = '<p class="empty-message">まだ作成されたカードがありません。</p>';
        return;
    }

    let htmlString = '';
    
    events.slice().reverse().forEach(event => {
        const membersText = (event.members || '').replace(/\n/g, '<br>');
        
        // データから public_id を取得（無い場合はエラーを防ぐため 'error-id' を入れる）
        const publicId = event.public_id || 'error-id';
        
        // Djangoの urls.py "e/<str:public_id>/" に合わせたURLを生成
        const detailUrl = `/e/${publicId}/`; 

        // ⬇︎ 全体を aタグ(card-link) で囲んでいます ⬇︎
        htmlString += `
            <a href="${detailUrl}" class="card-link">
                <div class="preview-scale-box">
                    <div class="card-container preview-card">
                        <div class="card-content">
                            <div class="text-section">
                                <div class="input-title">${event.title || 'タイトルなし'}</div>
                                <div class="input-date">${event.date || '未定'}</div>
                                <div class="input-time">${event.time || '未定'}</div>
                                <div class="input-location">${event.location || '未定'}</div>
                                <div class="input-author">${event.author || '未定'}</div>

                                <div class="members-area">
                                    <span>メンバー</span>
                                    <div class="input-members">${membersText}</div>
                                </div>
                            </div>
                            
                            <div class="image-section">
                                <svg viewBox="0 0 24 24">
                                    <path d="M19,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,19H5V5H19V19M13.96,12.29L11.21,15.83L9.25,13.47L6.5,17H17.5L13.96,12.29Z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </a>
        `;
    });

    container.innerHTML = htmlString;
});