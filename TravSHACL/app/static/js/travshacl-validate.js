// Shows a progress hint and prevents double submissions while a validation is running.
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('validate-form');
  var button = document.getElementById('validate-button');
  var status = document.getElementById('validate-status');
  if (!form || !button || !status) { return; }

  form.addEventListener('submit', function () {
    // Disable on the next tick; disabling synchronously would drop the button from the submitted data.
    setTimeout(function () { button.disabled = true; }, 0);
    status.hidden = false;
  });

  // The browser may restore this page from its cache when going back; reset the state.
  window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
      button.disabled = false;
      status.hidden = true;
    }
  });
});
