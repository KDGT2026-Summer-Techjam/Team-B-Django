document.addEventListener("DOMContentLoaded", () => {
  // 操作する要素を取得
  const trigger = document.getElementById("sidebar-trigger");
  const sidebar = document.getElementById("sidebar");

  // トリガー（左端30px）にマウスが入ったら、サイドバーに 'open' クラスを付ける
  trigger.addEventListener("mouseenter", () => {
    sidebar.classList.add("open");
  });

  // サイドバーからマウスが外れたら、'open' クラスを外す
  sidebar.addEventListener("mouseleave", () => {
    sidebar.classList.remove("open");
  });
});

/** ------------------------------
  event_done ページ用のボタンアクション
---------------------------------**/

document.addEventListener("DOMContentLoaded", () => {
  const btnCopy = document.getElementById("btn-copy");
  const btnShare = document.getElementById("btn-share");
  const btnReturn = document.getElementById("btn-return");

  // コピーボタンの処理（※仮のアラートです。後でクリップボード処理に書き換えます）
  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      alert("URLをコピーしました（※実装予定）");
    });
  }

  // シェアボタンの処理
  if (btnShare) {
    btnShare.addEventListener("click", () => {
      alert("シェア画面を開きます（※実装予定）");
    });
  }

  // 戻るボタンの処理（※DjangoのURLルーティングに合わせて変更してください）
  if (btnReturn) {
    btnReturn.addEventListener("click", () => {
      // 例: ホーム画面（/）へ遷移する
      window.location.href = "/";
    });
  }
});
