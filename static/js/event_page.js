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
  const missionIdByOrder = {}; // ミッションのorder番号 -> Mission.id（写真アップロードAPIに必要）
  // デコる機能の段階解放を更新する関数。4.のブロックで実体を割り当てる
  let updateDoodleUnlockState = null;

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

    // 開始時刻の表示（任意項目のため、設定されている場合のみ表示する）
    const timeEl = document.getElementById('event-time');
    if (data.start_time) {
      timeEl.textContent = data.start_time.slice(0, 5);
      timeEl.hidden = false;
    } else {
      timeEl.hidden = true;
    }

    document.getElementById('event-location').textContent = data.location;
    document.getElementById('event-author').textContent = `${data.organizer_name} が誘っています`;
    renderParticipants(data.participants || []);

    // イベント画像の表示
    const imageEl = document.getElementById('event-image');
    if (data.image) {
      imageEl.src = data.image;
      imageEl.style.display = 'block';
    } else {
      imageEl.removeAttribute('src');
      imageEl.style.display = 'none';
    }
  }

  // 参加中/未参加に応じて参加フォームと取り消しボタンの表示を切り替える
  function applyParticipationState(participantId) {
    currentParticipantId = participantId || null;
    const joined = !!currentParticipantId;
    joinBtnEl.hidden = joined;
    nameInputEl.hidden = joined;
    cancelJoinBtnEl.hidden = !joined;
  }

  async function loadEvent() {
    try {
      const res = await fetch(`/api/events/${publicId}`);
      if (res.ok) {
        currentEventData = await res.json();
        renderEventDetails(currentEventData);
        applyParticipationState(currentEventData.my_participant_id);
        restoreMissionProgress(currentEventData.missions);
      }
    } catch (e) { console.error(e); }
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
        applyParticipationState(data.id);

        if (data.participants && Array.isArray(data.participants)) {
          currentEventData.participants = data.participants;
        }

        renderParticipants(currentEventData.participants);
        nameInputEl.value = '';
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

          applyParticipationState(null);

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
      // missionIdByOrderが揃う（loadEvent完了）まではアップロード不可にしておく
      // ラベル経由のクリックもdisabled状態のinputには効かないため、これで競合状態を防げる
      fileInput.disabled = true;

      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          const reader = new FileReader();
          reader.onload = async (event) => {
            const photoDataUrl = event.target.result;
            const img = document.getElementById(`preview-${i}`);
            const label = document.querySelector(`#photo-box-${i} .photo-label`);

            img.src = photoDataUrl;
            img.style.display = 'block';
            if (label) label.style.display = 'none';

            const missionId = missionIdByOrder[i];
            if (!missionId) {
              alert('お題情報を取得できませんでした。ページを再読み込みしてください');
              return;
            }

            fileInput.disabled = true;
            try {
              const headers = { 'Content-Type': 'application/json' };
              const csrfToken = getCookie('csrftoken');
              if (csrfToken) headers['X-CSRFToken'] = csrfToken;

              const res = await fetch(`/api/events/${publicId}/missions/${missionId}/photo`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ photo: photoDataUrl })
              });

              if (res.ok) {
                setNodeDone(i);

                if (i < 3) {
                  animatePathToNext(i);
                }
              } else {
                const data = await res.json().catch(() => ({}));
                alert(data.error || '写真の登録に失敗しました');
                img.style.display = 'none';
                img.removeAttribute('src');
                if (label) label.style.display = 'flex';
              }
            } catch (err) {
              alert('通信エラーが発生しました');
              img.style.display = 'none';
              img.removeAttribute('src');
              if (label) label.style.display = 'flex';
            } finally {
              fileInput.disabled = false;
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

  // photoUrl指定時は写真プレビューも復元する（ページ読み込み時の状態復元用）
  function setNodeDone(num, photoUrl) {
    const node = document.getElementById(`node-${num}`);
    node.className = `map-node node-${num} done`;
    node.innerHTML = `<div class="node-icon">✔</div><div class="node-num">✔</div>`;

    const pBox = document.getElementById(`photo-box-${num}`);
    pBox.className = `photo-box pb-${num} done`;

    if (photoUrl) {
      const img = document.getElementById(`preview-${num}`);
      const label = document.querySelector(`#photo-box-${num} .photo-label`);
      img.src = photoUrl;
      img.style.display = 'block';
      if (label) label.style.display = 'none';
    }

    const mRow = document.querySelector(`.mission-row[data-mission="${num}"]`);
    mRow.className = `mission-row done`;
    document.getElementById(`m-icon-${num}`).textContent = '✔';

    // ミッション達成数に応じてデコる機能（色・スタンプ）の解放状態を更新する
    if (updateDoodleUnlockState) {
      const doneCount = document.querySelectorAll('.mission-row.done').length;
      updateDoodleUnlockState(doneCount);
    }
  }

  function animatePathToNext(currentNum) {
    if (!activePath) return;
    const offset = currentNum === 1 ? (pathLength * 0.5) : 0;
    activePath.style.strokeDashoffset = offset;

    setTimeout(() => {
      currentMission = currentNum + 1;
    }, 1500);
  }

  // ページ読み込み時、サーバーに保存済みのミッション進行状況を画面に復元する
  function restoreMissionProgress(missions) {
    if (!Array.isArray(missions) || missions.length === 0) return;

    let firstIncompleteOrder = null;

    missions.forEach(mission => {
      missionIdByOrder[mission.order] = mission.id;

      // missionIdが確定したのでアップロードを解禁する
      const fileInput = document.getElementById(`file-${mission.order}`);
      if (fileInput) fileInput.disabled = false;

      const inputEl = document.querySelector(`.mission-row[data-mission="${mission.order}"] .mission-input`);
      if (inputEl) inputEl.value = mission.prompt_text;

      if (mission.completed_at) {
        setNodeDone(mission.order, mission.photo);
      } else if (firstIncompleteOrder === null) {
        firstIncompleteOrder = mission.order;
      }
    });

    // 軌跡の線の進捗も、animatePathToNextと同じルールで完了状況に合わせて描画する
    if (activePath) {
      const isDone = order => missions.some(m => m.order === order && m.completed_at);
      if (isDone(2)) {
        activePath.style.strokeDashoffset = 0;
      } else if (isDone(1)) {
        activePath.style.strokeDashoffset = pathLength * 0.5;
      }
    }

    if (firstIncompleteOrder !== null) {
      currentMission = firstIncompleteOrder;
      setNodeActive(firstIncompleteOrder);
    }
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
      if (doodleToolbar) doodleToolbar.style.display = 'none';

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
          if (doodleToolbar) doodleToolbar.style.display = 'flex';
        }).catch(err => {
          console.error("ダウンロードエラー:", err);
          footer.style.display = 'flex';
          if (doodleToolbar) doodleToolbar.style.display = 'flex';
        });
      } else {
        alert("画像の生成に失敗しました。少し待ってから再度お試しください。");
        footer.style.display = 'flex';
        if (doodleToolbar) doodleToolbar.style.display = 'flex';
      }
    });
  }

  // ==========================================
  // 4. デコる（Doodle）機能
  // ==========================================
  const captureArea = document.getElementById('capture-area');
  const canvas = document.getElementById('doodle-canvas');
  const doodleToolbar = document.getElementById('doodle-toolbar');
  const footerActions = document.getElementById('footer-actions');

  if (canvas && captureArea) {
    const ctx = canvas.getContext('2d');
    const btnToggleDoodle = document.getElementById('btn-toggle-doodle');
    const doodleControls = document.getElementById('doodle-controls');
    const btnClear = document.getElementById('btn-clear-doodle');
    const colorSwatches = document.querySelectorAll('.color-swatch');
    const penWeightInput = document.getElementById('pen-weight');
    const toolModeBtns = document.querySelectorAll('.tool-mode-btn');
    const emojiSwatches = document.querySelectorAll('.emoji-swatch');
    const colorPaletteEl = document.getElementById('color-palette');
    const emojiPaletteEl = document.getElementById('emoji-palette');
    const weightControlEl = document.querySelector('.weight-control');
    const emojiModeBtn = document.getElementById('emoji-mode-btn');

    let isDrawModeOn = false;
    let isDrawing = false;
    let currentX = 0;
    let currentY = 0;
    let strokeColor = '#000000'; // 初期色
    let strokeWidth = 3;
    let currentTool = 'pen'; // 'pen' | 'eraser' | 'emoji'
    let currentEmoji = '⭐';

    // キャンバスのサイズを枠線に合わせる関数
    function resizeCanvas() {
      // 描画内容が消えないように一時退避
      const tempCanvas = document.createElement('canvas');
      const tCtx = tempCanvas.getContext('2d');
      tempCanvas.width = canvas.width;
      tempCanvas.height = canvas.height;
      tCtx.drawImage(canvas, 0, 0);

      // サイズ再設定
      canvas.width = captureArea.offsetWidth;
      canvas.height = captureArea.offsetHeight;
      
      // 退避した描画内容を復元
      ctx.drawImage(tempCanvas, 0, 0);
      
      // 線の見た目設定を再適用
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }

    // 初期化
    setTimeout(resizeCanvas, 100); // 画面描画が落ち着いてからサイズ取得
    window.addEventListener('resize', resizeCanvas);

    // モード切替
    btnToggleDoodle.addEventListener('click', () => {
      isDrawModeOn = !isDrawModeOn;
      if (isDrawModeOn) {
        btnToggleDoodle.textContent = '✏️ デコるモード: ON';
        btnToggleDoodle.classList.add('active');
        doodleControls.classList.remove('hidden');
        canvas.classList.add('active');
        document.body.style.overflow = 'hidden'; // 背景のスクロールをロック
        if (footerActions) footerActions.classList.add('doodle-disabled'); // 描画中は押せないことを視覚的に示す
      } else {
        btnToggleDoodle.textContent = '✏️ デコるモード: OFF';
        btnToggleDoodle.classList.remove('active');
        doodleControls.classList.add('hidden');
        canvas.classList.remove('active');
        document.body.style.overflow = ''; // スクロールロック解除
        if (footerActions) footerActions.classList.remove('doodle-disabled');
      }
    });

    // 座標取得
    function getPos(e) {
      const rect = canvas.getBoundingClientRect();
      let clientX = e.clientX;
      let clientY = e.clientY;
      if (e.touches && e.touches.length > 0) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
      }
      return { x: clientX - rect.left, y: clientY - rect.top };
    }

    // 絵文字スタンプを指定座標に配置する（一度置いたら固定・再配置不可）
    function stampEmoji(x, y) {
      const size = 40;
      ctx.font = `${size}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(currentEmoji, x, y);
    }

    // 描画開始
    function startDrawing(e) {
      if (!isDrawModeOn) return;
      const pos = getPos(e);

      // 消しゴムは重ね塗りではなく塗った部分を透明にする（スタンプにも影響するため先に設定）
      ctx.globalCompositeOperation = currentTool === 'eraser' ? 'destination-out' : 'source-over';

      if (currentTool === 'emoji') {
        stampEmoji(pos.x, pos.y); // スタンプはタップした瞬間に確定させ、ドラッグでの連続配置はしない
        return;
      }

      isDrawing = true;
      currentX = pos.x;
      currentY = pos.y;

      // タップしただけでも点が描ける（消しゴムなら消える）ようにする
      ctx.beginPath();
      ctx.fillStyle = strokeColor;
      ctx.arc(currentX, currentY, strokeWidth / 2, 0, Math.PI * 2);
      ctx.fill();
    }

    // 描画中
    function draw(e) {
      if (!isDrawing || !isDrawModeOn) return;
      e.preventDefault(); // スマホでの引っ張りスクロールなどを強力に阻止
      const pos = getPos(e);

      ctx.beginPath();
      ctx.moveTo(currentX, currentY);
      ctx.lineTo(pos.x, pos.y);
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth;
      ctx.stroke();
      ctx.closePath();

      currentX = pos.x;
      currentY = pos.y;
    }

    // 描画終了
    function stopDrawing() {
      isDrawing = false;
    }

    // イベントリスナー登録（スマホの passive: false は preventDefault を使うために必須）
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    window.addEventListener('mouseup', stopDrawing);

    canvas.addEventListener('touchstart', startDrawing, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    window.addEventListener('touchend', stopDrawing);

    // ツールバー操作
    colorSwatches.forEach(swatch => {
      swatch.addEventListener('click', () => {
        if (swatch.classList.contains('locked')) return; // 未解放の色は選択不可
        colorSwatches.forEach(s => s.classList.remove('active'));
        swatch.classList.add('active');
        strokeColor = swatch.dataset.color;
      });
    });

    penWeightInput.addEventListener('input', (e) => {
      strokeWidth = e.target.value;
    });

    btnClear.addEventListener('click', () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    });

    // ペン／スタンプの切替
    toolModeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.disabled) return; // スタンプ未解放時は切り替え不可
        currentTool = btn.dataset.mode;
        toolModeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const isEmoji = currentTool === 'emoji';
        // 消しゴムは色を使わないため、色パレットのみ非表示にする（太さは共用するので表示のまま）
        if (colorPaletteEl) colorPaletteEl.classList.toggle('hidden', isEmoji || currentTool === 'eraser');
        if (weightControlEl) weightControlEl.classList.toggle('hidden', isEmoji);
        if (emojiPaletteEl) emojiPaletteEl.classList.toggle('hidden', !isEmoji);
      });
    });

    // 絵文字スタンプの選択
    emojiSwatches.forEach(swatch => {
      swatch.addEventListener('click', () => {
        emojiSwatches.forEach(s => s.classList.remove('active'));
        swatch.classList.add('active');
        currentEmoji = swatch.dataset.emoji;
      });
    });

    // ミッション達成数に応じて色パレット・絵文字スタンプの解放状態を更新する
    function applyDoodleUnlock(doneCount) {
      colorSwatches.forEach(swatch => {
        const tier = parseInt(swatch.dataset.tier, 10) || 0;
        swatch.classList.toggle('locked', tier > doneCount);
      });

      const emojiUnlocked = doneCount >= 3;
      if (emojiModeBtn) {
        emojiModeBtn.disabled = !emojiUnlocked;
        emojiModeBtn.classList.toggle('locked', !emojiUnlocked);
      }

      // 解放前にスタンプモードを選んでいた場合はペンに戻す（基本的には起こらない防御的処理）
      if (!emojiUnlocked && currentTool === 'emoji') {
        currentTool = 'pen';
        toolModeBtns.forEach(b => b.classList.toggle('active', b.dataset.mode === 'pen'));
        if (colorPaletteEl) colorPaletteEl.classList.remove('hidden');
        if (weightControlEl) weightControlEl.classList.remove('hidden');
        if (emojiPaletteEl) emojiPaletteEl.classList.add('hidden');
      }
    }

    updateDoodleUnlockState = applyDoodleUnlock;
    // ページ読み込み直後（ミッションデータ取得前）の初期状態を反映
    applyDoodleUnlock(document.querySelectorAll('.mission-row.done').length);
  }
});