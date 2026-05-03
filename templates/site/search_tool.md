# Outil de recherche avancée

Cette page décrit la recherche avancée disponible sur `index.html`.

## Compatibilité multi-archives forum

L’interface est prévue pour gérer plusieurs pages/forums archivés :
- chaque topic conserve son `source_forum_url`;
- vous pouvez filtrer les résultats avec le champ **Forum source**.

## Filtres disponibles

- **Mot-clé titre** : recherche textuelle partielle dans le titre du topic.
- **Auteur** : filtre les topics selon le pseudo de l'auteur.
- **Forum source** : filtre sur l’URL source du forum/page crawlée.
- **Date min / Date max** : intervalle sur la date du premier post (`JJ/MM/AAAA`).
- **Réponses min / max** : intervalle numérique sur le nombre de réponses.
- **Vues min / max** : intervalle numérique sur le nombre de vues.

## Pagination des résultats

- Les topics ne sont plus affichés d’un seul bloc.
- Navigation par pages via **Précédent / Suivant**.
- Taille de page configurable (par défaut : 50).

## Détails techniques

- Les données sont chargées depuis `topics.js`.
- Le filtrage + pagination se font en JavaScript côté navigateur (`search.js`).
- Les topics sont rendus dynamiquement par `topic.html` + `topic.js` à partir de `topic_data/<topic_id>/<page>.json`.
- L’archive reste statique (pas de backend nécessaire).

## Galeries
- Galerie images: `gallery.html?type=images`
- Galerie avatars: `gallery.html?type=avatars`
- Données: `galleries/images.json` et `galleries/avatars.json`.
