(function () {
  const container = document.getElementById('topics-container');
  const postsContainer = document.getElementById('posts-container');
  const stats = document.getElementById('search-stats');
  const pageInfo = document.getElementById('page-info');
  const topics = (window.TOPICS_DATA || []).map(t => ({ ...t, isoDate: toIso(t.first_post_date) }));
  const posts = window.POSTS_SEARCH || [];
  let filtered = topics; let currentPage = 1;

  const esc = s => String(s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
  const toIso = d => (!d||!d.includes('/')) ? '' : `${d.split('/')[2]}-${d.split('/')[1].padStart(2,'0')}-${d.split('/')[0].padStart(2,'0')}`;
  const getInput = id => document.getElementById(id).value.trim();
  const getNum = id => { const v = getInput(id); if (v==='') return null; const n=Number(v); return Number.isFinite(n)?n:null; };
  const pageSize = () => Math.max(10, getNum('q-page-size') || 50);

  function parseQuery(raw) {
    const q = raw.trim().toLowerCase();
    const m = q.match(/^"(.+)"$/);
    if (m) return { phrase: m[1], terms: [] };
    return { phrase: '', terms: q.split(/\s+/).filter(Boolean) };
  }
  function matchText(text, query) {
    const hay = (text || '').toLowerCase();
    if (!query.phrase && query.terms.length === 0) return true;
    if (query.phrase) return hay.includes(query.phrase);
    return query.terms.every(term => hay.includes(term));
  }

  function applyFilters() {
    const qText = parseQuery(getInput('q-text'));
    const title = getInput('q-title').toLowerCase();
    const author = getInput('q-author').toLowerCase();
    const forum = getInput('q-forum').toLowerCase();
    const start = getInput('q-start'); const end = getInput('q-end');
    const rMin = getNum('q-replies-min'); const rMax = getNum('q-replies-max');
    const vMin = getNum('q-views-min'); const vMax = getNum('q-views-max');

    filtered = topics.filter(t => {
      const searchable = `${t.title||''} ${t.author||''}`;
      if (!matchText(searchable, qText)) return false;
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

    const matchedPosts = posts.filter(p => matchText(p.content_text, qText)).slice(0, 200);
    postsContainer.innerHTML = matchedPosts.map(p => `<div class="topic"><a href="topic.html?topic_id=${p.topic_id}&page=${p.page_num}#post${p.post_id}"><strong>Post #${p.post_id}</strong></a><div class="meta">topic ${p.topic_id} — ${esc(p.author)} — ${esc(p.date_text)}</div><div>${esc((p.content_text||'').slice(0,300))}</div></div>`).join('');

    currentPage = 1;
    renderPage();
  }

  function renderPage() {
    const size = pageSize(); const totalPages = Math.max(1, Math.ceil(filtered.length / size));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const startIdx = (currentPage - 1) * size;
    const pageItems = filtered.slice(startIdx, startIdx + size);
    container.innerHTML = pageItems.map(t => `<div class="topic"><a href="topic.html?topic_id=${t.topic_id}&page=1"><strong>${esc(t.title || '')}</strong></a><div class="meta">par ${esc(t.author || '?')} — ${t.replies} réponses — ${t.views} vues — ${t.last_page} page(s) — premier post : ${esc(t.first_post_date || '?')} — source: ${esc(t.source_forum_url || '?')}</div></div>`).join('');
    stats.textContent = `${filtered.length} résultat(s) topics sur ${topics.length}`;
    pageInfo.textContent = `Page ${currentPage}/${totalPages}`;
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
  }

  document.getElementById('apply-search').addEventListener('click', applyFilters);
  document.getElementById('reset-search').addEventListener('click', () => { ['q-text','q-title','q-author','q-forum','q-start','q-end','q-replies-min','q-replies-max','q-views-min','q-views-max'].forEach(id => document.getElementById(id).value=''); document.getElementById('q-page-size').value='50'; filtered=topics; currentPage=1; postsContainer.innerHTML=''; renderPage(); });
  document.getElementById('prev-page').addEventListener('click', () => { currentPage -= 1; renderPage(); });
  document.getElementById('next-page').addEventListener('click', () => { currentPage += 1; renderPage(); });
  document.getElementById('q-page-size').addEventListener('change', () => { currentPage = 1; renderPage(); });
  filtered=topics; renderPage();
})();
