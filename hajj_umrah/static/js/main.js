/* Eltokhey — front-end behavior
   1. Sticky header glass effect on scroll
   2. Mobile slide-in drawer with backdrop, Escape, body-scroll lock
   3. Scroll reveal (IntersectionObserver) with reduced-motion fallback
   4. Number counters (stat cards) — count up once on scroll
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
	var els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .section');
	if (!('IntersectionObserver' in window)) {
		els.forEach(function (el) {
			el.classList.add('visible');
		});
	} else {
		var firstBatch = true;
		var io = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (!entry.isIntersecting) return;
					var el = entry.target;
					el.classList.add('visible');
					if (firstBatch) {
						el.style.willChange = 'auto';
						el.style.transition = 'none';
						requestAnimationFrame(function () { el.style.transition = ''; });
					} else {
						el.addEventListener('transitionend', function release(e) {
							if (e.target === el && e.propertyName === 'opacity') {
								el.style.willChange = 'auto';
								el.removeEventListener('transitionend', release);
							}
						});
					}
					io.unobserve(el);
				});
				firstBatch = false;
			},
			{ threshold: 0, rootMargin: '0px 0px -36px 0px' }
		);
		els.forEach(function (el) {
			io.observe(el);
		});
	}

	/* 4. Number counters (count up once on scroll) */
	var counters = document.querySelectorAll('.stat-card strong, [data-counter]');
	if (counters.length && 'IntersectionObserver' in window) {
		var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		var cio = new IntersectionObserver(function (entries, obs) {
			entries.forEach(function (entry) {
				if (!entry.isIntersecting) return;
				var el = entry.target;
				var m = el.textContent.match(/([0-9]+)/);
				if (!m) return obs.unobserve(el);
				var end = parseInt(m[1], 10);
				var pre = el.textContent.slice(0, m.index);
				var suf = el.textContent.slice(m.index + m[0].length);
				var t0 = null;
				var step = function (ts) {
					if (t0 === null) t0 = ts;
					var p = Math.min((ts - t0) / 1500, 1);
					el.textContent = pre + Math.round(end * (1 - Math.pow(1 - p, 3))) + suf;
					if (p < 1) requestAnimationFrame(step);
				};
				requestAnimationFrame(reduced ? function () { el.textContent = pre + end + suf; } : step);
				obs.unobserve(el);
			});
		}, { threshold: 0.4, rootMargin: '0px 0px -36px 0px' });
		counters.forEach(function (el) { cio.observe(el); });
	}
})();