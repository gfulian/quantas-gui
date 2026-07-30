/* Apply the operating-system theme before Dash hydrates the application shell. */
(function bootstrapQuantasTheme() {
  const root = document.documentElement;
  const media = window.matchMedia
    ? window.matchMedia("(prefers-color-scheme: light)")
    : null;

  function applySystemTheme() {
    const configuredTheme = root.getAttribute("data-q-theme") || "system";
    if (configuredTheme !== "system") {
      return;
    }
    const effectiveTheme = media && media.matches ? "light" : "dark";
    root.setAttribute("data-q-theme", "system");
    root.setAttribute("data-q-effective-theme", effectiveTheme);
  }

  applySystemTheme();
  if (media && media.addEventListener) {
    media.addEventListener("change", applySystemTheme);
  } else if (media && media.addListener) {
    media.addListener(applySystemTheme);
  }
})();
