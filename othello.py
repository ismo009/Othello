"""
Othello (Reversi) - Logique du jeu
"""

# Constantes du plateau
TAILLE = 8
VIDE = 0
NOIR = 1
BLANC = 2

# Directions pour vérifier les retournements (8 directions)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]


def adversaire(joueur):
    """Retourne l'adversaire du joueur donné."""
    return BLANC if joueur == NOIR else NOIR


def creer_plateau():
    """Crée et retourne un plateau 8x8 avec la position initiale."""
    plateau = [[VIDE] * TAILLE for _ in range(TAILLE)]
    # Position initiale : les blancs commencent (selon le sujet)
    plateau[3][3] = BLANC
    plateau[3][4] = NOIR
    plateau[4][3] = NOIR
    plateau[4][4] = BLANC
    return plateau


def copier_plateau(plateau):
    """Retourne une copie du plateau."""
    return [ligne[:] for ligne in plateau]


def est_sur_plateau(ligne, colonne):
    """Vérifie si la position est dans les limites du plateau."""
    return 0 <= ligne < TAILLE and 0 <= colonne < TAILLE


def pions_a_retourner(plateau, ligne, colonne, joueur):
    """
    Retourne la liste des pions à retourner si le joueur pose à (ligne, colonne).
    Retourne une liste vide si le coup n'est pas valide.
    """
    if plateau[ligne][colonne] != VIDE:
        return []

    adv = adversaire(joueur)
    pions = []

    for dl, dc in DIRECTIONS:
        l, c = ligne + dl, colonne + dc
        pions_direction = []

        # Avancer dans la direction tant qu'on trouve des pions adverses
        while est_sur_plateau(l, c) and plateau[l][c] == adv:
            pions_direction.append((l, c))
            l += dl
            c += dc

        # Vérifier qu'on termine sur un pion du joueur
        if pions_direction and est_sur_plateau(l, c) and plateau[l][c] == joueur:
            pions.extend(pions_direction)

    return pions


def est_coup_valide(plateau, ligne, colonne, joueur):
    """Vérifie si le coup est valide pour le joueur."""
    if not est_sur_plateau(ligne, colonne):
        return False
    return len(pions_a_retourner(plateau, ligne, colonne, joueur)) > 0


def coups_valides(plateau, joueur):
    """Retourne la liste de tous les coups valides pour le joueur."""
    coups = []
    for l in range(TAILLE):
        for c in range(TAILLE):
            if est_coup_valide(plateau, l, c, joueur):
                coups.append((l, c))
    return coups


def jouer_coup(plateau, ligne, colonne, joueur):
    """
    Joue un coup sur le plateau. Retourne le nouveau plateau et les pions retournés.
    Retourne None si le coup est invalide.
    """
    pions = pions_a_retourner(plateau, ligne, colonne, joueur)
    if not pions:
        return None, []

    nouveau_plateau = copier_plateau(plateau)
    nouveau_plateau[ligne][colonne] = joueur
    for l, c in pions:
        nouveau_plateau[l][c] = joueur

    return nouveau_plateau, pions


def compter_pions(plateau):
    """Retourne le nombre de pions noirs et blancs."""
    noirs = sum(case == NOIR for ligne in plateau for case in ligne)
    blancs = sum(case == BLANC for ligne in plateau for case in ligne)
    return noirs, blancs


def est_partie_finie(plateau):
    """Vérifie si la partie est terminée (aucun joueur ne peut jouer)."""
    return not coups_valides(plateau, NOIR) and not coups_valides(plateau, BLANC)


def gagnant(plateau):
    """
    Retourne le gagnant de la partie.
    NOIR, BLANC ou VIDE (match nul).
    """
    noirs, blancs = compter_pions(plateau)
    if noirs > blancs:
        return NOIR
    elif blancs > noirs:
        return BLANC
    else:
        return VIDE


def afficher_plateau_console(plateau, joueur_actuel=None):
    """Affiche le plateau dans la console (debug)."""
    symboles = {VIDE: '.', NOIR: 'N', BLANC: 'B'}
    print("  ", " ".join(str(i) for i in range(TAILLE)))
    for l in range(TAILLE):
        ligne_str = f"{l}  "
        for c in range(TAILLE):
            ligne_str += symboles[plateau[l][c]] + " "
        print(ligne_str)
    noirs, blancs = compter_pions(plateau)
    print(f"Noirs: {noirs}  Blancs: {blancs}")
    if joueur_actuel:
        print(f"Tour: {'Noir' if joueur_actuel == NOIR else 'Blanc'}")
