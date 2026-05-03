# Outil de recherche avancée

Cette page décrit la recherche avancée disponible sur `index.html`.

## Filtres disponibles

- **Mot-clé titre** : recherche textuelle partielle dans le titre du topic.
- **Auteur** : filtre les topics selon le pseudo de l'auteur.
- **Date min / Date max** : intervalle sur la date du premier post (`JJ/MM/AAAA`).
- **Réponses min / max** : intervalle numérique sur le nombre de réponses.
- **Vues min / max** : intervalle numérique sur le nombre de vues.

## Utilisation

1. Ouvrir la page d'index du mini-site.
2. Renseigner un ou plusieurs filtres.
3. Cliquer sur **Filtrer**.
4. Cliquer sur **Réinitialiser** pour revenir à la liste complète.

## Détails techniques

- Les données sont chargées depuis `topics.js`.
- Le filtrage se fait en JavaScript côté navigateur (`search.js`).
- L'index reste statique (pas de backend nécessaire).

- Les topics sont rendus dynamiquement par `topic.html` + `topic.js` à partir de `topic_data/<topic_id>/<page>.json`.
