// Show/hide password buttons on the login and sign-up pages.
// Each <button class="password-toggle" aria-controls="<input id>"> starts
// hidden (so it never appears without JavaScript); this reveals it and makes
// it switch its input between type="password" and type="text".
document.querySelectorAll(".password-toggle").forEach(function (toggle) {
  const input = document.getElementById(toggle.getAttribute("aria-controls"));
  if (!input) return;
  toggle.hidden = false;
  toggle.addEventListener("click", function () {
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    toggle.textContent = showing ? "Show" : "Hide";
    toggle.setAttribute("aria-pressed", String(!showing));
  });
});
