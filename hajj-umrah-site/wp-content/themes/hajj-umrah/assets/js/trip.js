/* إضافات صفحة الرحلة */
(function () {
	document.querySelectorAll('.timeline-item').forEach(function (item, i) {
		var dot = item.querySelector('.timeline-dot');
		if (dot) {
			dot.textContent = i + 1;
		}
	});
})();