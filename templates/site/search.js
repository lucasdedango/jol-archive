(function () {
  const container = document.getElementById('topics-container');
  const stats = document.getElementById('search-stats');
  const pageInfo = document.getElementById('page-info');
  const topics = (window.TOPICS_DATA || []).map(t => ({ ...t, isoDate: toIso(t.first_post_date) }));
  let filtered = topics;
  let currentPage = 1;

  function toIso(frDate) {
    if (!frDate || !frDate.includes('/')) return '';
    const [dd, mm, yyyy] = frDate.split('/');
    return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
  }

  function topicCard(t) {
    return `<div class="topic"><a href="topic.html?topic_id=${t.topic_id}&page=1"><strong>${escapeHtml(t.title || '')}</strong></a><div class="meta">par ${escapeHtml(t.author || '?')} — ${t.replies} réponses — ${t.views} vues — ${t.last_page} page(s) — premier post : ${escapeHtml(t.first_post_date || '?')} — source: ${escapeHtml(t.source_forum_url || '?')}</div></div>`;
  }

  function escapeHtml(s) { return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
  function getInput(id) { return document.getElementById(id).value.trim(); }
  function getNum(id) { const v = getInput(id); if (v === '') return null; const n = Number(v); return Number.isFinite(n) ? n : null; }
  function pageSize() { return Math.max(10, getNum('q-page-size') || 50); }

  function applyFilters() {
    const title = getInput('q-title').toLowerCase();
    const author = getInput('q-author').toLowerCase();
    const forum = getInput('q-forum').toLowerCase();
    const start = getInput('q-start');
    const end = getInput('q-end');
    const rMin = getNum('q-replies-min');
    const rMax = getNum('q-replies-max');
    const vMin = getNum('q-views-min');
    const vMax = getNum('q-views-max');

    filtered = topics.filter(t => {
      if (title && !(t.title || '').toLowerCase().includes(title)) return false;
      if (author && !(t.author || '').toLowerCase().includes(author)) return false;
      if (forum && !(t.source_forum_url || '').toLowerCase().includes(forum)) return false;
      if (start && (!t.isoDate || t.isoDate < start)) return false;
      if (end && (!t.isoDate || t.isoDate > end)) return false;
      if (rMin !== null && t.replies < rMin) return false;
      if (rMax !== null && t.replies > rMax) return false;
      if (vMin !== null && t.views < vMin) return false;
      if (vMax !== null && t.views > vMax) return false;
      return true;
    });
    currentPage = 1;
    renderPage();
  }

  function renderPage() {
    const size = pageSize();
    const totalPages = Math.max(1, Math.ceil(filtered.length / size));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const startIdx = (currentPage - 1) * size;
    const pageItems = filtered.slice(startIdx, startIdx + size);

    container.innerHTML = pageItems.map(topicCard).join('');
    stats.textContent = `${filtered.length} résultat(s) sur ${topics.length}`;
    pageInfo.textContent = `Page ${currentPage}/${totalPages}`;
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
  }

  document.getElementById('apply-search').addEventListener('click', applyFilters);
  document.getElementById('reset-search').addEventListener('click', () => {
    ['q-title','q-author','q-forum','q-start','q-end','q-replies-min','q-replies-max','q-views-min','q-views-max'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('q-page-size').value = '50';
    filtered = topics;
    currentPage = 1;
    renderPage();
  });
  document.getElementById('prev-page').addEventListener('click', () => { currentPage -= 1; renderPage(); });
  document.getElementById('next-page').addEventListener('click', () => { currentPage += 1; renderPage(); });
  document.getElementById('q-page-size').addEventListener('change', () => { currentPage = 1; renderPage(); });

  filtered = topics;
  renderPage();
})();
