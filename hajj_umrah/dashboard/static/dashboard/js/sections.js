/* Sections drag-and-drop reorder */
(function () {
  'use strict';

  var list = document.getElementById('section-list');
  if (!list) return;

  var items = Array.prototype.slice.call(list.querySelectorAll('.reorder-item'));
  var dragged = null;

  function renumber() {
    Array.prototype.forEach.call(list.querySelectorAll('.reorder-item'), function (item, i) {
      item.querySelector('.reorder-num').textContent = i + 1;
    });
  }

  items.forEach(function (item) {
    item.addEventListener('dragstart', function (e) {
      dragged = item;
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    item.addEventListener('dragend', function () {
      item.classList.remove('dragging');
      dragged = null;
      renumber();
    });
    item.addEventListener('dragover', function (e) {
      e.preventDefault();
      if (!dragged || dragged === item) return;
      var rect = item.getBoundingClientRect();
      var after = e.clientY > rect.top + rect.height / 2;
      list.insertBefore(dragged, after ? item.nextSibling : item);
      renumber();
    });
    item.addEventListener('drop', function (e) {
      e.preventDefault();
    });
  });
})();