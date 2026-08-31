/* Content injection: all prose lives in content.<lang>.js (window.DECK_CONTENT).
   Layout elements declare data-t="slideId.key"; notes asides declare data-notes="slideId".
   Swapping language = swapping the content file include. */
function applyContent(deck) {
  if (!deck || !deck.slides) { console.error("loader: DECK_CONTENT missing"); return; }
  document.title = deck.deckTitle;
  document.querySelectorAll("[data-t]").forEach(function (el) {
    var ref = el.getAttribute("data-t");
    var dot = ref.indexOf(".");
    var slide = ref.slice(0, dot), key = ref.slice(dot + 1);
    var entry = deck.slides[slide];
    if (entry && entry[key] !== undefined) {
      el.innerHTML = entry[key];
    } else {
      console.error("loader: missing content for " + ref);
      el.innerHTML = "⚠ " + ref;
    }
  });
  document.querySelectorAll("aside.notes[data-notes]").forEach(function (el) {
    var slide = el.getAttribute("data-notes");
    var entry = deck.slides[slide];
    if (entry && entry.notes) { el.innerHTML = entry.notes; }
    else { console.error("loader: missing notes for " + slide); }
  });
}
document.addEventListener("DOMContentLoaded", function () { applyContent(window.DECK_CONTENT); });
