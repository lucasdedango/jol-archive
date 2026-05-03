(async function () {
  const params = new URLSearchParams(window.location.search);
  const type = params.get('type') || 'images';
  const isAvatars = type === 'avatars';
  const res = await fetch(`galleries/${isAvatars ? 'avatars' : 'images'}.json`);
  if (!res.ok) {
    document.getElementById('gallery-title').textContent = 'Erreur de chargement';
    return;
  }
  const data = await res.json();
  const esc = s => String(s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');

  const title = isAvatars ? 'Mosaïque des avatars' : 'Mosaïque des images des topics';
  document.title = title;
  document.getElementById('gallery-title').textContent = title;
  document.getElementById('gallery-count').textContent = `${data.length} image(s)`;

  document.getElementById('gallery-grid').innerHTML = data.map(item => {
    const usageHtml = item.first_usage ? `<div class="small"><a href="topic.html?topic_id=${item.first_usage.topic_id}&page=${item.first_usage.page_num}#post${item.first_usage.post_id}">Voir le premier post local utilisant cette image</a></div>` : '';
    return `<div class="tile"><a href="../${esc(item.local_path)}"><img src="../${esc(item.local_path)}" loading="lazy" alt=""></a>${usageHtml}<div class="small">${esc(item.original_url || '')}</div></div>`;
  }).join('');
})();
