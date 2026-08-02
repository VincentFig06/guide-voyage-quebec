# Passeport de l'Explorateur du Québec

Guide de voyage ludique pour Léo (9 ans) et sa fratrie (7 ans) — voyage du 13 au 28 août 2026.

Le contenu (histoire, culture, activités...) vit dans `src/data/*.json` et alimente **deux formats** :
- une **PWA** installable sur iPhone/iPad, utilisable 100% hors connexion ;
- un **PDF imprimable** (passeport papier à tamponner/coller).

## Arborescence

```
src/                la PWA — source de vérité (HTML/CSS/JS, manifest, service worker, icônes, data/)
src/data/           6 fichiers JSON, un par étape (source unique de contenu, avec position lat/lon)
src/assets/maps/    cartes SVG statiques générées (carte globale + 6 mini-cartes "Tu es ici !")
docs/               copie générée de src/, servie par GitHub Pages — NE JAMAIS ÉDITER À LA MAIN
pdf/                script Python qui génère le PDF à partir des mêmes JSON
scripts/            scripts de build (régénération de docs/ et des cartes SVG)
```

`docs/` est entièrement régénéré depuis `src/` par `npm run build` (voir plus bas). Toute modification
faite directement dans `docs/` sera perdue au prochain build : on édite uniquement `src/`.

## Utiliser la PWA en local

Il faut la servir en http(s) (le Service Worker ne fonctionne pas en `file://`).

```bash
cd "CANADAforKid"
python3 -m http.server 8000
```
Puis ouvrir `http://localhost:8000/src/index.html` (ou `http://localhost:8000/docs/index.html` pour
tester exactement ce qui sera publié sur GitHub Pages).

**Installer sur iPhone/iPad** : héberger le dossier sur un petit serveur accessible depuis l'appareil
(réseau local, GitHub Pages, Netlify...), ouvrir l'URL dans Safari, bouton Partager → *Sur l'écran d'accueil*.
Après le premier chargement en ligne, tout (pages, données, badges) fonctionne hors connexion.

La progression (étapes validées, réponses aux jeux, dessins, photos souvenir) est stockée dans le
`localStorage` de l'appareil — propre à chaque téléphone/tablette, rien n'est envoyé nulle part.

## Publier sur GitHub Pages (docs/)

Après toute modification dans `src/`, régénérer `docs/` avant de commiter :
```bash
npm run build
# équivalent : bash scripts/build-docs.sh
```
Ce script supprime `docs/` et le recrée comme copie exacte de `src/` (rien à modifier à la main dedans).
GitHub Pages doit être configuré pour servir depuis le dossier `/docs` de la branche `main`.

## Régénérer le PDF

```bash
python3 pdf/generate_pdf.py
```
Lit les JSON depuis `src/data/` et produit `pdf/passeport-explorateur.html` (source imprimable) puis, si
Google Chrome est installé sur la machine, convertit automatiquement en
`pdf/Passeport-Explorateur-du-Quebec.pdf` (A4). Sans Chrome, ouvrir le HTML dans un navigateur et faire
*Imprimer → Enregistrer en PDF*.

## Modifier le contenu

Chaque étape est un fichier `src/data/etape-N-*.json` (schéma commun : `carnet`, `histoire`, `culture`,
`specialite`, `pointsInteret`, `motQuebecois`, `activites`, `filRouge`...). Éditer le JSON suffit : la
PWA et le PDF se mettent à jour tous les deux, sans dupliquer de contenu. Ne pas oublier `npm run build`
ensuite pour répercuter le changement sur `docs/`.

Types d'activités supportés (`activites[].type`) : `chercheEtTrouve`, `bingo`, `vraiFaux`, `quiz`,
`enigme`, `motsMeles`, `dessine`.

## Cartes du trajet

Écran d'accueil : une carte globale façon carte au trésor (`src/assets/maps/carte-globale.svg`), avec
les 6 étapes cliquables reliées par un itinéraire en pointillés numéroté. Chaque page d'étape affiche en
plus une mini-carte "Tu es ici !" recadrée sur sa région, avec un pin animé sur l'étape courante et les
étapes précédente/suivante en plus petit pour le contexte.

Tout est du SVG statique (aucune carte interactive en ligne, donc 100% fiable hors connexion) généré à
partir de `src/data/*.json` (champ `position: {lat, lon}` de chaque étape) :
```bash
python3 scripts/generate_maps.py
```
Régénère les 7 fichiers dans `src/assets/maps/`. Comme pour le contenu, ne pas oublier `npm run build`
ensuite pour répercuter le changement sur `docs/`, et penser à ajouter tout nouveau fichier de carte à
`CORE_ASSETS` dans `src/service-worker.js` pour qu'il reste disponible hors connexion.

## Icônes de l'app

Générées par script (`icons/*.png`, fleur de lys blanche sur fond bleu) — pas de dépendance à un
outil graphique externe. Pour les régénérer ou changer le motif, voir l'historique de conversation ou
recréer un script équivalent (écriture PNG pure Python, sans bibliothèque externe).
