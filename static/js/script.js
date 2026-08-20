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
