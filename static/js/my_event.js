document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('events-container');

  // event_page.js の daysLeftText() と表記を揃える
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

  function isPastEvent(eventDate) {
    const target = new Date(`${eventDate}T00:00:00`);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return target < today;
  }

  // イベント名・場所はユーザー入力のため textContent でエスケープして描画する
  function buildEventCard(event) {
    const link = document.createElement('a');
    link.className = 'card-link';
    link.href = `/e/${event.public_id}/`;

    const scaleBox = document.createElement('div');
    scaleBox.className = 'preview-scale-box';

    const cardContainer = document.createElement('div');
    cardContainer.className = 'card-container preview-card';

    const cardContent = document.createElement('div');
    cardContent.className = 'card-content';

    const textSection = document.createElement('div');
    textSection.className = 'text-section';

    const titleEl = document.createElement('div');
    titleEl.className = 'input-title';
    titleEl.textContent = event.title;

    const dateEl = document.createElement('div');
    dateEl.className = 'input-date';
    dateEl.textContent = event.event_date.replace(/-/g, '/');

    const daysLeftEl = document.createElement('div');
    daysLeftEl.className = 'input-days-left';
    daysLeftEl.textContent = daysLeftText(event.event_date);

    const locationEl = document.createElement('div');
    locationEl.className = 'input-location';
    locationEl.textContent = event.location;

    textSection.append(titleEl, dateEl, daysLeftEl, locationEl);

    const imageSection = document.createElement('div');
    imageSection.className = 'image-section';
    imageSection.innerHTML = '<svg viewBox="0 0 24 24"><path d="M19,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,19H5V5H19V19M13.96,12.29L11.21,15.83L9.25,13.47L6.5,17H17.5L13.96,12.29Z" /></svg>';

    cardContent.append(textSection, imageSection);
    cardContainer.appendChild(cardContent);
    scaleBox.appendChild(cardContainer);
    link.appendChild(scaleBox);

    return link;
  }

  function buildSection(heading, events) {
    if (events.length === 0) {
      return null;
    }

    const section = document.createElement('div');
    section.className = 'event-section';

    const headingEl = document.createElement('h2');
    headingEl.className = 'section-heading';
    headingEl.textContent = heading;
    section.appendChild(headingEl);

    events.forEach(event => {
      section.appendChild(buildEventCard(event));
    });

    return section;
  }

  function showMessage(message) {
    container.textContent = '';
    const messageEl = document.createElement('p');
    messageEl.className = 'empty-message';
    messageEl.textContent = message;
    container.appendChild(messageEl);
  }

  function showEmptyState() {
    showMessage('参加予定・作成したイベントはまだありません。');

    const createLink = document.createElement('a');
    createLink.className = 'empty-cta';
    createLink.href = '/new';
    createLink.textContent = 'イベントを作成しよう';
    container.appendChild(createLink);
  }

  function render(events) {
    container.textContent = '';

    if (events.length === 0) {
      showEmptyState();
      return;
    }

    const upcoming = events.filter(event => !isPastEvent(event.event_date));
    const past = events.filter(event => isPastEvent(event.event_date)).reverse();

    const upcomingSection = buildSection('参加予定', upcoming);
    const pastSection = buildSection('終わったイベント', past);

    if (upcomingSection) {
      container.appendChild(upcomingSection);
    }
    if (pastSection) {
      container.appendChild(pastSection);
    }
  }

  async function loadEvents() {
    try {
      const response = await fetch('/api/my-events');
      if (!response.ok) {
        console.error('データの取得に失敗しました。ステータスコード:', response.status);
        showMessage('読み込みに失敗しました');
        return;
      }
      const data = await response.json();
      render(data.events || []);
    } catch (error) {
      console.error('通信エラーが発生しました:', error);
      showMessage('通信エラーが発生しました');
    }
  }

  loadEvents();
});
