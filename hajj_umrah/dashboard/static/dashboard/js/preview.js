/* Live preview: page nav, device presets, edit mode, inline-edit bridge */
(function () {
  'use strict';

  var frame = document.getElementById('preview-frame');
  var frameBox = document.getElementById('preview-frame-box');
  var pageSelect = document.getElementById('preview-url');
  var reloadBtn = document.getElementById('preview-reload');
  var tabBtn = document.getElementById('preview-tab');
  var editToggle = document.getElementById('preview-edit');
  var deviceBtns = document.querySelectorAll('[data-device]');
  var editorPanel = document.getElementById('editor-panel');
  var editorFrame = document.getElementById('editor-frame');
  var editorClose = document.getElementById('editor-close');
  var toasts = document.getElementById('preview-toasts');

  var DEVICES = {
    desktop: { width: '100%', label: 'كمبيوتر' },
    tablet: { width: '768px', label: 'تابلت' },
    mobile: { width: '390px', label: 'موبايل' }
  };

  function currentDevice() {
    var active = document.querySelector('.device-btn.active');
    return active ? (active.getAttribute('data-device') || 'desktop') : 'desktop';
  }

  function isEdit() { return editToggle ? editToggle.checked : false; }

  function frameUrl() {
    var base = frame.getAttribute('data-src') || '/';
    if (isEdit()) {
      base += (base.indexOf('?') === -1 ? '?' : '&') + 'edit=1';
    }
    return base;
  }

  function setFrame(url) {
    frame.setAttribute('data-src', url);
    frame.src = frameUrl();
  }

  function applyDevice(device) {
    var cfg = DEVICES[device] || DEVICES.desktop;
    frameBox.style.maxWidth = cfg.width;
    deviceBtns.forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-device') === device);
    });
  }

  if (pageSelect) {
    setFrame(pageSelect.value);
  }
  applyDevice('desktop');

  if (pageSelect) {
    pageSelect.addEventListener('change', function () {
      setFrame(pageSelect.value);
      closeEditor();
    });
  }
  if (reloadBtn) {
    reloadBtn.addEventListener('click', function () { frame.src = frameUrl(); });
  }
  if (tabBtn) {
    tabBtn.addEventListener('click', function (e) {
      e.preventDefault();
      var url = frame.getAttribute('data-src') || '/';
      window.open(url, '_blank', 'noopener');
    });
  }
  if (editToggle) {
    editToggle.addEventListener('change', function () {
      frame.src = frameUrl();
      if (!isEdit()) closeEditor();
    });
  }
  deviceBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyDevice(btn.getAttribute('data-device'));
    });
  });

  if (editorClose) {
    editorClose.addEventListener('click', closeEditor);
  }

  function openEditor(url) {
    if (!editorPanel || !editorFrame) return;
    editorFrame.src = url;
    editorPanel.classList.add('open');
    editorPanel.hidden = false;
  }
  function closeEditor() {
    if (editorFrame) editorFrame.src = 'about:blank';
    if (editorPanel) {
      editorPanel.classList.remove('open');
      editorPanel.hidden = true;
    }
  }
  window.closeEditor = closeEditor;

  /* bridge from inline editor inside the public-site iframe */
  window.addEventListener('message', function (e) {
    if (e.origin !== window.location.origin) return;
    var msg = e.data || {};
    if (msg.type === 'hu-dash-edit') {
      openEditor(msg.url);
      toast('فتح محرر تعديل ' + (msg.label || ''));
    } else if (msg.type === 'hu-dash-preview-reload') {
      frame.src = frameUrl();
    }
  });

  /* notifications when editor iframe submits (dashboard pages use same-origin message) */
  function toast(text) {
    if (!toasts) return;
    var t = document.createElement('div');
    t.className = 'toast';
    t.textContent = text;
    toasts.appendChild(t);
    setTimeout(function () { t.classList.add('out'); }, 2500);
    setTimeout(function () { t.remove(); }, 3000);
  }
})();