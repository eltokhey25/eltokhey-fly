/* PWA install banner — shows once, only when the app is not already installed. */
(function () {
  'use strict';

  var PROMPT_LS_KEY = 'eltokhey_pwa_dismissed';
  var promptShown = false;
  var deferredPrompt = null;

  var isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator && window.navigator.standalone === true);

  if (isStandalone) return;
  if (localStorage.getItem(PROMPT_LS_KEY)) return;

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
  });

  function dismiss() {
    var banner = document.getElementById('pwa-prompt');
    if (banner && banner.parentNode) banner.parentNode.removeChild(banner);
    promptShown = true;
    localStorage.setItem(PROMPT_LS_KEY, '1');
  }

  function showInstallHelp() {
    var note = document.getElementById('pwa-help');
    if (!note) return;
    note.style.display = 'block';
  }

  function install() {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function (choice) {
        localStorage.setItem(PROMPT_LS_KEY, '1');
        dismiss();
      });
      return;
    }
    /* iOS Safari / unsupported browsers have no beforeinstallprompt. */
    showInstallHelp();
  }

  function buildBanner() {
    if (document.getElementById('pwa-prompt')) return;
    var banner = document.createElement('div');
    banner.id = 'pwa-prompt';
    banner.className = 'pwa-prompt';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-live', 'polite');
    banner.innerHTML =
      '<div class="pwa-prompt-inner">' +
        '<button type="button" class="pwa-prompt-close" data-action="later" aria-label="إغلاق">✕</button>' +
        '<img class="pwa-prompt-icon" src="/static/img/favicon.png" alt="">' +
        '<p class="pwa-prompt-title">📱 نزّل تطبيق الطوخي للحج والعمرة على موبايلك</p>' +
        '<p class="pwa-prompt-actions">' +
          '<button type="button" class="pwa-prompt-btn" data-action="install">تنزيل</button>' +
          '<button type="button" class="pwa-prompt-later" data-action="later">لاحقاً</button>' +
        '</p>' +
        '<p class="pwa-prompt-help" id="pwa-help">' +
          'على آيفون/آيباد: افتح قائمة المشاركة (Safari) ثم اختار «إضافة إلى الشاشة الرئيسية».' +
        '</p>' +
      '</div>';
    document.body.appendChild(banner);

    banner.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-action]');
      if (!btn) return;
      if (btn.getAttribute('data-action') === 'install') install();
      else dismiss();
    });
  }

  window.addEventListener('load', function () {
    setTimeout(buildBanner, 2000);
  });
})();