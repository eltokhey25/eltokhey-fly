/* ظهور العناصر بتأثير سلس عند التمرير */
(function () {
	var els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
	if (!('IntersectionObserver' in window)) {
		els.forEach(function (el) {
			el.classList.add('visible');
		});
		return;
	}
	var io = new IntersectionObserver(
		function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('visible');
					io.unobserve(entry.target);
				}
			});
		},
		{ threshold: 0, rootMargin: '0px 0px -30px 0px' }
	);
	els.forEach(function (el) {
		io.observe(el);
	});
})();

/* القائمة الجانبية للموبايل */
(function () {
	var toggle = document.getElementById('nav-toggle');
	var close = document.getElementById('nav-close');
	var nav = document.getElementById('main-nav');
	if (toggle && nav) {
		function open() {
			nav.classList.add('open');
			toggle.setAttribute('aria-expanded', 'true');
		}
		function closeNav() {
			nav.classList.remove('open');
			toggle.setAttribute('aria-expanded', 'false');
		}
		toggle.addEventListener('click', open);
		if (close) {
			close.addEventListener('click', closeNav);
		}
		document.addEventListener('click', function (e) {
			if (nav.classList.contains('open') && !nav.contains(e.target) && !toggle.contains(e.target)) {
				closeNav();
			}
		});
	}
})();
