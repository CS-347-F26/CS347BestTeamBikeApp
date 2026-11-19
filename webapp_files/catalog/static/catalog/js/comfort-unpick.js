// comfort-unpick.js: on the routes page's comfort line, tapping the circle
// that's already picked un-picks it, so a rider can turn the comfort filter
// off without the Clear link. (Plain radio buttons can't be un-picked.)
//
// How: just before a press, remember whether that radio was already checked.
// The browser then "clicks" it (which keeps it checked); if it was checked
// before the press, we uncheck it. Without JavaScript the page still works.
document.querySelectorAll(".comfort-line input[type='radio']").forEach((radio) => {
  let wasChecked = false;
  const remember = () => {
    wasChecked = radio.checked;
  };

  // Mouse/finger presses land on the circle (the label).
  const label = document.querySelector(`label[for="${radio.id}"]`);
  if (label) label.addEventListener("pointerdown", remember);

  // Keyboard: browsers don't "click" a radio that's already checked when you
  // press Space, so un-pick it here instead. Arrow keys move between circles
  // as normal and aren't changed.
  radio.addEventListener("keydown", (event) => {
    if (event.key === " " && radio.checked) {
      event.preventDefault();
      radio.checked = false;
    }
  });

  radio.addEventListener("click", () => {
    if (wasChecked) radio.checked = false;
    wasChecked = false;
  });
});
