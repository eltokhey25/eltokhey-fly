/* Eltokhey — front-end behavior
   1. Sticky header glass effect on scroll
   2. Mobile slide-in drawer with backdrop, Escape, body-scroll lock
   3. Scroll reveal (IntersectionObserver) with reduced-motion fallback
*/

(function () {
	'use strict';

	/* 1. Sticky header glass effect */
	var header = document.getElementById('site-header');
	if (header) {
		var updateHeader = function () {
			header.classList.toggle('scrolled', window.scrollY > 16);
		};
		updateHeader();
		window.addEventListener('scroll', updateHeader, { passive: true });
	}

	/* 2. Mobile drawer */
	var toggle = document.getElementById('nav-toggle');
	var close = document.getElementById('nav-close');
	var nav = document.getElementById('main-nav');
	var backdrop = document.getElementById('nav-backdrop');

	if (toggle && nav) {
		var setState = function (open) {
			nav.classList.toggle('open', open);
			if (backdrop) backdrop.classList.toggle('active', open);
			toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
			if (close) close.setAttribute('aria-expanded', open ? 'true' : 'false');
			document.body.classList.toggle('menu-open', open);
			document.body.style.overflow = open ? 'hidden' : '';
		};

		toggle.addEventListener('click', function () {
			setState(true);
		});
		if (close) close.addEventListener('click', function () {
			setState(false);
		});
		if (backdrop) backdrop.addEventListener('click', function () {
			setState(false);
		});
		nav.addEventListener('click', function (e) {
			if (e.target.closest('a')) setState(false);
		});
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape' && nav.classList.contains('open')) setState(false);
		});
	}

	/* 3. Scroll reveal */
	var els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
	if (!('IntersectionObserver' in window)) {
		els.forEach(function (el) {
			el.classList.add('visible');
		});
	} else {
		var io = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('visible');
						io.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0, rootMargin: '0px 0px -36px 0px' }
		);
		els.forEach(function (el) {
			io.observe(el);
		});
	}
})();