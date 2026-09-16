/* Dashboard core interactions */
(function () {
  'use strict';

  /* mobile sidebar toggle */
  var toggle = document.getElementById('nav-toggle');
  var closeBtn = document.getElementById('sidebar-close');
  var sidebar = document.getElementById('dash-sidebar');

  function openSidebar() { sidebar.classList.add('open'); }
  function closeSidebar() { sidebar.classList.remove('open'); }

  if (toggle) toggle.addEventListener('click', openSidebar);
  if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
  if (sidebar) {
    sidebar.addEventListener('click', function (e) {
      var target = e.target.closest('a');
      if (target && sidebar.classList.contains('open')) closeSidebar();
    });
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !toggle.contains(e.target) &&
          !(closeBtn && closeBtn.contains(e.target))) {
        closeSidebar();
      }
    });
  }

  /* auto-dismiss alerts */
  document.querySelectorAll('.alert[data-auto]').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(function () { el.remove(); }, 420);
    }, 4500);
  });

  /* confirm dialogs */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-confirm]');
    if (!btn) return;
    if (!window.confirm(btn.getAttribute('data-confirm'))) {
      e.preventDefault();
    }
  });

  /* file drop area */
  var drop = document.getElementById('file-drop');
  var fileInput = document.getElementById('id_file');
  if (drop && fileInput) {
    drop.addEventListener('click', function () { fileInput.click(); });
    drop.addEventListener('dragover', function (e) { e.preventDefault(); drop.classList.add('drag'); });
    drop.addEventListener('dragleave', function () { drop.classList.remove('drag'); });
    drop.addEventListener('drop', function (e) {
      e.preventDefault();
      drop.classList.remove('drag');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        updateDropLabel();
      }
    });
    fileInput.addEventListener('change', updateDropLabel);
    function updateDropLabel() {
      var name = fileInput.files && fileInput.files[0] ? fileInput.files[0].name : '';
      var el = document.querySelector('.file-drop em');
      if (el && name) el.textContent = name;
    }
  }
})();