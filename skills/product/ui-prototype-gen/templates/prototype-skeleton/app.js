const buttons = document.querySelectorAll("[data-screen]");
const screens = document.querySelectorAll(".screen");
const navItems = document.querySelectorAll(".nav-item");

function showScreen(targetId) {
  screens.forEach((screen) => {
    screen.classList.toggle("active", screen.id === targetId);
  });

  navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.screen === targetId);
  });
}

buttons.forEach((button) => {
  button.addEventListener("click", () => showScreen(button.dataset.screen));
});
