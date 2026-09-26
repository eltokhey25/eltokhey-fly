/* Chatbot widget: chat UI + in-chat booking flow (all Arabic, RTL). */
(function () {
  'use strict';

  var API = '/api/chat/';
  var BOOKING_API = '/api/chat/booking/';
  var TRIPS_API = '/api/chat/trips/';
  var KEY = 'chatbot_history_v1';
  var TEASER_KEY = 'chatbot_teaser_seen';
  var CHAT_PAGE = '/chat/';
  var MOBILE_MAX = 768;
  var MAX = 20;

  var history = [];
  var isOpen = false;
  var isLoading = false;

  /* Booking flow state: null | 'trips' | 'form' | 'summary' | 'done' */
  var booking = null;
  var trips = [];

  try {
    var saved = sessionStorage.getItem(KEY);
    if (saved) history = JSON.parse(saved);
  } catch (e) { history = []; }

  function el(id) { return document.getElementById(id); }
  function messagesEl() { return el('chatbot-messages'); }

  function csrfToken() {
    var input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  function save() {
    try { sessionStorage.setItem(KEY, JSON.stringify(history.slice(-MAX))); } catch (e) {}
  }

  function scroll() {
    var c = messagesEl();
    if (c) c.scrollTop = c.scrollHeight;
  }

  /* Any of these mean the model could not answer, so offer a human channel
     instead of leaving the visitor at a dead end. */
  var ERROR_MARKERS = ['مشغول', 'خطأ', 'بطيء', 'ضغط', 'غير متاح', 'تعذر', 'حصل خطأ'];
  function isErrorText(text) {
    for (var i = 0; i < ERROR_MARKERS.length; i++) {
      if (String(text || '').indexOf(ERROR_MARKERS[i]) !== -1) return true;
    }
    return false;
  }

  function addWhatsAppButton() {
    var c = messagesEl();
    if (!c || c.querySelector('.chatbot-wa-help')) return;
    var wrap = document.createElement('div');
    wrap.className = 'chatbot-wa-help';
    var a = document.createElement('a');
    a.className = 'chatbot-btn wa';
    a.href = 'https://wa.me/201095454012';
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = 'تواصل على واتساب';
    wrap.appendChild(a);
    c.appendChild(wrap);
    scroll();
  }

  /* ---------- plain messages ---------- */

  /* "14:32" under every bubble, 24h — matches how the panel header reads. */
  function stamp() {
    var d = new Date();
    var h = d.getHours();
    var m = d.getMinutes();
    return h + ':' + (m < 10 ? '0' + m : m);
  }

  function add(role, content, store) {
    var c = messagesEl();
    if (!c) return;
    var d = document.createElement('div');
    d.className = 'chatbot-msg ' + role;
    d.textContent = String(content == null ? '' : content)
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/__([^_]+)__/g, '$1')
      .replace(/^#{1,6}\s*/gm, '');
    var t = document.createElement('span');
    t.className = 'chatbot-time';
    t.textContent = stamp();
    d.appendChild(t);
    c.appendChild(d);
    if (store !== false) { history.push({ role: role, content: content }); save(); }
    scroll();
    return d;
  }

  function card() {
    var c = messagesEl();
    if (!c) return null;
    var d = document.createElement('div');
    d.className = 'chatbot-card';
    d.id = 'chatbot-booking-card';
    c.appendChild(d);
    scroll();
    return d;
  }

  function clearCard() {
    var d = el('chatbot-booking-card');
    if (d) d.remove();
  }

  /* Empty state: a friendly bot plate above the welcome line, so a brand-new
     visitor sees a face, not a bare transcript. */
  var BOT_GLYPH =
    '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" ' +
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
    '<rect x="3.5" y="7.5" width="17" height="12" rx="4"/>' +
    '<path d="M12 7.5V4.6"/><circle cx="12" cy="3.2" r="1.3" fill="currentColor" stroke="none"/>' +
    '<path d="M9.4 12.4v1.7M14.6 12.4v1.7"/><path d="M1.8 13h2.2M22.2 13H20"/></svg>';

  function emptyState() {
    var c = messagesEl();
    if (!c) return;
    var wrap = document.createElement('div');
    wrap.className = 'chatbot-empty';
    wrap.innerHTML =
      '<span class="chatbot-empty__art">' + BOT_GLYPH + '</span>' +
      '<div class="chatbot-empty__title">أهلاً بيك 👋</div>' +
      '<div class="chatbot-empty__sub">اسألني عن أي رحلة أو سعر أو موعد، وأنا معاك على مدار الساعة.</div>';
    c.appendChild(wrap);
  }

  function render() {
    var c = messagesEl();
    if (!c) return;
    c.innerHTML = '';
    if (history.length === 0) {
      emptyState();
      add('bot',
        'السلام عليكم 🌙\nأنا مساعد الطوخي الذكي للحج والعمرة 🤖\nأقدر أساعدك في:\n' +
        '✅ اختيار الرحلة المناسبة\n✅ معرفة الأسعار والمواعيد\n✅' +
        '✅ حجز مباشرة من هنا\n\nاسألني عن أي حاجة!', false);
      quick();
    } else {
      history.forEach(function (m) { add(m.role, m.content, false); });
      /* Re-draw the booking step so closing/reopening mid-booking is safe. */
      if (booking && booking.step !== 'done') drawBooking();
    }
    scroll();
  }

  /* ---------- quick actions ---------- */

  function quick() {
    var c = el('chatbot-quick');
    if (!c) return;
    c.innerHTML = '';
    ['عايز أعرف الرحلات', 'عايز أحجز', 'الأسعار'].forEach(function (t) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = t;
      b.onclick = function () { send(t); };
      c.appendChild(b);
    });
  }

  function hideQuick() {
    var c = el('chatbot-quick');
    if (c) c.innerHTML = '';
  }

  /* ---------- typing indicator ---------- */

  function typing() {
    var c = messagesEl();
    if (!c) return;
    var t = document.createElement('div');
    t.className = 'chatbot-typing';
    t.id = 'chatbot-typing';
    t.innerHTML = '<span></span><span></span><span></span>';
    c.appendChild(t);
    scroll();
  }

  function hideTyping() {
    var e = el('chatbot-typing');
    if (e) e.remove();
  }

  /* ---------- booking flow ---------- */

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function priceOf(trip) {
    if (trip.price_display) return trip.price_display;
    return trip.price ? trip.price + ' جنيه' : 'السعر قريباً';
  }

  function loadTrips() {
    return fetch(TRIPS_API, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (d) { return (d && d.trips) || []; })
      .catch(function () { return []; });
  }

  function stepTrips() {
    booking = { step: 'trips' };
    clearCard();
    var box = card();
    if (!box) return;
    box.innerHTML = '<div class="chatbot-card-title">اختر الرحلة اللي تناسبك 🤖</div>' +
      '<div class="chatbot-card-sub">دوس على "اختيار" وسأكملك باقي خطوات الحجز.</div>' +
      '<div class="chatbot-trip-loading">جاري تحميل الرحلات...</div>';
    add('bot', 'تمام! اختر الرحلة اللي عايز تحجزها:', false);

    loadTrips().then(function (list) {
      trips = list;
      if (!box.isConnected) box = card();
      if (!box) return;
      if (!list.length) {
        box.innerHTML = '<div class="chatbot-card-title">مفيش رحلات متاحة دلوقتي</div>' +
          '<div class="chatbot-card-sub">تواصل معنا على الواتساب 201095454012.</div>';
        return;
      }
      var html = '<div class="chatbot-card-title">اختر الرحلة اللي تناسبك 🤖</div>' +
        '<div class="chatbot-card-sub">دوس على "اختيار" وسأكملك باقي خطوات الحجز.</div>';
      list.forEach(function (t) {
        html += '<div class="chatbot-trip">' +
          '<div><div class="chatbot-trip-name">' + esc(t.name) + '</div>' +
          '<div class="chatbot-trip-price">' + esc(priceOf(t)) + '</div></div>' +
          '<button class="chatbot-btn" type="button" data-trip="' + esc(t.id) + '">اختيار</button>' +
          '</div>';
      });
      html += '<div class="chatbot-actions">' +
        '<a class="chatbot-btn ghost" href="/booking/">اكمل على صفحة الحجز</a>' +
        '<button class="chatbot-btn ghost" type="button" data-act="cancel">إلغاء</button>' +
        '</div>';
      box.innerHTML = html;
      box.querySelectorAll('[data-trip]').forEach(function (b) {
        b.onclick = function () { stepForm(b.getAttribute('data-trip')); };
      });
      box.querySelector('[data-act="cancel"]').onclick = function () { cancelBooking(); };
    });
  }

  function stepForm(tripId) {
    var trip = trips.filter(function (t) { return String(t.id) === String(tripId); })[0];
    booking = { step: 'form', trip: trip || null };
    clearCard();
    var box = card();
    if (!box) return;
    box.innerHTML =
      '<div class="chatbot-card-title">بيانات الحجز ✍️</div>' +
      '<div class="chatbot-card-sub">' + esc(trip ? trip.name : '') + '</div>' +
      '<div class="chatbot-form-error" id="chatbot-form-error"></div>' +
      '<div class="chatbot-field"><label for="cb-name">الاسم الكامل *</label>' +
      '<input id="cb-name" type="text" placeholder="مثال: أحمد محمد علي" autocomplete="name"></div>' +
      '<div class="chatbot-field"><label for="cb-phone">رقم الموبايل *</label>' +
      '<input id="cb-phone" type="tel" placeholder="01xxxxxxxxx" autocomplete="tel" inputmode="tel"></div>' +
      '<div class="chatbot-field"><label for="cb-email">الإيميل <span class="opt">(اختياري)</span></label>' +
      '<input id="cb-email" type="email" placeholder="name@example.com" autocomplete="email"></div>' +
      '<div class="chatbot-field"><label for="cb-people">عدد الأفراد *</label>' +
      '<input id="cb-people" type="number" min="1" max="50" value="1" inputmode="numeric"></div>' +
      '<div class="chatbot-field"><label for="cb-notes">ملاحظات <span class="opt">(اختياري)</span></label>' +
      '<textarea id="cb-notes" placeholder="أي تفاصيل تحب نعرفها"></textarea></div>' +
      '<div class="chatbot-actions">' +
      '<button class="chatbot-btn" type="button" data-act="next">التالي</button>' +
      '<button class="chatbot-btn ghost" type="button" data-act="back">رجوع</button>' +
      '<a class="chatbot-btn ghost" href="/booking/?trip=' + esc(tripId) + '">اكمل على صفحة الحجز</a>' +
      '</div>';
    box.querySelector('[data-act="next"]').onclick = function () { stepSummary(); };
    box.querySelector('[data-act="back"]').onclick = function () { stepTrips(); };
    var name = el('cb-name');
    if (name) name.focus();
  }

  function showError(msg) {
    var e = el('chatbot-form-error');
    if (e) { e.textContent = msg; e.classList.add('show'); }
  }

  function stepSummary() {
    var name = (el('cb-name') && el('cb-name').value || '').trim();
    var phone = (el('cb-phone') && el('cb-phone').value || '').trim();
    var email = (el('cb-email') && el('cb-email').value || '').trim();
    var people = (el('cb-people') && el('cb-people').value || '1').trim();
    var notes = (el('cb-notes') && el('cb-notes').value || '').trim();

    if (name.length < 2) return showError('من فضلك اكتب الاسم بالكامل.');
    if (!/^[\d\s+()-]{6,20}$/.test(phone)) return showError('رقم الموبايل غير صحيح.');
    if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) return showError('البريد الإلكتروني غير صحيح.');

    booking = {
      step: 'summary',
      trip: booking && booking.trip,
      name: name, phone: phone, email: email,
      people: people, notes: notes
    };
    clearCard();
    var box = card();
    if (!box) return;
    var t = booking.trip;
    var rows = [
      ['الرحلة', t ? t.name : '—'],
      ['الاسم', name],
      ['الموبايل', phone],
      ['الإيميل', email || '—'],
      ['عدد الأفراد', people],
      ['ملاحظات', notes || 'لا توجد']
    ].map(function (r) {
      return '<div class="chatbot-summary-row"><span>' + esc(r[0]) +
        '</span><span>' + esc(r[1]) + '</span></div>';
    }).join('');
    box.innerHTML = '<div class="chatbot-card-title">تأكيد بيانات الحجز ✅</div>' +
      '<div class="chatbot-card-sub">راجع البيانات كويس قبل ما تؤكد.</div>' + rows +
      '<div class="chatbot-actions">' +
      '<button class="chatbot-btn gold" type="button" data-act="confirm">تأكيد الحجز</button>' +
      '<button class="chatbot-btn ghost" type="button" data-act="edit">تعديل</button>' +
      '<button class="chatbot-btn ghost" type="button" data-act="cancel">إلغاء</button>' +
      '</div>';
    box.querySelector('[data-act="confirm"]').onclick = submitBooking;
    box.querySelector('[data-act="edit"]').onclick = function () { stepForm(t ? t.id : ''); };
    box.querySelector('[data-act="cancel"]').onclick = function () { cancelBooking(); };
  }

  function cancelBooking() {
    booking = null;
    clearCard();
    add('bot', 'تم إلغاء الحجز. لو محتاج أي حاجة تانية أنا موجود 🌙', false);
  }

  function submitBooking() {
    if (isLoading) return;
    var btn = document.querySelector('[data-act="confirm"]');
    if (btn) { btn.disabled = true; btn.textContent = 'جاري التأكيد...'; }
    isLoading = true;

    fetch(BOOKING_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        trip_id: booking && booking.trip ? booking.trip.id : null,
        trip_name: booking && booking.trip ? booking.trip.name : '',
        name: booking.name,
        phone: booking.phone,
        email: booking.email,
        number_of_people: booking.people,
        notes: booking.notes
      })
    })
      .then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, data: d }; });
      })
      .then(function (res) {
        if (!res.ok) {
          showError(res.data.error || 'حصل خطأ، حاول تاني.');
          if (btn) { btn.disabled = false; btn.textContent = 'تأكيد الحجز'; }
          return;
        }
        stepDone(res.data);
      })
      .catch(function () {
        showError('تعذر الاتصال بالسيرفر. حاول تاني.');
        if (btn) { btn.disabled = false; btn.textContent = 'تأكيد الحجز'; }
      })
      .then(function () { isLoading = false; });
  }

  function stepDone(data) {
    booking = { step: 'done' };
    clearCard();
    var box = card();
    if (!box) return;
    var ref = data.reference_code || '';
    box.innerHTML = '<div class="chatbot-success-icon">🎉</div>' +
      '<div class="chatbot-card-title" style="text-align:center">تم استلام حجزك بنجاح!</div>' +
      '<div class="chatbot-ref">' + esc(ref) + '</div>' +
      '<div class="chatbot-card-sub" style="text-align:center">' +
      'سنتواصل معك على الواتساب لتأكيد التفاصيل. شكراً لثقتك 🌙</div>' +
      '<div class="chatbot-actions" style="justify-content:center">' +
      '<button class="chatbot-btn" type="button" data-act="copy">نسخ رقم الحجز</button>' +
      '<button class="chatbot-btn ghost" type="button" data-act="close">حسناً</button>' +
      '</div>';

    var copy = box.querySelector('[data-act="copy"]');
    copy.onclick = function () {
      var done = function () { copy.textContent = 'تم النسخ ✅'; setTimeout(function () { copy.textContent = 'نسخ رقم الحجز'; }, 1800); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(ref).then(done, done);
      } else {
        done();
      }
    };
    box.querySelector('[data-act="close"]').onclick = function () {
      booking = null;
      clearCard();
      add('bot', 'تحب تسأل عن حاجة تانية؟ 🌙', false);
    };
    add('bot', data.message || 'تم استلام حجزك بنجاح!', false);
  }

  function drawBooking() {
    if (!booking) return;
    if (booking.step === 'trips') stepTrips();
    else if (booking.step === 'form') stepForm(booking.trip ? booking.trip.id : '');
  }

  /* ---------- sending ---------- */

  function send(text) {
    if (!text || isLoading) return;
    var inp = el('chatbot-input');
    if (inp) inp.value = '';
    hideQuick();
    hideTeaser();
    add('user', text);
    isLoading = true;
    typing();

    fetch(API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
        'Accept': 'application/json'
      },
      body: JSON.stringify({ message: text, history: history.slice(-6) })
    })
      .then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, data: d }; });
      })
      .then(function (res) {
        hideTyping();
        if (!res.ok) {
          add('bot', (res.data && res.data.reply) || 'حصل خطأ مؤقت. حاول تاني.', false);
          addWhatsAppButton();
          return;
        }
        add('bot', res.data.reply, true);
        if (isErrorText(res.data.reply)) addWhatsAppButton();
        if (res.data.action === 'start_booking') {
          hideTyping();
          stepTrips();
        }
      })
      .catch(function () {
        hideTyping();
        add('bot', 'تعذر الاتصال. حاول تاني أو تواصل على الواتساب 201095454012.', false);
        addWhatsAppButton();
      })
      .then(function () { isLoading = false; });
  }

  /* ---------- teaser bubble ---------- */

  /* Desktop nudge that appears once per session, 4s after the page settles.
     Dismissed by the 8s timer, by tapping the launcher, or by sending. */
  function hideTeaser() {
    var teaser = el('chatbot-teaser');
    if (!teaser) return;
    try { sessionStorage.setItem(TEASER_KEY, '1'); } catch (e) {}
    teaser.classList.remove('is-visible');
    clearTimeout(teaser._hideTimer);
    teaser._hideTimer = setTimeout(function () { teaser.hidden = true; }, 400);
  }

  function initTeaser(toggle) {
    var teaser = el('chatbot-teaser');
    if (!teaser || !toggle || isMobile()) return;
    var seen = false;
    try { seen = sessionStorage.getItem(TEASER_KEY) === '1'; } catch (e) {}
    if (seen) return;

    var showTimer = setTimeout(function () {
      teaser.hidden = false;
      /* Flush layout so the opacity/translate transition has a starting frame to
         animate from. rAF is not safe here: it is throttled in a background tab
         and never fires at all in headless runs, which would strand the teaser
         at opacity 0 with the timer already running. */
      void teaser.offsetWidth;
      teaser.classList.add('is-visible');
      teaser._hideTimer = setTimeout(hideTeaser, 8000);
    }, 4000);

    toggle.addEventListener('click', function () {
      clearTimeout(showTimer);
      hideTeaser();
    }, true);
  }

  /* ---------- open / close ---------- */

  function lockScroll(on) {
    document.body.classList.toggle('chatbot-scroll-locked', !!on);
  }

  /* Same 768px edge the CSS uses, so panel and layout never disagree. */
  function isMobile() {
    return (window.innerWidth || 0) <= MOBILE_MAX;
  }

  /* Phones get a real page: an overlay panel cannot win against the on-screen
     keyboard, which covers the composer and leaves half a screen of chat. */
  function goChatPage() {
    var toggle = el('chatbot-toggle');
    var url = (toggle && toggle.getAttribute('data-chat-url')) || CHAT_PAGE;
    window.location.href = url;
  }

  function open() {
    if (isMobile()) { goChatPage(); return; }
    isOpen = true;
    var w = el('chatbot-window');
    var t = el('chatbot-toggle');
    hideTeaser();
    if (w) w.classList.add('open');
    if (t) {
      t.setAttribute('aria-expanded', 'true');
      t.classList.add('is-opening');
      setTimeout(function () { t.classList.remove('is-opening'); }, 520);
    }
    render();
    var inp = el('chatbot-input');
    if (inp) setTimeout(function () { inp.focus(); }, 80);
  }

  function close() {
    isOpen = false;
    var w = el('chatbot-window');
    var t = el('chatbot-toggle');
    if (w) w.classList.remove('open');
    if (t) t.setAttribute('aria-expanded', 'false');
    lockScroll(false);
  }

  /* ---------- init ---------- */

  document.addEventListener('DOMContentLoaded', function () {
    var toggle = el('chatbot-toggle');
    var closeBtn = el('chatbot-close');
    var input = el('chatbot-input');
    var sendBtn = el('chatbot-send');

    if (toggle) toggle.onclick = open;
    if (closeBtn) closeBtn.onclick = close;

    if (sendBtn) sendBtn.onclick = function () { send(input && input.value); };
    if (input) {
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          send(input.value);
        }
      });
      /* On the standalone page keep the composer above the soft keyboard by
         re-pinning the viewport height when it changes (iOS Safari). */
      if (window.visualViewport) {
        var vv = window.visualViewport;
        var pin = function () {
          document.documentElement.style.setProperty('--chat-vh', vv.height + 'px');
        };
        vv.addEventListener('resize', pin);
        pin();
      }
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen) close();
    });

    /* /chat/ has no launcher: render the transcript on load and make the back
       arrow behave like a real history step. */
    if (!toggle) {
      render();
      var back = document.querySelector('[data-chat-back]');
      if (back) {
        back.addEventListener('click', function (e) {
          if (document.referrer && document.referrer.indexOf(location.origin) === 0 && history.length > 1) {
            e.preventDefault();
            history.back();
          }
        });
      }
      if (input && !isMobile()) setTimeout(function () { input.focus(); }, 120);
    }

    initTeaser(toggle);
  });
})();
