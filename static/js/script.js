document.addEventListener('DOMContentLoaded', () => {
  // 操作する要素を取得
  const trigger = document.getElementById('sidebar-trigger');
  const sidebar = document.getElementById('sidebar');

  // トリガー（左端30px）にマウスが入ったら、サイドバーに 'open' クラスを付ける
  trigger.addEventListener('mouseenter', () => {
      sidebar.classList.add('open');
  });

  // サイドバーからマウスが外れたら、'open' クラスを外す
  sidebar.addEventListener('mouseleave', () => {
      sidebar.classList.remove('open');
  });
});


/** ------------------------------
  event_done ページ用のボタンアクション
   ---------------------------------**/

document.addEventListener('DOMContentLoaded', () => {
  const btnCopy = document.getElementById('btn-copy');
  const btnShare = document.getElementById('btn-share');
  const btnReturn = document.getElementById('btn-return');

  // コピー完了を示すチェックマークアイコン（ホバーしなくても見た目で分かるようにする）
  const CHECK_ICON_SVG = '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';

  // 元のtitle/アイコンはクリックされる前に確定させておく。
  // showCopyFeedback内でbutton.titleを読み直すと、連打時に「コピーしました」状態を
  // 元の値として誤って記憶し、表示が固定されたまま戻らなくなる
  const captureOriginalState = (button) =>
      button ? { title: button.title, icon: button.innerHTML } : null;
  const copyFeedbackTimers = new WeakMap();

  // コピー完了時に一瞬アイコンをチェックマークに切り替えるフィードバック
  const showCopyFeedback = (button, original) => {
      clearTimeout(copyFeedbackTimers.get(button));
      button.title = 'コピーしました';
      button.innerHTML = CHECK_ICON_SVG;
      button.classList.add('icon-btn--done');
      const timerId = setTimeout(() => {
          button.title = original.title;
          button.innerHTML = original.icon;
          button.classList.remove('icon-btn--done');
      }, 1500);
      copyFeedbackTimers.set(button, timerId);
  };

  // event_done.js が組み立てた共有用テキスト・URLをクリップボードにコピーする
  const copyShareTextToClipboard = async (button, original) => {
      const shareText = window.eventShareText || '';
      const shareUrl = window.eventShareUrl || window.location.href;
      try {
          await navigator.clipboard.writeText(`${shareText}\n\n${shareUrl}`);
          showCopyFeedback(button, original);
      } catch (error) {
          console.error('クリップボードへのコピーに失敗しました:', error);
      }
  };

  // コピーボタンの処理
  const btnCopyOriginal = captureOriginalState(btnCopy);
  if (btnCopy) {
      btnCopy.addEventListener('click', () => {
          copyShareTextToClipboard(btnCopy, btnCopyOriginal);
      });
  }

  // シェアボタンの処理（Web Share API非対応環境ではコピーにフォールバック）
  const btnShareOriginal = captureOriginalState(btnShare);
  if (btnShare) {
      btnShare.addEventListener('click', async () => {
          const shareData = {
              title: document.getElementById('done-title')?.textContent || '',
              text: window.eventShareText || '',
              url: window.eventShareUrl || window.location.href,
          };

          if (navigator.share) {
              try {
                  await navigator.share(shareData);
              } catch (error) {
                  // ユーザーが共有シートを閉じた場合(AbortError)は何もしない
                  if (error.name !== 'AbortError') {
                      console.error('共有に失敗しました:', error);
                  }
              }
          } else {
              copyShareTextToClipboard(btnShare, btnShareOriginal);
          }
      });
  }

  // 戻るボタンの処理（※DjangoのURLルーティングに合わせて変更してください）
  if (btnReturn) {
      btnReturn.addEventListener('click', () => {
          // 例: ホーム画面（/）へ遷移する
          window.location.href = '/';
      });
  }
});
