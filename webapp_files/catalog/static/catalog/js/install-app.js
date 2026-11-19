document.addEventListener("DOMContentLoaded", () => {
  const installButton = document.getElementById("install-app-button");
  const installHelp = document.getElementById("ios-install-help");

  if (!installButton) return;

  const isInstalled =
    window.navigator.standalone === true ||
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    window.matchMedia("(display-mode: minimal-ui)").matches;

  let installPrompt = null;

  installButton.hidden = isInstalled;
  if (installHelp) {
    installHelp.hidden = true;
  }

  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault();
    installPrompt = event;
  });

  installButton.addEventListener("click", async () => {
    const isIOS =
      /iphone|ipad|ipod/i.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" &&
       navigator.maxTouchPoints > 1);

    if (isIOS) {
      if (installHelp) installHelp.hidden = false;
      return;
    }

    if (installPrompt) {
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      return;
    }

    if (installHelp) {
      installHelp.textContent =
        "Open the browser menu and choose Install app or Add to Home screen.";
      installHelp.hidden = false;
    }
  });

  window.addEventListener("appinstalled", () => {
    if (installHelp) installHelp.hidden = true;
    installButton.hidden = true;
  });
});