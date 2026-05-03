(async function () {
  const params = new URLSearchParams(window.location.search);
  const type = params.get('type') || 'images';
  const isAvatars = type === 'avatars';

  await new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = `galleries/${isAvatars ? 'avatars' : 'images'}.js`;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  }).catch(() => {
    document.getElementById('gallery-title').textContent = 'Erreur de chargement';
  });

  const data = window.GALLERY_DATA;
  if (!data) return;
  const esc = s => String(s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
  const title = isAvatars ? 'Mosaïque des avatars' : 'Mosaïque des images des topics';
  document.title = title;
  document.getElementById('gallery-title').textContent = title;
  document.getElementById('gallery-count').textContent = `${data.length} image(s)`;
  document.getElementById('gallery-grid').innerHTML = data.map(item => {
    const usageHtml = item.first_usage ? `<div class="small"><a href="topic.html?topic_id=${item.first_usage.topic_id}&page=${item.first_usage.page_num}#post${item.first_usage.post_id}">Voir le premier post local utilisant cette image</a></div>` : '';
    return `<div class="tile"><a href="${esc(item.local_path)}"><img src="${esc(item.local_path)}" loading="lazy" alt=""></a>${usageHtml}<div class="small">${esc(item.original_url || '')}</div></div>`;
  }).join('');
})();
