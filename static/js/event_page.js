// event_page ページ固有のJS
// docs/設計.md「投稿ページの2状態」: 同じURLのまま参加前／参加後を切り替える。
// 参加済みかどうかはvisitor_id Cookieを見たサーバー判定(data-is-participant)を初期値にし、
// 参加ボタンを押した後はページを再読み込みせずにDOMを書き換える。
document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const publicId = body.dataset.publicId;
  if (!publicId) {
    return;
  }

  const titleEl = document.getElementById('event-title');
  const dateEl = document.getElementById('event-date');
  const daysLeftEl = document.getElementById('event-days-left');
  const locationEl = document.getElementById('event-location');
  const authorEl = document.getElementById('event-author');
  const memberCountEl = document.getElementById('event-member-count');
  const memberListEl = document.getElementById('event-member-list');
  const joinAreaEl = document.getElementById('event-join-area');
  const joinedMessageEl = document.getElementById('event-joined-message');
  const nameInputEl = document.getElementById('event-name-input');
  const joinBtnEl = document.getElementById('event-join-btn');
  const errorEl = document.getElementById('event-error');

  // CookieからCSRFトークンを取得する
  function getCookie(name) {
    if (!document.cookie) {
      return null;
    }
    const prefix = `${name}=`;
    for (const rawCookie of document.cookie.split(';')) {
      const cookie = rawCookie.trim();
      if (cookie.startsWith(prefix)) {
        return decodeURIComponent(cookie.slice(prefix.length));
      }
    }
    return null;
  }

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  }

  function clearError() {
    errorEl.textContent = '';
    errorEl.hidden = true;
  }

  // 参加前／参加後で、名前入力欄・参加ボタン・「参加しました」表示を切り替える
  function applyJoinState(isParticipant) {
    joinAreaEl.hidden = isParticipant;
    joinBtnEl.hidden = isParticipant;
    joinedMessageEl.hidden = !isParticipant;
  }

  // 開催日までの残り日数を出す。当日・過去日は日数ではなく状態を示す文言にする
  function daysLeftText(eventDate) {
    const target = new Date(`${eventDate}T00:00:00`);
    if (Number.isNaN(target.getTime())) {
      return '';
    }
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const msPerDay = 24 * 60 * 60 * 1000;
    const days = Math.round((target - today) / msPerDay);

    if (days > 0) {
      return `あと${days}日`;
    }
    if (days === 0) {
      return '今日';
    }
    return '終了しました';
  }

  // 参加者一覧を描画する。参加者名はユーザー入力のためtextContentでエスケープする
  function renderParticipants(participants) {
    memberCountEl.textContent = `${participants.length}人`;
    memberListEl.textContent = '';

    if (participants.length === 0) {
      const emptyItem = document.createElement('li');
      emptyItem.textContent = 'まだメンバーはいません';
      memberListEl.appendChild(emptyItem);
      return;
    }

    for (const participant of participants) {
      const item = document.createElement('li');
      item.textContent = participant.name;
      memberListEl.appendChild(item);
    }
  }

  function renderEvent(eventData) {
    titleEl.textContent = eventData.title;
    // 日付のハイフン(YYYY-MM-DD)をスラッシュ(YYYY/MM/DD)に置換
    dateEl.textContent = eventData.event_date.replace(/-/g, '/');
    daysLeftEl.textContent = daysLeftText(eventData.event_date);
    locationEl.textContent = eventData.location;
    authorEl.textContent = `${eventData.organizer_name} が誘っています`;
    renderParticipants(eventData.participants || []);
  }

  // イベント情報を読み込んで描画する
  async function loadEvent() {
    try {
      const response = await fetch(`/api/events/${publicId}`);
      if (!response.ok) {
        console.error('データの取得に失敗しました。ステータスコード:', response.status);
        titleEl.textContent = 'データを読み込めませんでした';
        memberListEl.textContent = '';
        return;
      }
      renderEvent(await response.json());
    } catch (error) {
      console.error('通信エラーが発生しました:', error);
      titleEl.textContent = '通信エラー';
      memberListEl.textContent = '';
    }
  }

  // 参加ボタン: POST後はレスポンスの参加者一覧でDOMを差し替え、参加後の状態にする
  async function joinEvent() {
    clearError();

    const name = nameInputEl.value.trim();
    if (!name) {
      showError('名前を入力してください');
      return;
    }

    joinBtnEl.disabled = true;
    try {
      const response = await fetch(`/api/events/${publicId}/participants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ name })
      });

      const data = await response.json();
      if (!response.ok) {
        showError(data.error || '参加に失敗しました');
        return;
      }

      renderParticipants(data.participants || []);
      applyJoinState(true);
    } catch (error) {
      console.error('API Error:', error);
      showError('通信エラーが発生しました。');
    } finally {
      joinBtnEl.disabled = false;
    }
  }

  applyJoinState(body.dataset.isParticipant === 'true');
  joinBtnEl.addEventListener('click', joinEvent);
  loadEvent();
});
