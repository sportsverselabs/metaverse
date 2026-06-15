/* Sportsverse — public website interactions. Vanilla JS, no dependencies.
   Forms are placeholders until the email service is connected (see docs). */
(function () {
  "use strict";

  var nav = document.getElementById("nav");
  var menuBtn = document.getElementById("menuBtn");
  var overlay = document.getElementById("overlayMenu");

  // Sticky nav background on scroll
  function onScroll() {
    if (window.scrollY > 40) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Fullscreen menu toggle
  function setMenu(open) {
    overlay.classList.toggle("open", open);
    overlay.setAttribute("aria-hidden", open ? "false" : "true");
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    menuBtn.classList.toggle("is-open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      setMenu(!overlay.classList.contains("open"));
    });
  }
  // Close menu when a link is clicked
  overlay && overlay.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () { setMenu(false); });
  });
  // Esc closes the menu
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setMenu(false);
  });

  // Scroll-reveal animations
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  // Current year in footer
  var yr = document.getElementById("yr");
  if (yr) yr.textContent = new Date().getFullYear();

  // Placeholder form handlers (no backend yet)
  function flash(id, msg) {
    var el = document.getElementById(id);
    if (el) { el.textContent = msg; el.style.color = "#19e3ff"; }
  }
  window.Sportsverse = {
    subscribe: function (e) {
      e.preventDefault();
      flash("newsMsg", "Thanks! You're on the list (placeholder — connect the email service to go live).");
      e.target.reset();
      return false;
    },
    contact: function (e) {
      e.preventDefault();
      flash("contactMsg", "Message captured locally (placeholder — wire to email before launch).");
      e.target.reset();
      return false;
    }
  };
})();
