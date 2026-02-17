"""
Othello IA — Moteur d'intelligence artificielle imbattable
==========================================================
Techniques utilisées :
  - NegaMax avec élagage Alpha-Beta
  - Approfondissement itératif (Iterative Deepening)
  - Table de transposition (Zobrist hashing)
  - Tri des coups (Move Ordering)
  - Résolution exacte en fin de partie (Endgame Solver)
  - Fonction d'évaluation multi-composantes :
      * Poids positionnels
      * Mobilité (coups du joueur vs adversaire)
      * Stabilité des pions (pions impossibles à retourner)
      * Occupation des coins
      * Pions frontières
      * Parité (qui joue en dernier)
  - Stratégies par phase (ouverture / milieu / fin de partie)
"""

import random
import time
from othello import (
    TAILLE, VIDE, NOIR, BLANC, DIRECTIONS,
    adversaire, copier_plateau, est_sur_plateau,
    pions_a_retourner, coups_valides, jouer_coup,
    compter_pions, est_partie_finie
)

# ═══════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════

INF = 1_000_000

# Table de poids positionnels classique pour Othello 8x8
# Les coins valent beaucoup, les cases adjacentes aux coins (X/C) sont dangereuses
POIDS_POSITION = [
    [ 500, -150, 30, 10, 10, 30, -150,  500],
    [-150, -250,  0,  0,  0,  0, -250, -150],
    [  30,    0,  1,  2,  2,  1,    0,   30],
    [  10,    0,  2, 16, 16,  2,    0,   10],
    [  10,    0,  2, 16, 16,  2,    0,   10],
    [  30,    0,  1,  2,  2,  1,    0,   30],
    [-150, -250,  0,  0,  0,  0, -250, -150],
    [ 500, -150, 30, 10, 10, 30, -150,  500],
]

# Cases de coins
COINS = [(0, 0), (0, 7), (7, 0), (7, 7)]

# Cases X (diagonalement adjacentes au coin) — très dangereuses
CASES_X = [(1, 1), (1, 6), (6, 1), (6, 6)]

# Cases C (adjacentes au coin sur le bord)
CASES_C = [
    (0, 1), (1, 0),  # coin (0,0)
    (0, 6), (1, 7),  # coin (0,7)
    (6, 0), (7, 1),  # coin (7,0)
    (6, 7), (7, 6),  # coin (7,7)
]

# Association coin → cases X et C dangereuses
COIN_ADJACENTES = {
    (0, 0): [(1, 1), (0, 1), (1, 0)],
    (0, 7): [(1, 6), (0, 6), (1, 7)],
    (7, 0): [(6, 1), (6, 0), (7, 1)],
    (7, 7): [(6, 6), (6, 7), (7, 6)],
}

# Bords du plateau
BORDS = []
for i in range(TAILLE):
    BORDS.extend([(0, i), (7, i), (i, 0), (i, 7)])
BORDS = list(set(BORDS))


# ═══════════════════════════════════════════════════════════════
# Table de transposition (Zobrist Hashing)
# ═══════════════════════════════════════════════════════════════

random.seed(42)  # Reproductibilité
_zobrist_table = [[[random.getrandbits(64) for _ in range(3)]
                   for _ in range(TAILLE)] for _ in range(TAILLE)]
_zobrist_joueur = random.getrandbits(64)


def zobrist_hash(plateau, joueur):
    """Calcule le hash Zobrist du plateau."""
    h = 0
    for l in range(TAILLE):
        for c in range(TAILLE):
            if plateau[l][c] != VIDE:
                h ^= _zobrist_table[l][c][plateau[l][c]]
    if joueur == BLANC:
        h ^= _zobrist_joueur
    return h


# ═══════════════════════════════════════════════════════════════
# Fonctions utilitaires rapides
# ═══════════════════════════════════════════════════════════════

def jouer_coup_rapide(plateau, ligne, col, joueur):
    """Version optimisée de jouer_coup qui modifie le plateau en place.
    Retourne la liste des pions retournés (pour annuler le coup)."""
    adv = adversaire(joueur)
    pions = []

    for dl, dc in DIRECTIONS:
        l, c = ligne + dl, col + dc
        pions_dir = []
        while 0 <= l < TAILLE and 0 <= c < TAILLE and plateau[l][c] == adv:
            pions_dir.append((l, c))
            l += dl
            c += dc
        if pions_dir and 0 <= l < TAILLE and 0 <= c < TAILLE and plateau[l][c] == joueur:
            pions.extend(pions_dir)

    if not pions:
        return None

    plateau[ligne][col] = joueur
    for l, c in pions:
        plateau[l][c] = joueur
    return pions


def annuler_coup(plateau, ligne, col, joueur, pions_retournes):
    """Annule un coup joué avec jouer_coup_rapide."""
    plateau[ligne][col] = VIDE
    adv = adversaire(joueur)
    for l, c in pions_retournes:
        plateau[l][c] = adv


def coups_valides_rapide(plateau, joueur):
    """Version optimisée de coups_valides."""
    adv = adversaire(joueur)
    coups = []
    for l in range(TAILLE):
        for c in range(TAILLE):
            if plateau[l][c] != VIDE:
                continue
            valide = False
            for dl, dc in DIRECTIONS:
                ll, cc = l + dl, c + dc
                found = False
                while 0 <= ll < TAILLE and 0 <= cc < TAILLE and plateau[ll][cc] == adv:
                    ll += dl
                    cc += dc
                    found = True
                if found and 0 <= ll < TAILLE and 0 <= cc < TAILLE and plateau[ll][cc] == joueur:
                    valide = True
                    break
            if valide:
                coups.append((l, c))
    return coups


def compter_cases_vides(plateau):
    """Compte le nombre de cases vides."""
    return sum(1 for l in range(TAILLE) for c in range(TAILLE) if plateau[l][c] == VIDE)


# ═══════════════════════════════════════════════════════════════
# Fonction d'évaluation multi-composantes
# ═══════════════════════════════════════════════════════════════

def eval_positionnelle(plateau, joueur):
    """Évalue la position en utilisant les poids statiques.
    Ajuste dynamiquement les poids X/C quand le coin adjacent est pris."""
    adv = adversaire(joueur)
    score = 0

    # Copier les poids et ajuster dynamiquement
    for l in range(TAILLE):
        for c in range(TAILLE):
            if plateau[l][c] == VIDE:
                continue
            poids = POIDS_POSITION[l][c]

            # Ajustement dynamique : si le coin est pris par le joueur,
            # les cases X et C adjacentes deviennent neutres/positives
            for coin in COINS:
                if (l, c) in COIN_ADJACENTES.get(coin, []):
                    if plateau[coin[0]][coin[1]] == plateau[l][c]:
                        # Le coin est pris par le même joueur → pas de pénalité
                        poids = abs(poids)

            if plateau[l][c] == joueur:
                score += poids
            else:
                score -= poids

    return score


def eval_mobilite(plateau, joueur):
    """Évalue la mobilité : nombre de coups du joueur vs adversaire."""
    adv = adversaire(joueur)
    coups_j = len(coups_valides_rapide(plateau, joueur))
    coups_a = len(coups_valides_rapide(plateau, adv))

    if coups_j + coups_a == 0:
        return 0
    return 100 * (coups_j - coups_a) / (coups_j + coups_a)


def eval_coins(plateau, joueur):
    """Évalue l'occupation des coins."""
    adv = adversaire(joueur)
    score = 0
    for l, c in COINS:
        if plateau[l][c] == joueur:
            score += 1
        elif plateau[l][c] == adv:
            score -= 1
    return score * 250


def eval_stabilite(plateau, joueur):
    """Évalue la stabilité des pions (pions qui ne peuvent plus être retournés).
    Un pion est stable s'il est dans un coin, ou appuyé contre un bord/coin stable."""
    adv = adversaire(joueur)
    stable_j = _compter_pions_stables(plateau, joueur)
    stable_a = _compter_pions_stables(plateau, adv)

    if stable_j + stable_a == 0:
        return 0
    return 100 * (stable_j - stable_a) / (stable_j + stable_a)


def _compter_pions_stables(plateau, joueur):
    """Compte les pions stables pour un joueur en utilisant une propagation depuis les coins."""
    stable = [[False] * TAILLE for _ in range(TAILLE)]
    count = 0

    for cl, cc in COINS:
        if plateau[cl][cc] != joueur:
            continue

        # Propagation depuis ce coin
        # Direction de propagation depuis chaque coin
        dl = 1 if cl == 0 else -1
        dc = 1 if cc == 0 else -1

        # Marquer les pions stables le long des bords et diagonales depuis le coin
        # Ligne horizontale depuis le coin
        c = cc
        while 0 <= c < TAILLE and plateau[cl][c] == joueur:
            stable[cl][c] = True
            c += dc

        # Colonne verticale depuis le coin
        l = cl
        while 0 <= l < TAILLE and plateau[l][cc] == joueur:
            stable[l][cc] = True
            l += dl

        # Triangle stable : si une ligne complète est stable,
        # la ligne suivante est aussi stable jusqu'au premier non-joueur
        l = cl
        while 0 <= l < TAILLE:
            c = cc
            row_stable = True
            while 0 <= c < TAILLE:
                if plateau[l][c] == joueur and (stable[l - dl][c] if 0 <= l - dl < TAILLE else l == cl):
                    stable[l][c] = True
                else:
                    row_stable = False
                    break
                c += dc
            if not row_stable and l != cl:
                break
            l += dl

    for l in range(TAILLE):
        for c in range(TAILLE):
            if stable[l][c]:
                count += 1

    return count


def eval_frontieres(plateau, joueur):
    """Évalue les pions frontières (adjacents à une case vide).
    Moins de pions frontières est mieux (moins exposé aux retournements)."""
    adv = adversaire(joueur)
    front_j = 0
    front_a = 0

    for l in range(TAILLE):
        for c in range(TAILLE):
            if plateau[l][c] == VIDE:
                continue
            # Vérifier si au moins une case adjacente est vide
            est_frontiere = False
            for dl, dc in DIRECTIONS:
                nl, nc = l + dl, c + dc
                if 0 <= nl < TAILLE and 0 <= nc < TAILLE and plateau[nl][nc] == VIDE:
                    est_frontiere = True
                    break
            if est_frontiere:
                if plateau[l][c] == joueur:
                    front_j += 1
                else:
                    front_a += 1

    if front_j + front_a == 0:
        return 0
    return -100 * (front_j - front_a) / (front_j + front_a)


def eval_parite(plateau, joueur):
    """Évalue la parité : avantage à celui qui joue le dernier coup."""
    vides = compter_cases_vides(plateau)
    # Si nombre pair de cases vides et c'est notre tour → on joue en dernier
    if vides % 2 == 0:
        return 10
    else:
        return -10


def evaluation(plateau, joueur):
    """
    Fonction d'évaluation principale — stratégie mixte par phase.

    Phase 1 (ouverture, ≤ 20 pions joués) : positionnel + mobilité
    Phase 2 (milieu, 20-50 pions joués) : mobilité + stabilité + coins
    Phase 3 (fin, > 50 pions joués) : différence de pions + résolution
    """
    noirs, blancs = compter_pions(plateau)
    total_pions = noirs + blancs
    vides = 64 - total_pions

    # ── Fin de partie : score absolu ──
    if vides == 0 or (not coups_valides_rapide(plateau, NOIR) and
                       not coups_valides_rapide(plateau, BLANC)):
        diff = (noirs - blancs) if joueur == NOIR else (blancs - noirs)
        if diff > 0:
            return INF - 100 + diff  # Victoire
        elif diff < 0:
            return -INF + 100 - diff  # Défaite
        else:
            return 0  # Nul

    # ── Phase d'ouverture (≤ 20 pions sur le plateau) ──
    if total_pions <= 20:
        score = (
            eval_positionnelle(plateau, joueur) * 1.0 +
            eval_mobilite(plateau, joueur) * 5.0 +
            eval_coins(plateau, joueur) * 10.0 +
            eval_frontieres(plateau, joueur) * 2.0
        )

    # ── Phase de milieu (20-50 pions) ──
    elif total_pions <= 50:
        score = (
            eval_positionnelle(plateau, joueur) * 0.5 +
            eval_mobilite(plateau, joueur) * 4.0 +
            eval_coins(plateau, joueur) * 15.0 +
            eval_stabilite(plateau, joueur) * 3.0 +
            eval_frontieres(plateau, joueur) * 1.5 +
            eval_parite(plateau, joueur) * 1.0
        )

    # ── Phase de fin de partie (> 50 pions) ──
    else:
        diff = (noirs - blancs) if joueur == NOIR else (blancs - noirs)
        score = (
            diff * 10.0 +
            eval_coins(plateau, joueur) * 20.0 +
            eval_stabilite(plateau, joueur) * 5.0 +
            eval_parite(plateau, joueur) * 3.0
        )

    return score


# ═══════════════════════════════════════════════════════════════
# Tri des coups (Move Ordering)
# ═══════════════════════════════════════════════════════════════

# Priorité de chaque case pour le tri des coups
_PRIORITE_COUP = [
    [0, 5, 3, 3, 3, 3, 5, 0],  # coins = 0 (meilleur), X = 5 (pire)
    [5, 6, 4, 4, 4, 4, 6, 5],
    [3, 4, 2, 2, 2, 2, 4, 3],
    [3, 4, 2, 1, 1, 2, 4, 3],
    [3, 4, 2, 1, 1, 2, 4, 3],
    [3, 4, 2, 2, 2, 2, 4, 3],
    [5, 6, 4, 4, 4, 4, 6, 5],
    [0, 5, 3, 3, 3, 3, 5, 0],
]


def trier_coups(coups, plateau, joueur, tt_best_move=None):
    """Trie les coups par ordre de qualité décroissante.
    Le meilleur coup de la table de transposition est mis en premier."""

    def cle_tri(coup):
        l, c = coup
        if tt_best_move and coup == tt_best_move:
            return -1  # Toujours en premier
        return _PRIORITE_COUP[l][c]

    return sorted(coups, key=cle_tri)


# ═══════════════════════════════════════════════════════════════
# NegaMax avec Alpha-Beta + Table de Transposition
# ═══════════════════════════════════════════════════════════════

# Types d'entrées dans la table de transposition
TT_EXACT = 0
TT_ALPHA = 1  # Borne supérieure
TT_BETA = 2   # Borne inférieure


class IAOthello:
    """Moteur d'IA pour Othello."""

    def __init__(self, couleur, profondeur_max=8, temps_max=5.0):
        """
        Args:
            couleur: NOIR ou BLANC
            profondeur_max: profondeur maximale de recherche
            temps_max: temps maximum par coup en secondes
        """
        self.couleur = couleur
        self.profondeur_max = profondeur_max
        self.temps_max = temps_max

        # Table de transposition : hash → (profondeur, score, type, meilleur_coup)
        self.table_transposition = {}
        self.noeuds_explores = 0
        self.temps_debut = 0
        self.timeout = False

        # Statistiques
        self.stats = {
            'noeuds': 0,
            'coupes': 0,
            'tt_hits': 0,
            'profondeur_atteinte': 0,
            'temps': 0,
        }

    def reinitialiser_stats(self):
        """Remet les statistiques à zéro."""
        self.noeuds_explores = 0
        self.timeout = False
        self.stats = {
            'noeuds': 0,
            'coupes': 0,
            'tt_hits': 0,
            'profondeur_atteinte': 0,
            'temps': 0,
        }

    def choisir_coup(self, plateau):
        """
        Choisit le meilleur coup pour l'IA en utilisant l'approfondissement itératif.
        Retourne (ligne, col) ou None si aucun coup possible.
        """
        coups = coups_valides_rapide(plateau, self.couleur)
        if not coups:
            return None
        if len(coups) == 1:
            return coups[0]

        self.reinitialiser_stats()
        self.temps_debut = time.time()
        self.timeout = False

        vides = compter_cases_vides(plateau)

        # En fin de partie, résolution exacte si assez peu de cases
        if vides <= 14:
            profondeur_limite = vides  # Résoudre exactement
        else:
            profondeur_limite = self.profondeur_max

        meilleur_coup = coups[0]
        meilleur_score = -INF

        # Approfondissement itératif
        for profondeur in range(1, profondeur_limite + 1):
            if self.timeout:
                break

            score_courant = -INF
            coup_courant = None

            # Trier avec le meilleur coup de l'itération précédente en premier
            coups_tries = trier_coups(coups, plateau, self.couleur, meilleur_coup)

            alpha = -INF
            beta = INF

            for coup in coups_tries:
                if self.timeout:
                    break

                l, c = coup
                pions = jouer_coup_rapide(plateau, l, c, self.couleur)
                if pions is None:
                    continue

                score = -self._negamax(plateau, adversaire(self.couleur),
                                       profondeur - 1, -beta, -alpha)

                annuler_coup(plateau, l, c, self.couleur, pions)

                if score > score_courant:
                    score_courant = score
                    coup_courant = coup

                if score > alpha:
                    alpha = score

            if not self.timeout and coup_courant is not None:
                meilleur_coup = coup_courant
                meilleur_score = score_courant
                self.stats['profondeur_atteinte'] = profondeur

            # Si on a trouvé un coup gagnant certain, pas besoin de chercher plus
            if meilleur_score >= INF - 200:
                break

        self.stats['temps'] = time.time() - self.temps_debut
        self.stats['noeuds'] = self.noeuds_explores

        return meilleur_coup

    def _negamax(self, plateau, joueur, profondeur, alpha, beta):
        """
        NegaMax avec élagage Alpha-Beta et table de transposition.
        """
        # Vérifier le timeout
        if time.time() - self.temps_debut > self.temps_max:
            self.timeout = True
            return 0

        self.noeuds_explores += 1

        # Lookup dans la table de transposition
        h = zobrist_hash(plateau, joueur)
        tt_entry = self.table_transposition.get(h)
        tt_best_move = None

        if tt_entry is not None:
            tt_depth, tt_score, tt_type, tt_move = tt_entry
            if tt_depth >= profondeur:
                self.stats['tt_hits'] += 1
                if tt_type == TT_EXACT:
                    return tt_score
                elif tt_type == TT_BETA and tt_score >= beta:
                    return tt_score
                elif tt_type == TT_ALPHA and tt_score <= alpha:
                    return tt_score
            tt_best_move = tt_move

        # Feuille : évaluation
        if profondeur == 0:
            score = evaluation(plateau, joueur)
            self.table_transposition[h] = (0, score, TT_EXACT, None)
            return score

        coups = coups_valides_rapide(plateau, joueur)

        # Aucun coup : passer le tour ou fin de partie
        if not coups:
            coups_adv = coups_valides_rapide(plateau, adversaire(joueur))
            if not coups_adv:
                # Fin de partie
                return evaluation(plateau, joueur)
            else:
                # Passer le tour
                return -self._negamax(plateau, adversaire(joueur),
                                      profondeur, -beta, -alpha)

        # Tri des coups pour améliorer les coupes alpha-beta
        coups = trier_coups(coups, plateau, joueur, tt_best_move)

        meilleur_score = -INF
        meilleur_coup = coups[0]
        tt_type = TT_ALPHA  # Par défaut, borne supérieure

        for coup in coups:
            if self.timeout:
                return 0

            l, c = coup
            pions = jouer_coup_rapide(plateau, l, c, joueur)
            if pions is None:
                continue

            score = -self._negamax(plateau, adversaire(joueur),
                                   profondeur - 1, -beta, -alpha)

            annuler_coup(plateau, l, c, joueur, pions)

            if score > meilleur_score:
                meilleur_score = score
                meilleur_coup = coup

            if score > alpha:
                alpha = score
                tt_type = TT_EXACT

            if alpha >= beta:
                self.stats['coupes'] += 1
                tt_type = TT_BETA
                break

        # Stocker dans la table de transposition
        if not self.timeout:
            self.table_transposition[h] = (profondeur, meilleur_score,
                                            tt_type, meilleur_coup)

        return meilleur_score

    def obtenir_stats(self):
        """Retourne les statistiques de la dernière recherche."""
        return self.stats.copy()
