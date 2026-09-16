/* Inline editing — runs on public pages when staff requests ?edit=1 */
(function () {
  'use strict';

  if (!window.DATA_AUTH || !DATA_AUTH.is_staff) return;
  document.body.classList.add('dash-edit-mode');

  /* resolve dashboard URLs (settings hashes arrive as plain dashboard paths) */
  var BASE = DATA_AUTH.dash_base || '/dashboard/';

  var TARGETS = [
    { sel: 'section.hero h1',               url: BASE + 'settings/', label: 'عنوان الرئيسية' },
    { sel: 'section.hero .container p',     url: BASE + 'settings/', label: 'وصف الرئيسية' },
    { sel: '#trips .section-head h2',       url: BASE + 'settings/', label: 'عنوان الرحلات' },
    { sel: '#trips .section-head p',        url: BASE + 'settings/', label: 'وصف الرحلات' },
    { sel: '.section.hero + .section .section-head h2, #main ~ .section:nth-of-type(2) .section-head h2', url: BASE + 'settings/', label: 'عنوان المزايا' },
    { sel: '.cta-title',                    url: BASE + 'settings/', label: 'عنوان الحث' },
    { sel: '.cta-sub',                      url: BASE + 'settings/', label: 'وصف الحث' },
    { sel: '.site-header .header-top span', url: BASE + 'settings/', label: 'الشريط العلوي' },
  ];

  function inPreview() {
    try { return window.self !== window.top; } catch (e) { return false; }
  }

  function openDash(url, label) {
    if (inPreview()) {
      window.parent.postMessage({ type: 'hu-dash-edit', url: url, label: label || '' }, window.location.origin);
    } else {
      window.location.href = url;
    }
  }

  function wrap(els, url, label) {
    Array.prototype.forEach.call(els, function (el) {
      el.classList.add('dash-editable');
      el.setAttribute('title', 'تعديل: ' + label);
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'dash-edit-btn';
      btn.textContent = '✎';
      btn.setAttribute('aria-label', 'تعديل ' + label);
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        openDash(url, label);
      });
      el.appendChild(btn);
    });
  }

  /* element-level targets */
  TARGETS.forEach(function (t) {
    var els = document.querySelectorAll(t.sel);
    if (els.length) wrap(els, t.url, t.label);
  });

  /* trip cards -> their own edit page */
  document.querySelectorAll('.trip-card').forEach(function (card) {
    var link = card.querySelector('a[href*="/trips/"], a[href*="trip_detail"]');
    var href = link && link.getAttribute('href');
    var m = href && href.match(/\/trips\/([\w-]+)\/?$/);
    if (!m) return;
    wrap([card], BASE + 'trips/' + m[1] + '/edit/', 'تعديل الرحلة');
  });

  /* trip detail summary box */
  document.querySelectorAll('.summary-box, .trip-hero .container').forEach(function (el) {
    var slugEl = document.querySelector('body.single-trip');
    var href = window.location.pathname.match(/\/trips\/([\w-]+)\/?$/);
    if (href) wrap([el], BASE + 'trips/' + href[1] + '/edit/', 'تعديل الرحلة');
  });

  /* admin bar */
  var bar = document.createElement('div');
  bar.className = 'dash-admin-bar';
  bar.innerHTML =
    '<span class="bar-badge">✎ وضع التحرير</span>' +
    '<span style="opacity:0.55;">|</span>' +
    '<a href="' + BASE + 'overview/">لوحة التحكم</a>' +
    '<a href="' + BASE + 'preview/">المعاينة</a>' +
    '<a href="' + BASE + 'settings/">الإعدادات</a>' +
    '<a href="' + BASE + 'sections/">الأقسام</a>' +
    '<a class="bar-exit" href="#" data-exit>إنهاء التحرير</a>';
  document.body.appendChild(bar);

  bar.querySelector('[data-exit]').addEventListener('click', function (e) {
    e.preventDefault();
    var url = window.location.href.replace(/[?&]edit=1/, '').replace(/[?&]$/, '');
    window.location.href = url;
  });

  var tip = document.createElement('div');
  tip.className = 'dash-edit-tip';
  tip.textContent = 'مرّر فوق أي عنصر واضغط ✎ لتعديله مباشرة';
  document.body.appendChild(tip);
  setTimeout(function () { tip.remove(); }, 5000);
})();