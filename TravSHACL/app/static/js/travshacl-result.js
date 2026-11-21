// Client-side filtering, searching, sorting, pagination, and CSV export of the validation result.
// Without JavaScript the server-rendered table is still complete.
document.addEventListener('DOMContentLoaded', function () {
  var table = document.getElementById('result-table');
  if (!table) { return; }
  document.documentElement.classList.add('js');

  var PAGE_SIZE = 100;
  var KEYS = ['instance', 'shape', 'result', 'finished'];
  var tbody = table.tBodies[0];
  var rows = Array.prototype.map.call(tbody.rows, function (tr) {
    var cells = Array.prototype.map.call(tr.cells, function (td) { return td.textContent.trim(); });
    return { el: tr, cells: cells, text: cells.join(' ').toLowerCase() };
  });

  var toolbar = document.getElementById('result-toolbar');
  var search = document.getElementById('result-search');
  var empty = document.getElementById('result-empty');
  var pager = document.getElementById('result-pager');
  var info = document.getElementById('page-info');
  var prev = document.getElementById('page-prev');
  var next = document.getElementById('page-next');
  var filterButtons = toolbar.querySelectorAll('[data-filter]');
  var headers = table.querySelectorAll('th[data-sort]');

  var state = { filter: 'all', query: '', sortIndex: -1, sortDir: 1, page: 0, visible: rows.slice() };
  toolbar.hidden = false;

  function refresh() {
    var q = state.query.toLowerCase();
    state.visible = rows.filter(function (r) {
      return (state.filter === 'all' || r.cells[2] === state.filter) && (!q || r.text.indexOf(q) !== -1);
    });
    if (state.sortIndex >= 0) {
      var i = state.sortIndex, d = state.sortDir;
      state.visible.sort(function (a, b) { return d * a.cells[i].localeCompare(b.cells[i]); });
    }
    render();
  }

  function render() {
    var pages = Math.max(1, Math.ceil(state.visible.length / PAGE_SIZE));
    state.page = Math.min(state.page, pages - 1);
    var start = state.page * PAGE_SIZE;
    var shown = state.visible.slice(start, start + PAGE_SIZE);

    while (tbody.firstChild) { tbody.removeChild(tbody.firstChild); }
    shown.forEach(function (r) { tbody.appendChild(r.el); });

    empty.hidden = state.visible.length > 0;
    pager.hidden = pages <= 1;
    info.textContent = 'Page ' + (state.page + 1) + ' of ' + pages + ' (' + state.visible.length + ' results)';
    prev.disabled = state.page === 0;
    next.disabled = state.page >= pages - 1;
  }

  Array.prototype.forEach.call(filterButtons, function (btn) {
    btn.addEventListener('click', function () {
      state.filter = btn.getAttribute('data-filter');
      state.page = 0;
      Array.prototype.forEach.call(filterButtons, function (b) {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      refresh();
    });
  });

  search.addEventListener('input', function () {
    state.query = search.value.trim();
    state.page = 0;
    refresh();
  });

  Array.prototype.forEach.call(headers, function (th) {
    th.tabIndex = 0;
    function sort() {
      var index = KEYS.indexOf(th.getAttribute('data-sort'));
      state.sortDir = state.sortIndex === index ? -state.sortDir : 1;
      state.sortIndex = index;
      state.page = 0;
      Array.prototype.forEach.call(headers, function (h) { h.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', state.sortDir === 1 ? 'ascending' : 'descending');
      refresh();
    }
    th.addEventListener('click', sort);
    th.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sort(); }
    });
  });

  prev.addEventListener('click', function () { state.page -= 1; render(); });
  next.addEventListener('click', function () { state.page += 1; render(); });

  // Exports what is currently filtered (all pages, not only the visible one).
  document.getElementById('download-csv').addEventListener('click', function () {
    function quote(value) { return '"' + value.replace(/"/g, '""') + '"'; }
    var lines = [['instance', 'shape', 'validation result', 'finished@shape'].map(quote).join(',')];
    state.visible.forEach(function (r) { lines.push(r.cells.map(quote).join(',')); });
    var blob = new Blob(['\ufeff' + lines.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'travshacl-result.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  });

  refresh();
});
