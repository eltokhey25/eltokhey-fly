/* Eltokhey — light/dark theme controller
   1. Applies the saved theme (or the system preference) to <html data-theme>
   2. Toggles the theme from the header / drawer button and persists it
   3. Follows OS-level preference changes while the visitor has no saved choice

   base.html runs a tiny inline copy of step 1 in <head> to avoid a flash of
   the wrong theme; this file re-applies it (cheap) and owns the interaction.
*/
(function () {
	'use strict';

	var STORAGE_KEY = 'theme';
	var root = document.documentElement;
	var mql = window.matchMedia
		? window.matchMedia('(prefers-color-scheme: dark)')
		: null;

	var LABELS = {
		light: 'تفعيل الوضع المظلم',
		dark: 'تفعيل الوضع الفاتح'
	};

	var META_COLORS = {
		light: '#0f172a',
		dark: '#0b1220'
	};

	function readStored() {
		try {
			return localStorage.getItem(STORAGE_KEY);
		} catch (e) {
			return null;
		}
	}

	function writeStored(theme) {
		try {
			localStorage.setItem(STORAGE_KEY, theme);
		} catch (e) {
			/* private mode / storage disabled — theme still applies for this page */
		}
	}

	function systemTheme() {
		return mql && mql.matches ? 'dark' : 'light';
	}

	function currentTheme() {
		return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
	}

	function syncControls(theme) {
		var buttons = document.querySelectorAll('.theme-toggle, [data-theme-toggle]');
		var label = LABELS[theme];
		for (var i = 0; i < buttons.length; i++) {
			buttons[i].setAttribute('aria-label', label);
			buttons[i].setAttribute('title', label);
			buttons[i].setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
		}

		var meta = document.querySelector('meta[name="theme-color"]');
		if (meta) meta.setAttribute('content', META_COLORS[theme]);
	}

	function apply(theme, persist) {
		root.setAttribute('data-theme', theme);
		if (persist) writeStored(theme);
		syncControls(theme);
	}

	/* 1. Initial theme: saved choice wins, otherwise the OS preference. */
	var saved = readStored();
	apply(saved === 'dark' || saved === 'light' ? saved : systemTheme(), false);

	/* 2. Toggle. Delegated so every instance (header + drawer) works. */
	document.addEventListener('click', function (event) {
		var target = event.target;
		if (!target || !target.closest) return;
		var button = target.closest('.theme-toggle, [data-theme-toggle]');
		if (!button) return;
		event.preventDefault();
		apply(currentTheme() === 'dark' ? 'light' : 'dark', true);
	});

	/* 3. Follow the OS only while the visitor has no explicit choice. */
	if (mql) {
		var onSystemChange = function (event) {
			if (!readStored()) apply(event.matches ? 'dark' : 'light', false);
		};
		if (mql.addEventListener) {
			mql.addEventListener('change', onSystemChange);
		} else if (mql.addListener) {
			mql.addListener(onSystemChange);
		}
	}
})();
