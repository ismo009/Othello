# Othello — Jeu avec Intelligence Artificielle

## Description

Implémentation complète du jeu **Othello** (aussi connu sous le nom de Reversi) en Python avec une interface graphique Pygame et une **IA très performante** basée sur des algorithmes classiques de théorie des jeux à deux joueurs.

Le projet a été développé dans le cadre du TP d'algorithmique de l'INSA, dont l'objectif est de concevoir un système IA capable de jouer à Othello contre un humain ou contre une autre IA.

---

## Structure du projet

```
Othello/
├── othello.py      # Logique du jeu (plateau, règles, coups valides)
├── ia.py           # Moteur d'IA (NegaMax, Alpha-Beta, évaluation)
├── main.py         # Interface graphique Pygame + boucle de jeu
├── sujettp.txt     # Sujet du TP
└── README.md       # Ce fichier
```

### Séparation en modules

Le code est volontairement séparé en **trois fichiers distincts** :

| Fichier | Rôle |
|---|---|
| `othello.py` | Contient uniquement la logique pure du jeu : représentation du plateau, calcul des coups valides, retournement des pions, détection de fin de partie. Ce module ne dépend d'aucune bibliothèque externe et peut être utilisé indépendamment. |
| `ia.py` | Le moteur d'intelligence artificielle. Importe `othello.py` pour manipuler le plateau. Aucune dépendance à Pygame. |
| `main.py` | L'interface graphique. Importe les deux autres modules pour les assembler. |

Ce découpage permet de tester chaque composant séparément et de les réutiliser facilement (par exemple, brancher un autre algorithme IA sans toucher à l'interface).

---

## Installation et lancement

### Prérequis

- Python 3.10+
- Pygame

### Installation

```bash
pip install pygame
```

### Lancement

```bash
python main.py
```

### Contrôles

| Touche / Action | Effet |
|---|---|
| Clic gauche | Jouer un coup (sur une case valide) |
| `N` | Nouvelle partie |
| `M` ou `Echap` | Retour au menu |
| `Echap` (au menu) | Quitter |

---

## Modes de jeu

Le menu principal propose trois modes :

1. **Humain vs Humain** — Deux joueurs humains sur le même écran.
2. **Humain vs IA** — Le joueur humain contrôle les Blancs, l'IA joue les Noirs.
3. **IA vs IA** — Deux instances de l'IA s'affrontent automatiquement.

---

## Règles implémentées

Les règles suivent le standard Othello :

- Le plateau est une grille **8×8**. La position initiale place 2 pions blancs et 2 pions noirs au centre.
- **Les Blancs commencent** (conformément au sujet du TP).
- Un joueur doit poser un pion de sorte à encadrer au moins un pion adverse (horizontalement, verticalement ou en diagonale). Les pions adverses encadrés sont **retournés**.
- Si un joueur ne peut pas jouer, il **passe son tour**. Si aucun des deux joueurs ne peut jouer, la **partie est terminée**.
- Le gagnant est celui qui possède **le plus de pions** à la fin.

---

## Interface graphique

### Choix de Pygame

Pygame a été choisi pour sa **simplicité d'utilisation** et sa bonne documentation. Il permet de créer une interface 2D fonctionnelle sans la lourdeur d'un framework GUI complet.

### Éléments visuels

- **Plateau vert** avec grille, rappelant un vrai plateau d'Othello, avec 4 points repères aux intersections classiques.
- **Coordonnées** A-H (colonnes) et 1-8 (lignes) autour du plateau.
- **Pions** avec ombres portées et reflets pour un rendu pseudo-3D.
- **Coups valides** affichés sous forme de petits cercles semi-transparents.
- **Prévisualisation** : en survolant une case jouable, le pion apparaît en transparence.
- **Animation de retournement** : les pions capturés s'animent avec un effet de rotation (réduction puis agrandissement du rayon).
- **Marqueurs** : le dernier coup joué est marqué en jaune, les pions retournés en orange.
- **Panneau latéral** affichant les scores, le tour actuel, le nombre de coups possibles, et les statistiques de l'IA.
- **Overlay de fin de partie** annonçant le résultat.

### Threading

L'IA réfléchit dans un **thread séparé** pour ne pas bloquer l'interface graphique pendant le calcul. Un indicateur animé « Analyse en cours... » informe le joueur.

---

## Architecture de l'IA

### Algorithme principal : NegaMax avec Alpha-Beta

#### Pourquoi NegaMax plutôt que Min-Max ?

L'algorithme **NegaMax** est une reformulation de Min-Max qui exploite la propriété suivante des jeux à somme nulle :

```
max(a, b) = -min(-a, -b)
```

Au lieu de maintenir deux fonctions distinctes (une pour maximiser, une pour minimiser), NegaMax utilise une seule fonction récursive en inversant le signe du score à chaque niveau. Le code résultant est **plus compact**, **moins sujet aux bugs**, et **tout aussi performant** que Min-Max classique.

#### Élagage Alpha-Beta

L'élagage **Alpha-Beta** est intégré directement dans NegaMax. Il permet de couper des branches de l'arbre de recherche qui ne peuvent pas influencer la décision finale :

- **Alpha** = meilleur score garanti pour le joueur courant
- **Beta** = meilleur score garanti pour l'adversaire

Quand `alpha >= beta`, la branche courante est inutile et on effectue une **coupe**. Cela réduit considérablement le nombre de nœuds explorés, passant de `O(b^d)` à `O(b^(d/2))` dans le meilleur cas (avec un bon tri des coups), où `b` est le facteur de branchement et `d` la profondeur.

### Optimisations

#### 1. Approfondissement itératif (Iterative Deepening)

Au lieu de chercher directement à profondeur maximale, l'IA effectue des recherches successives à profondeur 1, 2, 3, ... jusqu'à la profondeur maximale ou l'expiration du temps.

**Avantages :**
- Permet de toujours avoir un coup disponible même si le temps expire.
- Le meilleur coup de l'itération précédente est exploré en premier à l'itération suivante, ce qui améliore significativement les coupes Alpha-Beta.
- Le surcoût est négligeable car la majorité du temps est passé à la profondeur maximale.

#### 2. Table de transposition (Zobrist Hashing)

Une **table de transposition** stocke les résultats des positions déjà évaluées pour éviter de les recalculer. La clé de hachage utilise le **hashing de Zobrist** :

- On génère aléatoirement une valeur 64-bit pour chaque combinaison (case, couleur de pion).
- Le hash d'une position est le XOR de toutes ces valeurs pour les pions présents.
- Le hash est incrémentalement mis à jour lors des coups (très rapide).

Chaque entrée stocke :
- La **profondeur** de la recherche
- Le **score** trouvé
- Le **type** de borne (exacte, alpha = borne supérieure, beta = borne inférieure)
- Le **meilleur coup** trouvé (pour le tri)

**Justification** : À Othello, de nombreuses séquences de coups différentes mènent à la même position. La table de transposition évite d'explorer ces positions en double.

#### 3. Tri des coups (Move Ordering)

L'efficacité d'Alpha-Beta dépend fortement de l'**ordre d'exploration des coups**. Le tri est fait selon :

1. **Le meilleur coup de la table de transposition** est toujours exploré en premier.
2. **Les coins** (priorité maximale) — les cases les plus importantes à Othello.
3. **Les bords stables** ensuite.
4. **Les cases X et C** (diagonales et adjacentes aux coins) en dernier — car elles donnent souvent un avantage à l'adversaire.

#### 4. Résolution exacte en fin de partie (Endgame Solver)

Quand il reste **14 cases vides ou moins**, l'IA augmente sa profondeur de recherche pour couvrir toutes les cases restantes. Elle calcule alors le résultat **exact** de la partie (gagné/perdu/nul), pas une estimation heuristique.

#### 5. Opérations rapides (Make/Unmake)

Au lieu de créer une copie complète du plateau à chaque nœud de l'arbre (coûteux en mémoire et en temps), l'IA utilise des opérations **faire/défaire** (`jouer_coup_rapide` / `annuler_coup`) qui modifient le plateau en place et le restaurent après exploration. Cela réduit considérablement les allocations mémoire.

### Fonction d'évaluation

La fonction d'évaluation utilise une **stratégie mixte par phase**, conformément aux recommandations du sujet (stratégie « Mixte »). Elle combine 6 composantes, pondérées différemment selon la phase de la partie :

#### Composantes

| Composante | Description | Justification |
|---|---|---|
| **Positionnelle** | Score basé sur une table de poids statiques 8×8. Les coins valent +500, les cases X valent −250. | Les coins sont des pions permanents (impossibles à retourner). Les cases X donnent souvent le coin à l'adversaire. Les poids sont ajustés dynamiquement : si le coin est déjà pris, les cases X/C adjacentes ne sont plus pénalisées. |
| **Mobilité** | `100 × (coups joueur − coups adversaire) / (coups joueur + coups adversaire)` | Au Othello, il est crucial de maximiser ses options tout en limitant celles de l'adversaire. Un joueur sans coup est forcé de passer. |
| **Coins** | +250 par coin possédé, −250 par coin de l'adversaire. | Les coins sont les cases les plus stratégiques car ils sont **permanents** et permettent de stabiliser des bords entiers. |
| **Stabilité** | Nombre de pions stables (impossibles à retourner) normalisé. Calculé par propagation depuis les coins. | Les pions stables sont un avantage durable. Un coin pris permet de stabiliser progressivement tout un bord, puis un triangle entier. |
| **Frontières** | Pénalise les pions adjacents à des cases vides (exposés aux retournements). | Moins de pions frontières signifie une position plus « compacte » et plus difficile à attaquer. |
| **Parité** | Bonus si le joueur joue le dernier coup dans une région. | En fin de partie, le joueur qui joue en dernier dans une région fermée a un avantage tactique. |

#### Pondération par phase

| Phase | Pions sur le plateau | Composantes dominantes | Justification |
|---|---|---|---|
| **Ouverture** | ≤ 20 | Positionnelle ×1, Mobilité ×5, Coins ×10, Frontières ×2 | En début de partie, il faut maximiser ses options et prendre de bonnes positions. La mobilité est reine. |
| **Milieu** | 20 – 50 | Positionnelle ×0.5, Mobilité ×4, Coins ×15, Stabilité ×3, Frontières ×1.5, Parité ×1 | La stabilité devient importante. Les coins sont encore plus valorisés car ils commencent à verrouiller les bords. |
| **Fin** | > 50 | Diff. pions ×10, Coins ×20, Stabilité ×5, Parité ×3 | En fin de partie, seul le nombre final de pions compte. La résolution exacte (endgame solver) prend le relais quand ≤ 14 cases vides. |

### Paramètres de l'IA

| Paramètre | Valeur (Humain vs IA) | Valeur (IA vs IA) |
|---|---|---|
| Profondeur maximale | 10 | 8 |
| Temps maximum par coup | 5 secondes | 3 secondes |
| Résolution exacte | ≤ 14 cases vides | ≤ 14 cases vides |

### Statistiques affichées

Le panneau latéral affiche en temps réel après chaque coup de l'IA :

- **Profondeur** atteinte lors de la recherche
- **Nombre de nœuds** explorés dans l'arbre
- **Coupes Alpha-Beta** effectuées (branches évitées)
- **Hits de la table de transposition** (positions déjà connues)
- **Temps** de calcul du coup

---

## Références

- Russell, S., Norvig, P. — *Artificial Intelligence: A Modern Approach* — Chapitres sur les jeux adversariaux, Min-Max, Alpha-Beta.
- Buro, M. — *An Evaluation Function for Othello Based on Statistics* — Techniques d'évaluation positionnelle.
- Breuker, D. — *Memory versus Search in Games* — Tables de transposition et Zobrist hashing.
- Cours d'algorithmique INSA — Algorithmes Min-Max, Alpha-Beta, NegaMax.