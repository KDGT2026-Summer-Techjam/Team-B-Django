document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const publicId = body.dataset.publicId;
  if (!publicId) return;

  // CSRFトークンを取得
  function getCookie(name) {
    if (!document.cookie) return null;
    const prefix = `${name}=`;
    for (const rawCookie of document.cookie.split(';')) {
      const cookie = rawCookie.trim();
      if (cookie.startsWith(prefix)) {
        return decodeURIComponent(cookie.slice(prefix.length));
      }
    }
    return null;
  }

  // ==========================================
  // 1. イベント情報の取得・描画・編集機能
  // ==========================================
  const nameInputEl = document.getElementById('event-name-input');
  const joinBtnEl = document.getElementById('event-join-btn');
  const errorEl = document.getElementById('event-error');
  const cancelJoinBtnEl = document.getElementById('event-cancel-join-btn');

  let currentParticipantId = null; //現在のブラウザで参加しているParticipantのIDを保持
  let currentEventData = {}; // 編集用に現在のデータを保持
  let isEditing = false; // 編集モードの判定

  function renderParticipants(participants) {
    document.getElementById('event-member-count').textContent = `${participants.length}人`;
    const listEl = document.getElementById('event-member-list');
    listEl.textContent = '';
    if (participants.length === 0) {
      listEl.innerHTML = '<li>まだいません</li>';
      return;
    }
    participants.forEach(p => {
      const li = document.createElement('li');
      const memberName = p.name ? p.name : p; 
      li.textContent = `・${memberName}`;
      listEl.appendChild(li);
    });
  }

  // 画面にテキストを描画する共通関数
  function renderEventDetails(data) {
    document.getElementById('event-title').textContent = data.title;
    document.getElementById('event-date').textContent = data.event_date.replace(/-/g, '/');
    
    // 残り日数の計算
    const target = new Date(`${data.event_date}T00:00:00`);
    const today = new Date();
    today.setHours(0,0,0,0);
    const diffDays = Math.round((target - today) / (1000 * 60 * 60 * 24));
    let daysText = diffDays > 0 ? `あと${diffDays}日` : diffDays === 0 ? '今日' : '終了';
    document.getElementById('event-days-left').textContent = daysText;
    
    document.getElementById('event-location').textContent = data.location;
    document.getElementById('event-author').textContent = `${data.organizer_name} が誘っています`;
    renderParticipants(data.participants || []);
  }

  async function loadEvent() {
    try {
      const res = await fetch(`/api/events/${publicId}`);
      if (res.ok) {
        currentEventData = await res.json();
        renderEventDetails(currentEventData);
      }
    } catch (e) { console.error(e); }
  }

  // ★追加：編集ボタンのロジック
  const btnEdit = document.querySelector('.btn-edit');
  if (btnEdit) {
    btnEdit.addEventListener('click', async () => {
      if (!isEditing) {
        // 【編集モードへ切り替え】
        isEditing = true;
        btnEdit.textContent = '完了';
        btnEdit.style.backgroundColor = '#E57373'; // 完了ボタンっぽい色に変更
        
        // テキストをinputタグに置き換える
        document.getElementById('event-title').innerHTML = `<input type="text" id="edit-title" class="edit-input" value="${currentEventData.title}">`;
        document.getElementById('event-date').innerHTML = `<input type="date" id="edit-date" class="edit-input" value="${currentEventData.event_date}">`;
        document.getElementById('event-location').innerHTML = `<input type="text" id="edit-location" class="edit-input" value="${currentEventData.location}">`;
        document.getElementById('event-author').innerHTML = `<input type="text" id="edit-author" class="edit-input" value="${currentEventData.organizer_name}">`;
        
      } else {
        // 【保存処理（API通信）】
        const newTitle = document.getElementById('edit-title').value.trim();
        const newDate = document.getElementById('edit-date').value;
        const newLocation = document.getElementById('edit-location').value.trim();
        const newAuthor = document.getElementById('edit-author').value.trim();

        if (!newTitle || !newDate || !newLocation || !newAuthor) {
          alert('すべての項目を入力してください');
          return;
        }

        btnEdit.disabled = true;
        try {
          const headers = { 'Content-Type': 'application/json' };
          const csrfToken = getCookie('csrftoken');
          if (csrfToken) headers['X-CSRFToken'] = csrfToken;
          
          // PATCHリクエストでデータを更新
          const res = await fetch(`/api/events/${publicId}`, {
            method: 'PATCH',
            headers: headers,
            body: JSON.stringify({
              title: newTitle,
              event_date: newDate,
              location: newLocation,
              organizer_name: newAuthor
            })
          });

          if (res.ok) {
            currentEventData = await res.json();
            isEditing = false;
            btnEdit.textContent = '編集';
            btnEdit.style.backgroundColor = ''; // 色を元に戻す
            renderEventDetails(currentEventData);
          } else {
            const err = await res.json();
            alert(err.error || '編集に失敗しました。作成者のみが編集可能です。');
          }
        } catch (e) {
          alert('通信エラーが発生しました');
        } finally {
          btnEdit.disabled = false;
        }
      }
    });
  }

  // 参加ボタンの処理
  joinBtnEl.addEventListener('click', async () => {
    if (errorEl) { errorEl.textContent = ''; errorEl.hidden = true; }
    const name = nameInputEl.value.trim();
    if (!name) {
      if (errorEl) { errorEl.textContent = '名前を入力してください'; errorEl.hidden = false; }
      return;
    }
    
    joinBtnEl.disabled = true;
    try {
      const headers = { 'Content-Type': 'application/json' };
      const csrfToken = getCookie('csrftoken');
      if (csrfToken) headers['X-CSRFToken'] = csrfToken;

      const res = await fetch(`/api/events/${publicId}/participants`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ name })
      });
      
      if (res.ok) {
        const data = await res.json();
        // 現在のデータにも参加者を反映
        currentParticipantId = data.id;

        if (data.participants && Array.isArray(data.participants)) {
          currentEventData.participants = data.participants;
        } 
        
        renderParticipants(currentEventData.participants);
        nameInputEl.value = ''; 
        joinBtnEl.hidden = true;
        nameInputEl.hidden = true;
        cancelJoinBtnEl.hidden = false;
      } else {
        if (errorEl) { errorEl.textContent = 'エラーが発生しました'; errorEl.hidden = false; }
      }
    } catch (e) { 
      if (errorEl) { errorEl.textContent = '通信エラーが発生しました'; errorEl.hidden = false; }
    } finally {
      joinBtnEl.disabled = false;
    }
  });

  // 参加取り消しボタンの処理
  if (cancelJoinBtnEl) {
    cancelJoinBtnEl.addEventListener('click', async () => {
      if (!currentParticipantId) {
        if (errorEl) {
          errorEl.textContent = '参加者情報を取得できませんでした';
          errorEl.hidden = false;
        }
        return;
      }

      cancelJoinBtnEl.disabled = true;

      try {
        const headers = {};
        const csrfToken = getCookie('csrftoken');

        if (csrfToken) {
          headers['X-CSRFToken'] = csrfToken;
        }

        const res = await fetch(
          `/api/events/${publicId}/participants/${currentParticipantId}`,
          {
            method: 'DELETE',
            headers: headers
          }
        );

        if (res.ok) {
          const data = await res.json();

          currentEventData.participants = data.participants || [];
          renderParticipants(currentEventData.participants);

          currentParticipantId = null;

          joinBtnEl.hidden = false;
          nameInputEl.hidden = false;
          cancelJoinBtnEl.hidden = true;

          if (errorEl) {
            errorEl.textContent = '';
            errorEl.hidden = true;
          }
        } else {
          const data = await res.json();

          if (errorEl) {
            errorEl.textContent = data.error || '参加の取り消しに失敗しました';
            errorEl.hidden = false;
          }
        }
      } catch (e) {
        console.error(e);

        if (errorEl) {
          errorEl.textContent = '通信エラーが発生しました';
          errorEl.hidden = false;
        }
      } finally {
        cancelJoinBtnEl.disabled = false;
      }
    });
  }

  loadEvent();

  // ==========================================
  // 2. スタンプラリーのロジック
  // ==========================================
  const activePath = document.getElementById('active-path');
  let pathLength = 0;
  if (activePath) {
    pathLength = activePath.getTotalLength(); 
    activePath.style.strokeDasharray = pathLength;
    activePath.style.strokeDashoffset = pathLength; 
    activePath.style.transition = 'stroke-dashoffset 1.5s ease-in-out';
  }
  
  let currentMission = 1;
  
  for (let i = 1; i <= 3; i++) {
    const node = document.getElementById(`node-${i}`);
    const pBox = document.getElementById(`photo-box-${i}`);
    
    if (node) {
      node.classList.remove('hidden');
      node.classList.add('locked');
    }
    if (pBox) {
      pBox.classList.remove('hidden');
      pBox.classList.add('locked');
    }
  }

  for(let i=1; i<=3; i++) {
    const node = document.getElementById(`node-${i}`);
    if(node) {
      node.addEventListener('click', () => {
        if (node.classList.contains('locked') && i === currentMission) {
          setNodeActive(i); 
        }
      });
    }
    
    const fileInput = document.getElementById(`file-${i}`);
    if(fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          const reader = new FileReader();
          reader.onload = (event) => {
            const img = document.getElementById(`preview-${i}`);
            img.src = event.target.result;
            img.style.display = 'block';
            document.querySelector(`#photo-box-${i} .photo-label`).style.display = 'none';
            
            setNodeDone(i);
            
            if(i < 3) {
              animatePathToNext(i);
            }
          }
          reader.readAsDataURL(e.target.files[0]);
        }
      });
    }
  }

  function setNodeActive(num) {
    const node = document.getElementById(`node-${num}`);
    node.className = `map-node node-${num} active`;
    node.innerHTML = `<div class="node-icon">📷</div><div class="node-num">${num}</div>`;
    
    const pBox = document.getElementById(`photo-box-${num}`);
    pBox.className = `photo-box pb-${num} active`;

    const mRow = document.querySelector(`.mission-row[data-mission="${num}"]`);
    mRow.className = `mission-row active`;
    document.getElementById(`m-icon-${num}`).textContent = '📷';
  }

  function setNodeDone(num) {
    const node = document.getElementById(`node-${num}`);
    node.className = `map-node node-${num} done`;
    node.innerHTML = `<div class="node-icon">✔</div><div class="node-num">✔</div>`;
    
    const pBox = document.getElementById(`photo-box-${num}`);
    pBox.className = `photo-box pb-${num} done`;
    
    const mRow = document.querySelector(`.mission-row[data-mission="${num}"]`);
    mRow.className = `mission-row done`;
    document.getElementById(`m-icon-${num}`).textContent = '✔';
  }

  function animatePathToNext(currentNum) {
    if (!activePath) return;
    const offset = currentNum === 1 ? (pathLength * 0.5) : 0; 
    activePath.style.strokeDashoffset = offset;
    
    setTimeout(() => {
      currentMission = currentNum + 1;
    }, 1500);
  }

  // ==========================================
  // 3. コピーとダウンロード機能
  // ==========================================
  const btnCopy = document.getElementById('btn-copy');
  if(btnCopy) {
    btnCopy.addEventListener('click', () => {
      navigator.clipboard.writeText(window.location.href).then(() => {
        alert('URLをコピーしました！');
      });
    });
  }

  const btnDownload = document.getElementById('btn-download');
  if(btnDownload) {
    btnDownload.addEventListener('click', () => {
      const targetArea = document.getElementById('capture-area');
      const footer = document.getElementById('footer-actions');
      
      footer.style.display = 'none'; 
      
      if (typeof html2canvas !== 'undefined') {
        html2canvas(targetArea, {
          scale: 2, 
          backgroundColor: "#F6F5EF",
          useCORS: true
        }).then(canvas => {
          const link = document.createElement('a');
          link.download = 'inby-event-card.png';
          link.href = canvas.toDataURL('image/png');
          link.click();
          footer.style.display = 'flex'; 
        }).catch(err => {
          console.error("ダウンロードエラー:", err);
          footer.style.display = 'flex';
        });
      } else {
        alert("画像の生成に失敗しました。少し待ってから再度お試しください。");
        footer.style.display = 'flex';
      }
    });
  }
});