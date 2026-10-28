/*
 * Latryn site config + shared behaviour.
 * EDIT THIS BLOCK ONCE: every CTA on every page reads from it.
 * Leave a value as "" and the link that uses it falls back gracefully
 * (social links hide, "Book a call" opens the contact form instead).
 */
window.LATRYN = {
  email: "contact@latryn.com",            // receives "Scope a program", "Book a call" and general enquiries
  careersEmail: "contact@latryn.com",     // shown on join.html for application questions
  latticeEndpoint: "",                     // Google Apps Script web app URL (see _source/apps-script/README.md); empty = application opens an email instead
  bookingUrl: "",                          // e.g. a Cal.com or Calendly link; empty = use the contact form
  social: {
    linkedin: "",                          // e.g. https://www.linkedin.com/company/latryn
    x: "",                                 // e.g. https://x.com/latryn
    youtube: ""                            // e.g. https://www.youtube.com/@latryn
  }
};

(function () {
  var C = window.LATRYN;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- smooth, inertial scrolling (Lenis, bundled in assets/vendor) ----------
     Native scroll position is still used, so sticky sections, scroll events and the
     keyboard all keep working. Touch devices keep their own native momentum. */
  var lenis = null;
  if (!reduce && window.Lenis) {
    lenis = new window.Lenis({ lerp: 0.085, wheelMultiplier: 0.95, smoothWheel: true });
    window.__lenis = lenis;
    if (window.gsap && window.ScrollTrigger) {
      /* homepage: one clock for smooth scroll and every scroll-linked animation */
      window.gsap.registerPlugin(window.ScrollTrigger);
      lenis.on("scroll", window.ScrollTrigger.update);
      window.gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
      window.gsap.ticker.lagSmoothing(0);
    } else {
      (function raf(time) { lenis.raf(time); requestAnimationFrame(raf); })(performance.now());
    }
  }
  var NAV_OFFSET = -96;
  function scrollToEl(el, center) {
    var off = center ? -Math.max(80, (innerHeight - el.offsetHeight) / 2) : NAV_OFFSET;
    var y = el.getBoundingClientRect().top + window.scrollY + off;
    if (lenis) lenis.scrollTo(y, { duration: 1.3, easing: function (t) { return 1 - Math.pow(1 - t, 4); } });
    else window.scrollTo({ top: y, behavior: reduce ? "auto" : "smooth" });
  }
  window.__scrollToEl = scrollToEl;
  /* same-page anchor links glide too */
  document.addEventListener("click", function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a || a.hasAttribute("data-cta") || a.getAttribute("href").length < 2) return;
    var el = document.getElementById(a.getAttribute("href").slice(1));
    if (!el) return;
    e.preventDefault();
    scrollToEl(el, false);
    history.replaceState(null, "", a.getAttribute("href"));
  });

  /* ---------- social + booking links ---------- */
  document.querySelectorAll("[data-social]").forEach(function (a) {
    var url = C.social[a.getAttribute("data-social")];
    if (url) { a.href = url; a.target = "_blank"; a.rel = "noopener"; }
    else { a.hidden = true; }
  });
  document.querySelectorAll("[data-book]").forEach(function (a) {
    if (C.bookingUrl) { a.href = C.bookingUrl; a.target = "_blank"; a.rel = "noopener"; }
  });
  document.querySelectorAll("[data-email]").forEach(function (a) {
    var key = a.getAttribute("data-email") === "careers" ? C.careersEmail : C.email;
    a.href = "mailto:" + key; if (!a.textContent.trim()) a.textContent = key;
  });

  /* ---------- prefill forms from CTA clicks or URL params ---------- */
  /* motion answers the action: every field a CTA changed flashes once, so the visitor sees what was filled in */
  function prefill(form, data, flash) {
    if (!form) return;
    Object.keys(data).forEach(function (k) {
      var f = form.elements[k];
      if (f && data[k] && f.value !== data[k]) {
        f.value = data[k];
        if (flash && !reduce) { f.classList.remove("changed"); void f.offsetWidth; setTimeout(function () { f.classList.add("changed"); }, 650); }
      }
    });
  }
  var contact = document.getElementById("contact-form");
  var apply = document.getElementById("apply-form");
  document.querySelectorAll("[data-cta]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      prefill(contact, { type: a.getAttribute("data-cta"), audience: a.getAttribute("data-audience") }, true);
      var target = contact;
      if (target && !(a.hasAttribute("data-book") && C.bookingUrl)) {
        e.preventDefault();
        scrollToEl(target, true);
        history.replaceState(null, "", "#" + target.id);
        setTimeout(function () { var f = target.querySelector("input,select,textarea"); if (f) f.focus({ preventScroll: true }); }, reduce ? 0 : 1300);
      }
    });
  });
  var params = new URLSearchParams(location.search);
  if (params.get("type") || params.get("audience")) prefill(contact, { type: params.get("type"), audience: params.get("audience") });
  if (params.get("role")) prefill(apply, { role: params.get("role") });

  /* ---------- forms compose an email (no backend needed) ---------- */
  function wire(form, to, subjectFn) {
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      var fd = new FormData(form), lines = [];
      fd.forEach(function (v, k) { if (v) lines.push(k.charAt(0).toUpperCase() + k.slice(1) + ": " + v); });
      var href = "mailto:" + to + "?subject=" + encodeURIComponent(subjectFn(fd)) + "&body=" + encodeURIComponent(lines.join("\n") + "\n\nSent from the Latryn website");
      window.location.href = href;
      var ok = form.querySelector(".form-ok");
      if (ok) { ok.hidden = false; ok.querySelector("a").href = href; }
      var btn = form.querySelector("button[type=submit]");
      if (btn && !btn.dataset.label) {
        btn.dataset.label = btn.innerHTML;
        btn.classList.add("sent"); btn.textContent = "Email ready to send";
        setTimeout(function () { btn.innerHTML = btn.dataset.label; btn.classList.remove("sent"); delete btn.dataset.label; }, 4000);
      }
    });
  }
  wire(contact, C.email, function (fd) { return (fd.get("type") || "Enquiry") + " | " + (fd.get("company") || fd.get("name")); });
  if (apply) lattice(apply);

  /* ---------- Lattice application (join.html) ----------
     Posts JSON with the resume as base64 to the Google Apps Script in _source/apps-script,
     which adds a row to the sheet, saves the resume to Drive and emails the applicant. */
  function lattice(form) {
    var MAX = 10 * 1024 * 1024, DOC = /\.(pdf|docx?)$/i;
    var fields = [].slice.call(form.querySelectorAll("[data-field]"));
    var file = form.elements.resume, drop = form.querySelector(".drop"), chosen = form.querySelector(".drop-file");
    var btn = form.querySelector("button[type=submit]"), status = form.querySelector(".form-ok");
    var count = document.getElementById("jcount"), bar = document.getElementById("jbar");

    function control(f) { return f.querySelector("input,select"); }
    function problem(f) {
      var group = f.getAttribute("data-group");
      if (group) return form.querySelector('input[name="' + group + '"]:checked') ? "" : f.getAttribute("data-msg");
      var el = control(f), v = el.validity;
      if (el.type === "file") {
        var x = el.files[0];
        if (!x) return f.getAttribute("data-msg");
        if (!DOC.test(x.name)) return "Upload a PDF or Word document (.pdf, .doc or .docx)";
        if (x.size > MAX) return "That file is " + (x.size / 1048576).toFixed(1) + " MB. The limit is 10 MB";
        return "";
      }
      if (v.valueMissing) return f.getAttribute("data-msg");
      if (el.name === "email" && !v.valid) return "Enter an email address like name@example.com";
      if (el.name === "phone" && !v.valid) return "Enter a 10-digit phone number, digits only";
      if (el.name === "portfolio" && !v.valid) return f.getAttribute("data-msg");
      return v.valid ? "" : f.getAttribute("data-msg");
    }
    function check(f) {
      var msg = problem(f), err = f.querySelector(".err");
      f.classList.toggle("bad", !!msg);
      if (err) err.textContent = msg;
      [].forEach.call(f.querySelectorAll("input,select"), function (el) { el.setAttribute("aria-invalid", msg ? "true" : "false"); });
      return !msg;
    }
    function needed(f) { return f.getAttribute("data-group") || control(f).required; }
    function progress() {
      var done = fields.filter(function (f) { return needed(f) && !problem(f); }).length;
      if (count && count.textContent !== String(done)) {
        count.textContent = done;
        count.classList.remove("tick"); void count.offsetWidth; count.classList.add("tick");
      }
      if (bar) { bar.style.transform = "scaleX(" + done / 10 + ")"; bar.parentNode.parentNode.classList.toggle("full", done === 10); }
      /* a section's number turns to "Complete" once every required answer in it is valid */
      [].forEach.call(form.querySelectorAll(":scope > fieldset"), function (s) {
        var req = fields.filter(function (f) { return s.contains(f) && needed(f); });
        s.classList.toggle("done", req.length > 0 && req.every(function (f) { return !problem(f); }));
      });
    }
    fields.forEach(function (f) {
      f.addEventListener("change", function () { if (f.dataset.touched || f.getAttribute("data-group")) check(f); f.dataset.touched = 1; progress(); });
      f.addEventListener("focusout", function (e) {
        if (f.getAttribute("data-group") && f.contains(e.relatedTarget)) return;
        var el = control(f);
        if (el.type !== "file" && (el.value || f.dataset.touched)) { f.dataset.touched = 1; check(f); }
      });
      f.addEventListener("input", function () { if (f.classList.contains("bad")) check(f); progress(); });
    });
    /* phone keeps digits only; a bare domain becomes a full link */
    form.elements.phone.addEventListener("input", function (e) { var t = e.target, d = t.value.replace(/\D/g, "").slice(0, 10); if (d !== t.value) t.value = d; });
    form.elements.portfolio.addEventListener("blur", function (e) { var t = e.target, v = t.value.trim(); if (v && !/^https?:\/\//i.test(v) && /\.[a-z]{2,}/i.test(v)) { t.value = "https://" + v; check(t.closest("[data-field]")); } });

    function showFile() {
      var x = file.files[0];
      drop.classList.toggle("has", !!x);
      chosen.hidden = !x;
      if (x) chosen.textContent = x.name + " · " + (x.size < 1048576 ? Math.max(1, Math.round(x.size / 1024)) + " KB" : (x.size / 1048576).toFixed(1) + " MB");
      check(file.closest("[data-field]")); progress();
    }
    file.addEventListener("change", showFile);
    ["dragenter", "dragover"].forEach(function (t) { drop.addEventListener(t, function () { drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (t) { drop.addEventListener(t, function () { drop.classList.remove("over"); }); });

    function busy(on) {
      btn.disabled = on; form.setAttribute("aria-busy", on ? "true" : "false");
      if (on) { btn.dataset.label = btn.innerHTML; btn.innerHTML = '<span class="spin" aria-hidden="true"></span> Sending application'; }
      else if (btn.dataset.label) { btn.innerHTML = btn.dataset.label; delete btn.dataset.label; }
    }
    function esc(t) { var n = document.createElement("i"); n.textContent = t; return n.innerHTML; }
    function say(html, bad) { status.hidden = false; status.classList.toggle("bad", !!bad); status.innerHTML = html; }
    function data() {
      var d = {};
      ["firstName", "lastName", "email", "phone", "qualification", "stream", "specialization", "availability", "portfolio", "role", "website"].forEach(function (k) {
        var el = form.elements[k]; d[k] = el ? String(el.value || "").trim() : "";
      });
      d.workTypes = [].map.call(form.querySelectorAll('input[name="workTypes"]:checked'), function (c) { return c.value; });
      return d;
    }
    function finish(d) {
      var card = form.closest(".join-card"), done = card.querySelector(".jdone");
      document.getElementById("jname").textContent = d.firstName;
      document.getElementById("jmail").textContent = d.email;
      /* the card eases from the form's height to the confirmation's instead of jumping */
      var h0 = card.offsetHeight;
      form.hidden = true; done.hidden = false;
      var h1 = card.offsetHeight;
      if (!reduce && card.animate) {
        card.style.overflow = "hidden";
        card.animate([{ height: h0 + "px" }, { height: h1 + "px" }], { duration: 450, easing: "cubic-bezier(.16,1,.3,1)" })
          .onfinish = function () { card.style.overflow = ""; };
      }
      requestAnimationFrame(function () { done.classList.add("on"); });
      scrollToEl(card, false); done.focus({ preventScroll: true });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var bad = fields.filter(function (f) { return !check(f); });
      progress();
      if (bad.length) {
        bad.forEach(function (f) { f.classList.remove("nudge"); void f.offsetWidth; f.classList.add("nudge"); });
        scrollToEl(bad[0], true);
        var el = bad[0].querySelector("input,select"); if (el) el.focus({ preventScroll: true });
        return;
      }
      var d = data();
      if (d.website) return; /* honeypot filled: a bot, drop it */
      if (!C.latticeEndpoint) {
        /* no backend configured yet: fall back to an email with the answers */
        var lines = Object.keys(d).filter(function (k) { return k !== "website" && d[k] && d[k].length; }).map(function (k) { return k + ": " + (d[k].join ? d[k].join(", ") : d[k]); });
        var href = "mailto:" + C.careersEmail + "?subject=" + encodeURIComponent("Lattice application | " + d.firstName + " " + d.lastName) + "&body=" + encodeURIComponent(lines.join("\n") + "\n\nPlease attach your resume to this email.\n\nSent from the Latryn website");
        window.location.href = href;
        say('Your email app should open with this application filled in. Attach your resume before you send it. If it did not open, <a href="' + href + '">open it here</a>.');
        return;
      }
      busy(true); status.hidden = true;
      var x = file.files[0], reader = new FileReader();
      reader.onerror = function () { busy(false); say("We could not read that file. Choose it again and resubmit.", true); };
      reader.onload = function () {
        d.resume = { name: x.name, type: x.type || "application/octet-stream", size: x.size, data: String(reader.result).split(",")[1] };
        /* text/plain keeps this a simple request, so Apps Script needs no CORS preflight */
        fetch(C.latticeEndpoint, { method: "POST", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify(d) })
          .then(function (r) { return r.json(); })
          .then(function (res) { if (!res || !res.ok) throw new Error(res && res.error); busy(false); finish(d); })
          .catch(function (err) {
            busy(false);
            var reason = err && err.message && !/fetch|network|JSON/i.test(err.message) ? esc(err.message) + ". " : "";
            say(reason + 'We could not send your application. Check your connection and try again, or email <a href="mailto:' + C.careersEmail + '">' + C.careersEmail + "</a> with your resume.", true);
          });
      };
      reader.readAsDataURL(x);
    });
    progress();
  }

  /* ---------- inner pages (the homepage runs its own motion) ---------- */
  if (document.body.getAttribute("data-page") === "home") return;

  /* heading stamp: the page title's ember square lands on load, later headings as they enter view */
  var h1dot = document.querySelector("h1 .dot");
  if (h1dot) setTimeout(function () { h1dot.classList.add("on"); }, reduce ? 0 : 380);
  if ("IntersectionObserver" in window) {
    var dio = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.querySelector(".dot").classList.add("on"); dio.unobserve(e.target); } });
    }, { threshold: .6 });
    document.querySelectorAll("h2").forEach(function (h) { if (h.querySelector(".dot")) dio.observe(h); });
  } else {
    document.querySelectorAll(".dot").forEach(function (d) { d.classList.add("on"); });
  }

  /* citations: following a [n] link highlights the reference it points to */
  function flashRef(id) {
    var el = document.getElementById(id); if (!el) return;
    var li = el.closest("li") || el; li.classList.remove("flash"); void li.offsetWidth; li.classList.add("flash");
  }
  document.querySelectorAll('.prose sup a[href^="#ref-"]').forEach(function (a) {
    a.addEventListener("click", function () { flashRef(a.getAttribute("href").slice(1)); });
  });
  if (/^#ref-\d+$/.test(location.hash)) flashRef(location.hash.slice(1));
  var bar = document.querySelector(".progress"), nav = document.getElementById("nav"), last = 0, tick = false;
  function onScroll() {
    var y = window.scrollY, h = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = "scaleX(" + (h > 0 ? y / h : 0) + ")";
    if (nav) { nav.classList.toggle("scrolled", y > 10); nav.classList.toggle("hide", y > last && y > 400); }
    last = y; tick = false;
  }
  addEventListener("scroll", function () { if (!tick) { requestAnimationFrame(onScroll); tick = true; } }, { passive: true });
  onScroll();
})();
