function buttonSelected() {
  document.getElementById('vote-submit').disabled = false;
}

(function() {
  document.getElementsByName('action').forEach(elem => {
    if (elem.type === 'radio') {
      elem.checked = false;
      elem.onchange = buttonSelected;
    }
  });

  document.getElementById('vote-submit').disabled = true;
})();
