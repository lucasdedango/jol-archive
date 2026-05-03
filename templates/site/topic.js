(async function () {
  const params = new URLSearchParams(window.location.search);
  const topicId = params.get('topic_id');
  const page = Number(params.get('page') || '1');
  if (!topicId) {
    document.getElementById('topic-title').textContent = 'Topic introuvable';
    return;
  }

  const base=(window.DATA_BASE||"./").replace(/\/$/, "");
  const dataUrl = `${base}/topic_data/${topicId}/${page}.js`;
  await new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = dataUrl;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  }).catch(() => {
    document.getElementById('topic-title').textContent = 'Erreur de chargement';
  });

  const data = window.TOPIC_DATA;
  if (!data) return;
  const esc = s => String(s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');

  document.title = `${data.title} — page ${data.page_num}`;
  document.getElementById('topic-title').textContent = data.title || 'Sans titre';
  document.getElementById('topic-meta').textContent = `Sujet ${data.topic_id} — page ${data.page_num}/${data.last_page} — premier post : ${data.first_post_date || '?'}`;

  const nav = document.getElementById('topic-nav');
  const navLinks = [];
  if (data.page_num > 1) navLinks.push(`<a href="topic.html?topic_id=${data.topic_id}&page=${data.page_num - 1}">← Page précédente</a>`);
  navLinks.push(`<a href="${esc(data.original_topic_url)}">Voir le topic original sur JeuxOnline</a>`);
  if (data.page_num < data.last_page) navLinks.push(`<a href="topic.html?topic_id=${data.topic_id}&page=${data.page_num + 1}">Page suivante →</a>`);
  nav.innerHTML = navLinks.join(' — ');

  document.getElementById('posts').innerHTML = data.posts.map(p => {
    const avatar = p.avatar_local_path ? `<img src="${esc(p.avatar_local_path)}" alt="avatar" loading="lazy">` : '';
    return `<article class="post" id="post${p.post_id}"><div class="avatar">${avatar}</div><div class="post-body"><div class="post-author">${esc(p.author || '?')}</div><div class="meta">${esc(p.date_text || '')} — post #${p.post_id} — <a href="https://forums.jeuxonline.info/p/${p.post_id}#post${p.post_id}">original JOL</a></div><div>${p.content_html || ''}</div></div></article>`;
  }).join('');
})();
