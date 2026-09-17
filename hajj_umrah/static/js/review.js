(function () {
  'use strict';

  function initStarInput() {
    var container = document.getElementById('star-input');
    var input = document.getElementById('id_rating');
    if (!container || !input) return;

    var stars = Array.prototype.slice.call(
      container.querySelectorAll('.star-btn')
    );

    function paint(value) {
      stars.forEach(function (star) {
        var starValue = parseInt(star.getAttribute('data-value'), 10);
        var active = starValue <= value;
        star.classList.toggle('filled', active);
        star.setAttribute('aria-checked', active ? 'true' : 'false');
      });
    }

    function select(value) {
      input.value = value;
      paint(value);
    }

    stars.forEach(function (star) {
      var value = parseInt(star.getAttribute('data-value'), 10);
      star.addEventListener('click', function () {
        select(value);
      });
      star.addEventListener('mouseenter', function () {
        paint(value);
      });
    });

    container.addEventListener('mouseleave', function () {
      paint(parseInt(input.value, 10) || 0);
    });

    paint(parseInt(input.value, 10) || 0);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStarInput);
  } else {
    initStarInput();
  }
})();
