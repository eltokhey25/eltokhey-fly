/* Trip itinerary editor — builds JSON into #id_itinerary_json */
(function () {
  'use strict';

  var hidden = document.getElementById('id_itinerary_json');
  var wrap = document.getElementById('itinerary-wrap');
  var addBtn = document.getElementById('itin-add');

  if (!hidden || !wrap) return;

  function readJson() {
    try {
      var data = JSON.parse(hidden.value || '[]');
      return Array.isArray(data) ? data : [];
    } catch (e) {
      return [];
    }
  }

  function render() {
    wrap.innerHTML = '';
    var steps = readJson();
    if (!steps.length) steps = [{ title: '', city: '', desc: '' }];
    steps.forEach(function (step, i) {
      wrap.appendChild(buildRow(step, i));
    });
    wrap.dispatchEvent(new CustomEvent('itin:rendered'));
  }

  function buildRow(step, i) {
    var row = document.createElement('div');
    row.className = 'itin-step';
    row.dataset.index = i;

    var head = document.createElement('div');
    head.className = 'itin-step-head';
    var label = document.createElement('strong');
    label.className = 'step-label';
    label.textContent = 'الخطوة #' + (i + 1);
    var tools = document.createElement('div');
    tools.className = 'step-tools';

    var up = mkBtn('▲', 'gold', 'تحريك لأعلى');
    var down = mkBtn('▼', 'gold', 'تحريك لأسفل');
    var del = mkBtn('🗑', 'red', 'حذف الخطوة');
    up.addEventListener('click', function () { move(i, -1); });
    down.addEventListener('click', function () { move(i, 1); });
    del.addEventListener('click', function () { removeStep(i); });

    tools.append(up, down, del);
    head.append(label, tools);

    var grid = document.createElement('div');
    grid.className = 'itin-grid';

    var title = field('عنوان الخطوة', 'text', step.title || '', 'مثال: الوصول إلى مكة المكرمة', 'title');
    var city = field('المدينة / الموقع', 'text', step.city || '', 'مثال: مكة المكرمة', 'city');
    var desc = field('تفاصيل الخطوة', 'textarea', step.desc || '', '', 'desc');
    title.classList.add('full-text');
    desc.classList.add('full');
    grid.append(title, city, desc);

    row.append(head, grid);
    return row;
  }

  function field(labelText, kind, value, placeholder, key) {
    var group = document.createElement('div');
    group.className = 'form-group';
    if (kind === 'textarea') group.classList.add('full');
    var lab = document.createElement('label');
    lab.textContent = labelText;
    var input;
    if (kind === 'textarea') {
      input = document.createElement('textarea');
      input.className = 'input textarea';
      input.rows = 2;
    } else {
      input = document.createElement('input');
      input.type = 'text';
      input.className = 'input';
      input.dir = 'rtl';
    }
    input.name = 'itin_' + key;
    input.placeholder = placeholder || '';
    input.value = value;
    input.addEventListener('input', save);
    group.append(lab, input);
    return group;
  }

  function mkBtn(text, tone, title) {
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = text;
    b.title = title;
    b.className = 'icon-btn mini ' + tone;
    return b;
  }

  function collect() {
    var rows = Array.prototype.slice.call(wrap.querySelectorAll('.itin-step'));
    var out = [];
    rows.forEach(function (row) {
      var title = row.querySelector('input[name="itin_title"]').value.trim();
      var city = row.querySelector('input[name="itin_city"]').value.trim();
      var desc = row.querySelector('textarea[name="itin_desc"]').value.trim();
      if (title || desc) out.push({ title: title, city: city, desc: desc });
    });
    hidden.value = JSON.stringify(out);
    return rows.length;
  }

  function save() { collect(); }

  function move(index, delta) {
    var steps = readJson();
    var target = index + delta;
    if (target < 0 || target >= steps.length) return;
    var tmp = steps[index];
    steps[index] = steps[target];
    steps[target] = tmp;
    hidden.value = JSON.stringify(steps);
    render();
  }

  function removeStep(index) {
    var steps = readJson();
    steps.splice(index, 1);
    hidden.value = JSON.stringify(steps);
    render();
  }

  if (addBtn) {
    addBtn.addEventListener('click', function () {
      var steps = readJson();
      steps.push({ title: '', city: '', desc: '' });
      hidden.value = JSON.stringify(steps);
      render();
    });
  }

  /* update step labels after render */
  wrap.addEventListener('itin:rendered', function () {
    Array.prototype.forEach.call(wrap.querySelectorAll('.itin-step'), function (row, i) {
      row.querySelector('.step-label').textContent = 'الخطوة #' + (i + 1);
    });
  });

  wrap.addEventListener('submit', function (e) { e.preventDefault(); save(); }, true);

  /* live slug auto-fill from trip name */
  (function () {
    var nameInput = document.getElementById('id_name');
    var slugInput = document.getElementById('id_slug');
    if (!nameInput || !slugInput) return;

    var lastAuto = '';
    var auto = true;

    function toSlug(value) {
      return String(value)
        .trim()
        .toLowerCase()
        .replace(/[\s_]+/g, '-')
        .replace(/[^a-z0-9-]/g, '')
        .replace(/-{2,}/g, '-')
        .replace(/^-|-$/g, '');
    }

    nameInput.addEventListener('input', function () {
      var slug = toSlug(nameInput.value);
      if (auto && (slugInput.value === '' || slugInput.value === lastAuto)) {
        slugInput.value = slug;
        lastAuto = slug;
      }
    });

    slugInput.addEventListener('input', function () {
      auto = slugInput.value === '' || slugInput.value === lastAuto;
      if (auto) lastAuto = slugInput.value;
    });
  })();

  render();
  save();
})();