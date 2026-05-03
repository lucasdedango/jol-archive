# Outil de recherche avancée

Le site final est généré dans `jol_archive_output/site` et contient à la fois le HTML/JS/CSS et les données exportées.

## Recherche globale (type Google)

Le champ **Recherche globale (topics + réponses)** fonctionne ainsi :

- `abraknyde` → recherche simple (mot présent dans les titres/auteurs/topics et dans les réponses).
- `donjon abraknyde` → recherche multi-termes : les deux mots doivent être présents, dans n’importe quel ordre.
- `"donjon abraknyde"` → recherche exacte : la séquence doit apparaître dans cet ordre.

Les résultats affichent :
- les topics filtrés,
- puis les posts/réponses correspondants (avec lien direct vers le message).

## Filtres disponibles

- Mot-clé titre
- Auteur
- Forum source
- Date min / max
- Réponses min / max
- Vues min / max

## Pagination des résultats

- Navigation par pages via **Précédent / Suivant**
- Taille de page configurable

## Galeries

- Galerie images: `gallery.html?type=images`
- Galerie avatars: `gallery.html?type=avatars`
- Données: `galleries/images.js` et `galleries/avatars.js`
- Les fichiers absents localement sont ignorés
