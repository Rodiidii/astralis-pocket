/* Astralis · effets de transition (optionnel, ~25 lignes, aucune dépendance).
   L'appli reconstruit tout le DOM à chaque rendu ; ce script détecte le démarrage et les
   vrais changements de page / de jeu pour ne rejouer les animations d'entrée qu'à ces moments-là. */
(function () {
  var root = document.documentElement, app = document.getElementById('app');
  if (!app) return;
  var last = '', timer = 0;
  function key() {
    var f = app.querySelector('.app-frame'), g = app.querySelector('.game-tab.active');
    return f ? (f.getAttribute('data-theme-section') || '') + '|' + (g ? g.getAttribute('data-game') : '') : '';
  }
  function fx(name, ms) {
    root.setAttribute('data-fx', name);
    clearTimeout(timer);
    timer = setTimeout(function () { root.removeAttribute('data-fx'); }, ms);
  }
  new MutationObserver(function () {
    var k = key();
    if (!k || k === last) return;
    fx(last ? 'nav' : 'boot', last ? 1300 : 2200);
    last = k;
  }).observe(app, { childList: true });
  /* horloge de la barre haute (le DOM est recréé à chaque rendu : on la met à jour en continu) */
  function tick(){var d=new Date(),t=('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2)+':'+('0'+d.getSeconds()).slice(-2);
    var n=document.querySelectorAll('[data-hud-clock]');for(var i=0;i<n.length;i++)n[i].textContent=t;}
  tick();setInterval(tick,1000);
  new MutationObserver(tick).observe(app,{childList:true});
  /* halo qui suit le pointeur sur les panneaux */
  document.addEventListener('pointermove',function(e){var el=e.target&&e.target.closest&&e.target.closest('.catalog-card,.dashboard-quick-stats article,.dashboard-universe-switch button,.panel,.glass-card');
    if(!el)return;var r=el.getBoundingClientRect();el.style.setProperty('--mx',(e.clientX-r.left)+'px');el.style.setProperty('--my',(e.clientY-r.top)+'px');},{passive:true});
})();
