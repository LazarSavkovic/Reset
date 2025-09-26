  // Mobile nav dropdown (requires #hamburger + .dropdown-links in layout.html)
  const hamburgerBtn = document.getElementById('hamburger');
  const navEl = hamburgerBtn ? hamburgerBtn.closest('nav') : null;
  if (hamburgerBtn && navEl) {
    hamburgerBtn.addEventListener('click', () => {
      navEl.classList.toggle('is-open');
    });
  }