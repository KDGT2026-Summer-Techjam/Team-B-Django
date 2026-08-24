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

  // コピー完了時に一瞬「コピーしました」と表示するフィードバック
  const showCopyFeedback = (button) => {
      const originalTitle = button.title;
      button.title = 'コピーしました';
      button.classList.add('icon-btn--done');
      setTimeout(() => {
          button.title = originalTitle;
          button.classList.remove('icon-btn--done');
      }, 1500);
  };

  // event_done.js が組み立てた共有用テキスト・URLをクリップボードにコピーする
  const copyShareTextToClipboard = async (button) => {
      const shareText = window.eventShareText || '';
      const shareUrl = window.eventShareUrl || window.location.href;
      try {
          await navigator.clipboard.writeText(`${shareText}\n\n${shareUrl}`);
          showCopyFeedback(button);
      } catch (error) {
          console.error('クリップボードへのコピーに失敗しました:', error);
      }
  };

  // コピーボタンの処理
  if (btnCopy) {
      btnCopy.addEventListener('click', () => {
          copyShareTextToClipboard(btnCopy);
      });
  }

  // シェアボタンの処理（Web Share API非対応環境ではコピーにフォールバック）
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
              copyShareTextToClipboard(btnShare);
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
