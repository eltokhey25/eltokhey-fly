/* إدارة خطوات برنامج السير وقوائم "يشمل / لا يشمل" في لوحة التحكم */
(function () {
	function init() {
		initItinerary();
		initRepeaters();
	}

	function initItinerary() {
		var blocks = document.querySelectorAll('.hu-itinerary-block');
		if (!blocks.length) {
			return;
		}

		blocks.forEach(function (block) {
			var wrap = block.querySelector('.hu-itinerary-wrap');
			if (!wrap) {
				return;
			}
			initItineraryBlock(block, wrap);
		});
	}

	function initItineraryBlock(block, wrap) {
		var index = parseInt(block.getAttribute('data-index'), 10);
		if (isNaN(index)) {
			index = wrap.querySelectorAll('.hu-step').length;
		}

		function renumber() {
			var steps = wrap.querySelectorAll('.hu-step');
			steps.forEach(function (step, i) {
				step.dataset.index = i;
				var label = step.querySelector('.hu-step-label');
				if (label) {
					label.textContent = i + 1;
				}
				var inner = step.querySelector('.hu-step-inner');
				var inputs = inner.querySelectorAll('input, textarea');
				inputs.forEach(function (input) {
					var name = input.getAttribute('name');
					if (name) {
						input.setAttribute('name', name.replace(/hu_itinerary\[\d+\]/, 'hu_itinerary[' + i + ']'));
					}
				});
			});
		}

		function addStep() {
			var div = document.createElement('div');
			div.className = 'hu-step';
			div.dataset.index = index;
			div.innerHTML =
				'<div class="hu-step-inner" style="border:1px solid #dcdcde;padding:10px;margin-bottom:10px;background:#f9f9f9;">' +
				'<p style="margin-top:0"><strong>الخطوة #<span class="hu-step-label">' + (index + 1) + '</span></strong></p>' +
				'<p><label>عنوان الخطوة (مثال: الوصول إلى مكة المكرمة)</label>' +
				'<input type="text" name="hu_itinerary[' + index + '][title]" class="widefat"></p>' +
				'<p><label>المدينة / الموقع</label>' +
				'<input type="text" name="hu_itinerary[' + index + '][city]" class="widefat" placeholder="مثال: مكة المكرمة"></p>' +
				'<p><label>تفاصيل الخطوة</label>' +
				'<textarea name="hu_itinerary[' + index + '][desc]" class="widefat" rows="3"></textarea></p>' +
				'<p><button type="button" class="button hu-remove-step">حذف الخطوة</button> ' +
				'<button type="button" class="button hu-move-up">▲ لأعلى</button> ' +
				'<button type="button" class="button hu-move-down">▼ لأسفل</button></p>' +
				'</div>';
			wrap.appendChild(div);
			index++;
			renumber();
		}

		wrap.addEventListener('click', function (e) {
			var btn = e.target.closest('button');
			if (!btn) {
				return;
			}
			var step = btn.closest('.hu-step');
			if (!step) {
				return;
			}
			if (btn.classList.contains('hu-remove-step')) {
				step.remove();
				renumber();
			} else if (btn.classList.contains('hu-move-up')) {
				var prev = step.previousElementSibling;
				if (prev) {
					wrap.insertBefore(step, prev);
					renumber();
				}
			} else if (btn.classList.contains('hu-move-down')) {
				var next = step.nextElementSibling;
				if (next) {
					wrap.insertBefore(next, step);
					renumber();
				}
			}
		});

		var addBtn = block.querySelector('.hu-add-step');
		if (addBtn) {
			addBtn.addEventListener('click', addStep);
		}
		var reorderBtn = block.querySelector('.hu-reorder-steps');
		if (reorderBtn) {
			reorderBtn.addEventListener('click', function () {
				var steps = Array.prototype.slice.call(wrap.querySelectorAll('.hu-step'));
				steps.forEach(function (step) {
					wrap.appendChild(step);
				});
				renumber();
			});
		}
	}

	function initRepeaters() {
		document.querySelectorAll('.hu-add-row').forEach(function (btn) {
			btn.addEventListener('click', function () {
				var repeater = btn.previousElementSibling;
				var name = repeater.getAttribute('data-name');
				var row = document.createElement('div');
				row.className = 'hu-repeater-row';
				row.style.marginBottom = '5px';
				var count = repeater.querySelectorAll('.hu-repeater-row').length;
				row.innerHTML = '<input type="text" name="' + name + '[' + count + ']" class="widefat">';
				repeater.appendChild(row);
			});
		});
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();