/* فلترة الرحلات في الرئيسية والأرشيف عند عرض قايماتها */
(function () {
	var filters = document.getElementById('trip-filters');
	if (!filters) {
		return;
	}
	filters.addEventListener('click', function (e) {
		var btn = e.target.closest('.filter-btn');
		if (!btn) {
			return;
		}
		filters.querySelectorAll('.filter-btn').forEach(function (b) {
			b.classList.remove('active');
		});
		btn.classList.add('active');

		var filter = btn.getAttribute('data-filter');
		document.querySelectorAll('.trip-card').forEach(function (card) {
			var types = (card.getAttribute('data-type') || '').split(',');
			var show = filter === 'all' || types.indexOf(filter) !== -1;
			card.style.display = show ? '' : 'none';
		});
	});
})();