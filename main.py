"""
Othello - Interface graphique Pygame
Modes : Humain vs Humain / Humain vs IA / IA vs IA
"""

import pygame
import sys
import math
import threading
from othello import (
    TAILLE, VIDE, NOIR, BLANC,
    creer_plateau, coups_valides, jouer_coup,
    compter_pions, est_partie_finie, gagnant, adversaire
)
from ia import IAOthello

# ─────────────────────────────────────────────────────────────
# Couleurs
# ─────────────────────────────────────────────────────────────
COULEUR_FOND        = (34, 139, 34)      # Vert plateau
COULEUR_GRILLE      = (0, 80, 0)         # Lignes du plateau
COULEUR_NOIR        = (15, 15, 15)       # Pions noirs
COULEUR_BLANC       = (240, 240, 240)    # Pions blancs
COULEUR_VALIDE      = (0, 200, 0, 120)   # Coups valides (semi-transparent)
COULEUR_SURVOL      = (255, 255, 100)    # Case survolée
COULEUR_PANNEAU     = (30, 30, 30)       # Panneau latéral
COULEUR_TEXTE       = (255, 255, 255)    # Texte
COULEUR_TEXTE_DIM   = (180, 180, 180)    # Texte secondaire
COULEUR_DERNIER     = (200, 200, 50)     # Marqueur du dernier coup
COULEUR_RETOURNE    = (255, 120, 50)     # Pions récemment retournés
COULEUR_BOUTON      = (60, 60, 60)       # Boutons
COULEUR_BOUTON_HOVER = (90, 90, 90)      # Boutons survolés

# ─────────────────────────────────────────────────────────────
# Dimensions
# ─────────────────────────────────────────────────────────────
TAILLE_CASE     = 70                     # Taille d'une case en pixels
MARGE_PLATEAU   = 30                     # Marge autour du plateau
LARGEUR_PANNEAU = 220                    # Largeur du panneau d'info

LARGEUR_PLATEAU = TAILLE * TAILLE_CASE
HAUTEUR_PLATEAU = TAILLE * TAILLE_CASE

LARGEUR_FENETRE = LARGEUR_PLATEAU + 2 * MARGE_PLATEAU + LARGEUR_PANNEAU
HAUTEUR_FENETRE = HAUTEUR_PLATEAU + 2 * MARGE_PLATEAU

FPS = 60


class AnimationPion:
    """Animation de retournement d'un pion."""
    def __init__(self, ligne, col, couleur_depart, couleur_fin, duree=300):
        self.ligne = ligne
        self.col = col
        self.couleur_depart = couleur_depart
        self.couleur_fin = couleur_fin
        self.duree = duree  # millisecondes
        self.debut = pygame.time.get_ticks()
        self.termine = False

    def progression(self):
        """Retourne la progression de l'animation entre 0 et 1."""
        elapsed = pygame.time.get_ticks() - self.debut
        p = min(elapsed / self.duree, 1.0)
        if p >= 1.0:
            self.termine = True
        return p

    def rayon_courant(self, rayon_max):
        """Simule un retournement : le rayon diminue puis augmente."""
        p = self.progression()
        if p < 0.5:
            # Phase de réduction
            return rayon_max * (1 - 2 * p)
        else:
            # Phase d'agrandissement
            return rayon_max * (2 * p - 1)

    def couleur_courante(self):
        """Retourne la couleur actuelle du pion."""
        p = self.progression()
        if p < 0.5:
            return self.couleur_depart
        else:
            return self.couleur_fin


class JeuOthelloGUI:
    """Classe principale de l'interface graphique du jeu d'Othello."""

    # Modes de jeu
    MODE_MENU = 0
    MODE_HVH = 1     # Humain vs Humain
    MODE_HVA = 2     # Humain vs IA
    MODE_AVA = 3     # IA vs IA

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Othello")

        self.ecran = pygame.display.set_mode((LARGEUR_FENETRE, HAUTEUR_FENETRE))
        self.horloge = pygame.time.Clock()

        # Polices
        self.police_titre = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.police_menu_titre = pygame.font.SysFont("Segoe UI", 56, bold=True)
        self.police_info = pygame.font.SysFont("Segoe UI", 20)
        self.police_score = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.police_petit = pygame.font.SysFont("Segoe UI", 16)
        self.police_bouton = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.police_fin = pygame.font.SysFont("Segoe UI", 40, bold=True)
        self.police_menu_btn = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.police_menu_desc = pygame.font.SysFont("Segoe UI", 14)

        # État
        self.mode = self.MODE_MENU
        self.ia = None
        self.ia2 = None        # Pour le mode IA vs IA
        self.ia_couleur = NOIR  # L'IA joue les noirs par défaut
        self.ia_reflechit = False
        self.ia_coup_pret = None
        self.ia_stats = None

        self.reinitialiser()

    def reinitialiser(self):
        """Remet le jeu à zéro."""
        self.plateau = creer_plateau()
        self.joueur_actuel = BLANC  # Les blancs commencent (sujet)
        self.partie_finie = False
        self.message = ""
        self.dernier_coup = None
        self.pions_retournes = []
        self.animations = []
        self.historique = []
        self.tour_passe = False
        self.case_survolee = None
        self.ia_reflechit = False
        self.ia_coup_pret = None
        self.ia_stats = None

        # Recréer les IA si besoin
        if self.mode == self.MODE_HVA:
            self.ia = IAOthello(self.ia_couleur, profondeur_max=10, temps_max=5.0)
        elif self.mode == self.MODE_AVA:
            self.ia = IAOthello(BLANC, profondeur_max=8, temps_max=3.0)
            self.ia2 = IAOthello(NOIR, profondeur_max=8, temps_max=3.0)

    def lancer_mode(self, mode):
        """Lance un mode de jeu."""
        self.mode = mode
        if mode == self.MODE_HVA:
            self.ia_couleur = NOIR  # IA joue les noirs
            self.ia = IAOthello(NOIR, profondeur_max=10, temps_max=5.0)
        elif mode == self.MODE_AVA:
            self.ia = IAOthello(BLANC, profondeur_max=8, temps_max=3.0)
            self.ia2 = IAOthello(NOIR, profondeur_max=8, temps_max=3.0)
        else:
            self.ia = None
            self.ia2 = None
        self.reinitialiser()

    def pixel_vers_case(self, x, y):
        """Convertit les coordonnées pixel en coordonnées de case."""
        col = (x - MARGE_PLATEAU) // TAILLE_CASE
        ligne = (y - MARGE_PLATEAU) // TAILLE_CASE
        if 0 <= ligne < TAILLE and 0 <= col < TAILLE:
            return ligne, col
        return None, None

    def case_vers_pixel(self, ligne, col):
        """Retourne le centre de la case en pixels."""
        x = MARGE_PLATEAU + col * TAILLE_CASE + TAILLE_CASE // 2
        y = MARGE_PLATEAU + ligne * TAILLE_CASE + TAILLE_CASE // 2
        return x, y

    # ─────────────────────────────────────────────────────────
    # Dessin
    # ─────────────────────────────────────────────────────────

    def dessiner_plateau(self):
        """Dessine le plateau de jeu."""
        # Fond du plateau
        rect_plateau = pygame.Rect(
            MARGE_PLATEAU, MARGE_PLATEAU,
            LARGEUR_PLATEAU, HAUTEUR_PLATEAU
        )
        pygame.draw.rect(self.ecran, COULEUR_FOND, rect_plateau)

        # Lignes de la grille
        for i in range(TAILLE + 1):
            # Lignes horizontales
            y = MARGE_PLATEAU + i * TAILLE_CASE
            pygame.draw.line(
                self.ecran, COULEUR_GRILLE,
                (MARGE_PLATEAU, y),
                (MARGE_PLATEAU + LARGEUR_PLATEAU, y), 2
            )
            # Lignes verticales
            x = MARGE_PLATEAU + i * TAILLE_CASE
            pygame.draw.line(
                self.ecran, COULEUR_GRILLE,
                (x, MARGE_PLATEAU),
                (x, MARGE_PLATEAU + HAUTEUR_PLATEAU), 2
            )

        # Petits points repères (comme un vrai plateau d'Othello)
        for pos in [(2, 2), (2, 6), (6, 2), (6, 6)]:
            x = MARGE_PLATEAU + pos[1] * TAILLE_CASE
            y = MARGE_PLATEAU + pos[0] * TAILLE_CASE
            pygame.draw.circle(self.ecran, COULEUR_GRILLE, (x, y), 5)

    def dessiner_coups_valides(self):
        """Dessine les coups possibles pour le joueur actuel."""
        if self.partie_finie or self.animations:
            return
        # En mode IA, ne pas afficher les coups valides pour l'IA
        if self.mode == self.MODE_HVA and self.joueur_actuel == self.ia_couleur:
            return
        if self.mode == self.MODE_AVA:
            return

        coups = coups_valides(self.plateau, self.joueur_actuel)
        surface = pygame.Surface((TAILLE_CASE, TAILLE_CASE), pygame.SRCALPHA)

        for l, c in coups:
            x = MARGE_PLATEAU + c * TAILLE_CASE
            y = MARGE_PLATEAU + l * TAILLE_CASE

            # Petit cercle semi-transparent pour indiquer le coup valide
            surface.fill((0, 0, 0, 0))
            pygame.draw.circle(
                surface, (0, 0, 0, 50),
                (TAILLE_CASE // 2, TAILLE_CASE // 2),
                TAILLE_CASE // 6
            )
            self.ecran.blit(surface, (x, y))

    def dessiner_survol(self):
        """Met en surbrillance la case survolée si c'est un coup valide."""
        if self.case_survolee is None or self.partie_finie or self.animations:
            return
        # Pas de survol quand c'est le tour de l'IA
        if self.mode == self.MODE_HVA and self.joueur_actuel == self.ia_couleur:
            return
        if self.mode == self.MODE_AVA:
            return

        l, c = self.case_survolee
        if (l, c) in coups_valides(self.plateau, self.joueur_actuel):
            x = MARGE_PLATEAU + c * TAILLE_CASE
            y = MARGE_PLATEAU + l * TAILLE_CASE
            surface = pygame.Surface((TAILLE_CASE, TAILLE_CASE), pygame.SRCALPHA)
            surface.fill((255, 255, 100, 40))
            self.ecran.blit(surface, (x, y))

            # Prévisualisation du pion
            cx, cy = self.case_vers_pixel(l, c)
            couleur = COULEUR_NOIR if self.joueur_actuel == NOIR else COULEUR_BLANC
            rayon = TAILLE_CASE // 2 - 8
            pion_surface = pygame.Surface((rayon * 2, rayon * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                pion_surface,
                (*couleur[:3], 100),
                (rayon, rayon), rayon
            )
            self.ecran.blit(pion_surface, (cx - rayon, cy - rayon))

    def dessiner_pions(self):
        """Dessine tous les pions sur le plateau."""
        rayon = TAILLE_CASE // 2 - 6

        # Ensemble des cases en animation
        cases_animees = {(a.ligne, a.col) for a in self.animations}

        for l in range(TAILLE):
            for c in range(TAILLE):
                if self.plateau[l][c] == VIDE:
                    continue
                if (l, c) in cases_animees:
                    continue  # Géré par l'animation

                cx, cy = self.case_vers_pixel(l, c)
                couleur = COULEUR_NOIR if self.plateau[l][c] == NOIR else COULEUR_BLANC

                # Ombre
                pygame.draw.circle(self.ecran, (0, 0, 0, 80), (cx + 2, cy + 2), rayon)
                # Pion
                pygame.draw.circle(self.ecran, couleur, (cx, cy), rayon)
                # Reflet
                reflet_couleur = (80, 80, 80) if self.plateau[l][c] == NOIR else (255, 255, 255)
                pygame.draw.circle(self.ecran, reflet_couleur, (cx - 8, cy - 8), rayon // 4)

                # Marqueur du dernier coup
                if self.dernier_coup == (l, c):
                    pygame.draw.circle(self.ecran, COULEUR_DERNIER, (cx, cy), 6)

                # Marqueur des pions retournés au dernier coup
                if (l, c) in self.pions_retournes and not self.animations:
                    pygame.draw.circle(self.ecran, COULEUR_RETOURNE, (cx, cy), 5)

    def dessiner_animations(self):
        """Dessine les animations de retournement."""
        rayon_max = TAILLE_CASE // 2 - 6

        for anim in self.animations:
            cx, cy = self.case_vers_pixel(anim.ligne, anim.col)
            rayon = max(2, int(anim.rayon_courant(rayon_max)))
            couleur = anim.couleur_courante()

            # Ombre
            pygame.draw.circle(self.ecran, (0, 0, 0), (cx + 2, cy + 2), rayon)
            # Pion (ellipse pour simuler la 3D)
            rect = pygame.Rect(cx - rayon, cy - rayon_max, rayon * 2, rayon_max * 2)
            pygame.draw.ellipse(self.ecran, couleur, rect)

        # Nettoyer les animations terminées
        self.animations = [a for a in self.animations if not a.termine]

    def dessiner_panneau_info(self):
        """Dessine le panneau d'informations à droite."""
        x_panneau = LARGEUR_PLATEAU + 2 * MARGE_PLATEAU
        rect = pygame.Rect(x_panneau, 0, LARGEUR_PANNEAU, HAUTEUR_FENETRE)
        pygame.draw.rect(self.ecran, COULEUR_PANNEAU, rect)

        x_centre = x_panneau + LARGEUR_PANNEAU // 2
        y = 30

        # Titre
        titre = self.police_titre.render("OTHELLO", True, COULEUR_TEXTE)
        self.ecran.blit(titre, (x_centre - titre.get_width() // 2, y))
        y += 60

        # Ligne séparatrice
        pygame.draw.line(
            self.ecran, (80, 80, 80),
            (x_panneau + 20, y), (x_panneau + LARGEUR_PANNEAU - 20, y), 1
        )
        y += 20

        # Scores
        noirs, blancs = compter_pions(self.plateau)

        # Score Blanc
        indicateur_b = "  ◄" if self.joueur_actuel == BLANC and not self.partie_finie else ""
        label_b = self.police_info.render(f"Blanc{indicateur_b}", True, COULEUR_BLANC)
        self.ecran.blit(label_b, (x_centre - label_b.get_width() // 2, y))
        y += 30

        # Pion blanc miniature + score
        pygame.draw.circle(self.ecran, COULEUR_BLANC, (x_centre - 35, y + 18), 15)
        score_b = self.police_score.render(str(blancs), True, COULEUR_BLANC)
        self.ecran.blit(score_b, (x_centre - 5, y))
        y += 65

        # Score Noir
        indicateur_n = "  ◄" if self.joueur_actuel == NOIR and not self.partie_finie else ""
        label_n = self.police_info.render(f"Noir{indicateur_n}", True, COULEUR_TEXTE_DIM)
        self.ecran.blit(label_n, (x_centre - label_n.get_width() // 2, y))
        y += 30

        pygame.draw.circle(self.ecran, COULEUR_NOIR, (x_centre - 35, y + 18), 15)
        pygame.draw.circle(self.ecran, (60, 60, 60), (x_centre - 35, y + 18), 15, 1)
        score_n = self.police_score.render(str(noirs), True, COULEUR_TEXTE)
        self.ecran.blit(score_n, (x_centre - 5, y))
        y += 80

        # Ligne séparatrice
        pygame.draw.line(
            self.ecran, (80, 80, 80),
            (x_panneau + 20, y), (x_panneau + LARGEUR_PANNEAU - 20, y), 1
        )
        y += 20

        # Tour actuel
        if not self.partie_finie:
            if self.mode == self.MODE_HVA:
                if self.joueur_actuel == self.ia_couleur:
                    tour_texte = "IA réfléchit..."
                else:
                    tour_texte = "A vous de jouer"
            elif self.mode == self.MODE_AVA:
                nom = "IA Blanc" if self.joueur_actuel == BLANC else "IA Noir"
                tour_texte = f"{nom} réfléchit..."
            else:
                tour_texte = "Tour des Blancs" if self.joueur_actuel == BLANC else "Tour des Noirs"
            tour = self.police_info.render(tour_texte, True, COULEUR_TEXTE)
            self.ecran.blit(tour, (x_centre - tour.get_width() // 2, y))
            y += 30

            # Indicateur IA qui réfléchit (animation)
            if self.ia_reflechit:
                dots = "." * (1 + (pygame.time.get_ticks() // 500) % 3)
                think = self.police_petit.render(
                    f"Analyse en cours{dots}", True, (255, 200, 100)
                )
                self.ecran.blit(think, (x_centre - think.get_width() // 2, y))
                y += 25
            else:
                nb_coups = len(coups_valides(self.plateau, self.joueur_actuel))
                coups_txt = self.police_petit.render(
                    f"{nb_coups} coup(s) possible(s)", True, COULEUR_TEXTE_DIM
                )
                self.ecran.blit(coups_txt, (x_centre - coups_txt.get_width() // 2, y))
                y += 25

            tour_num = self.police_petit.render(
                f"Tour n°{len(self.historique) + 1}", True, COULEUR_TEXTE_DIM
            )
            self.ecran.blit(tour_num, (x_centre - tour_num.get_width() // 2, y))

            # Statistiques IA du dernier coup
            if self.ia_stats and self.mode in (self.MODE_HVA, self.MODE_AVA):
                y += 30
                pygame.draw.line(
                    self.ecran, (80, 80, 80),
                    (x_panneau + 20, y), (x_panneau + LARGEUR_PANNEAU - 20, y), 1
                )
                y += 10
                ia_label = self.police_petit.render("Dernier coup IA :", True, (150, 200, 255))
                self.ecran.blit(ia_label, (x_centre - ia_label.get_width() // 2, y))
                y += 20
                for key, label in [('profondeur_atteinte', 'Profondeur'),
                                    ('noeuds', 'Noeuds'),
                                    ('coupes', 'Coupes α-β'),
                                    ('tt_hits', 'Cache TT'),
                                    ('temps', 'Temps')]:
                    val = self.ia_stats.get(key, 0)
                    if key == 'temps':
                        txt = f"{label}: {val:.2f}s"
                    elif key == 'noeuds':
                        txt = f"{label}: {val:,}"
                    else:
                        txt = f"{label}: {val}"
                    stat_render = self.police_petit.render(txt, True, COULEUR_TEXTE_DIM)
                    self.ecran.blit(stat_render, (x_panneau + 25, y))
                    y += 18
        else:
            self.dessiner_resultat(x_centre, y)

        y += 50

        # Message (tour passé, etc.)
        if self.message:
            msg = self.police_petit.render(self.message, True, (255, 200, 100))
            self.ecran.blit(msg, (x_centre - msg.get_width() // 2, y))

        # Bouton Nouvelle Partie (en bas)
        self.dessiner_bouton_nouvelle_partie(x_panneau)

    def dessiner_resultat(self, x_centre, y):
        """Affiche le résultat de la partie."""
        g = gagnant(self.plateau)
        noirs, blancs = compter_pions(self.plateau)

        if g == BLANC:
            texte = "Victoire Blanc !"
            couleur = (100, 200, 255)
        elif g == NOIR:
            texte = "Victoire Noir !"
            couleur = (255, 180, 100)
        else:
            texte = "Match Nul !"
            couleur = (200, 200, 200)

        resultat = self.police_info.render(texte, True, couleur)
        self.ecran.blit(resultat, (x_centre - resultat.get_width() // 2, y))
        y += 30

        detail = self.police_petit.render(
            f"{blancs} - {noirs}", True, COULEUR_TEXTE_DIM
        )
        self.ecran.blit(detail, (x_centre - detail.get_width() // 2, y))

    def dessiner_bouton_nouvelle_partie(self, x_panneau):
        """Dessine les boutons 'Nouvelle Partie' et 'Menu'."""
        largeur_btn = 180
        hauteur_btn = 36
        x_btn = x_panneau + (LARGEUR_PANNEAU - largeur_btn) // 2

        # Bouton Nouvelle Partie
        y_btn = HAUTEUR_FENETRE - 100
        self.rect_bouton = pygame.Rect(x_btn, y_btn, largeur_btn, hauteur_btn)
        mx, my = pygame.mouse.get_pos()
        survol = self.rect_bouton.collidepoint(mx, my)
        couleur = COULEUR_BOUTON_HOVER if survol else COULEUR_BOUTON
        pygame.draw.rect(self.ecran, couleur, self.rect_bouton, border_radius=8)
        pygame.draw.rect(self.ecran, (100, 100, 100), self.rect_bouton, 1, border_radius=8)
        texte = self.police_bouton.render("Nouvelle Partie", True, COULEUR_TEXTE)
        self.ecran.blit(texte, (
            x_btn + (largeur_btn - texte.get_width()) // 2,
            y_btn + (hauteur_btn - texte.get_height()) // 2
        ))

        # Bouton Menu
        y_btn2 = HAUTEUR_FENETRE - 55
        self.rect_bouton_menu = pygame.Rect(x_btn, y_btn2, largeur_btn, hauteur_btn)
        survol2 = self.rect_bouton_menu.collidepoint(mx, my)
        couleur2 = COULEUR_BOUTON_HOVER if survol2 else COULEUR_BOUTON
        pygame.draw.rect(self.ecran, couleur2, self.rect_bouton_menu, border_radius=8)
        pygame.draw.rect(self.ecran, (100, 100, 100), self.rect_bouton_menu, 1, border_radius=8)
        texte2 = self.police_bouton.render("Menu", True, COULEUR_TEXTE)
        self.ecran.blit(texte2, (
            x_btn + (largeur_btn - texte2.get_width()) // 2,
            y_btn2 + (hauteur_btn - texte2.get_height()) // 2
        ))

    def dessiner_coordonnees(self):
        """Dessine les coordonnées A-H et 1-8 autour du plateau."""
        lettres = "ABCDEFGH"
        for i in range(TAILLE):
            x = MARGE_PLATEAU + i * TAILLE_CASE + TAILLE_CASE // 2
            # Lettres en haut
            lettre = self.police_petit.render(lettres[i], True, COULEUR_TEXTE_DIM)
            self.ecran.blit(lettre, (x - lettre.get_width() // 2, 8))
            # Lettres en bas
            self.ecran.blit(lettre, (
                x - lettre.get_width() // 2,
                MARGE_PLATEAU + HAUTEUR_PLATEAU + 5
            ))

            y = MARGE_PLATEAU + i * TAILLE_CASE + TAILLE_CASE // 2
            # Chiffres à gauche
            chiffre = self.police_petit.render(str(i + 1), True, COULEUR_TEXTE_DIM)
            self.ecran.blit(chiffre, (8, y - chiffre.get_height() // 2))

    def dessiner_ecran_fin(self):
        """Overlay semi-transparent à la fin de la partie."""
        if not self.partie_finie:
            return

        overlay = pygame.Surface((LARGEUR_PLATEAU, HAUTEUR_PLATEAU), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.ecran.blit(overlay, (MARGE_PLATEAU, MARGE_PLATEAU))

        g = gagnant(self.plateau)
        if g == BLANC:
            texte = "VICTOIRE BLANC"
            couleur = (100, 200, 255)
        elif g == NOIR:
            texte = "VICTOIRE NOIR"
            couleur = (255, 180, 100)
        else:
            texte = "MATCH NUL"
            couleur = (200, 200, 200)

        rendu = self.police_fin.render(texte, True, couleur)
        cx = MARGE_PLATEAU + LARGEUR_PLATEAU // 2
        cy = MARGE_PLATEAU + HAUTEUR_PLATEAU // 2
        self.ecran.blit(rendu, (cx - rendu.get_width() // 2, cy - rendu.get_height() // 2))

    # ─────────────────────────────────────────────────────────
    # Menu
    # ─────────────────────────────────────────────────────────

    def dessiner_menu(self):
        """Dessine l'écran de menu principal."""
        self.ecran.fill((20, 25, 20))

        cx = LARGEUR_FENETRE // 2
        y = 60

        # Titre
        titre = self.police_menu_titre.render("OTHELLO", True, (100, 220, 100))
        self.ecran.blit(titre, (cx - titre.get_width() // 2, y))
        y += 80

        sous_titre = self.police_info.render("Choisissez un mode de jeu", True, COULEUR_TEXTE_DIM)
        self.ecran.blit(sous_titre, (cx - sous_titre.get_width() // 2, y))
        y += 60

        # Boutons de mode
        mx, my = pygame.mouse.get_pos()
        largeur_btn = 340
        hauteur_btn = 70

        boutons = [
            ("Humain vs Humain", "Deux joueurs sur le même écran", self.MODE_HVH),
            ("Humain vs IA", "Affrontez l'IA imbattable", self.MODE_HVA),
            ("IA vs IA", "Regardez deux IA s'affronter", self.MODE_AVA),
        ]

        self.rects_menu = []

        for label, desc, mode in boutons:
            x_btn = cx - largeur_btn // 2
            rect = pygame.Rect(x_btn, y, largeur_btn, hauteur_btn)
            self.rects_menu.append((rect, mode))

            survol = rect.collidepoint(mx, my)
            couleur_bg = (50, 80, 50) if survol else (40, 50, 40)
            couleur_bord = (100, 200, 100) if survol else (60, 80, 60)

            pygame.draw.rect(self.ecran, couleur_bg, rect, border_radius=12)
            pygame.draw.rect(self.ecran, couleur_bord, rect, 2, border_radius=12)

            # Label
            lbl = self.police_menu_btn.render(label, True, COULEUR_TEXTE)
            self.ecran.blit(lbl, (cx - lbl.get_width() // 2, y + 15))

            # Description
            d = self.police_menu_desc.render(desc, True, COULEUR_TEXTE_DIM)
            self.ecran.blit(d, (cx - d.get_width() // 2, y + 44))

            y += hauteur_btn + 20

        # Pied de page
        y += 20
        footer = self.police_petit.render("Appuyez sur Echap pour quitter", True, (80, 80, 80))
        self.ecran.blit(footer, (cx - footer.get_width() // 2, y))

    def gerer_clic_menu(self, x, y):
        """Gère un clic dans le menu."""
        if not hasattr(self, 'rects_menu'):
            return
        for rect, mode in self.rects_menu:
            if rect.collidepoint(x, y):
                self.lancer_mode(mode)
                return

    # ─────────────────────────────────────────────────────────
    # IA
    # ─────────────────────────────────────────────────────────

    def est_tour_ia(self):
        """Vérifie si c'est le tour de l'IA."""
        if self.partie_finie or self.animations:
            return False
        if self.mode == self.MODE_HVA and self.joueur_actuel == self.ia_couleur:
            return True
        if self.mode == self.MODE_AVA:
            return True
        return False

    def lancer_reflexion_ia(self):
        """Lance la réflexion de l'IA dans un thread séparé."""
        if self.ia_reflechit:
            return

        self.ia_reflechit = True
        self.ia_coup_pret = None

        def _penser():
            if self.mode == self.MODE_AVA:
                ia = self.ia if self.joueur_actuel == BLANC else self.ia2
            else:
                ia = self.ia

            # Copier le plateau pour le thread
            plateau_copie = [row[:] for row in self.plateau]
            ia.couleur = self.joueur_actuel
            coup = ia.choisir_coup(plateau_copie)
            self.ia_stats = ia.obtenir_stats()
            self.ia_coup_pret = coup

        thread = threading.Thread(target=_penser, daemon=True)
        thread.start()

    def appliquer_coup_ia(self):
        """Applique le coup choisi par l'IA."""
        if self.ia_coup_pret is None:
            return

        coup = self.ia_coup_pret
        self.ia_coup_pret = None
        self.ia_reflechit = False

        if coup is not None:
            self.effectuer_coup(coup[0], coup[1])

    # ─────────────────────────────────────────────────────────
    # Logique de jeu
    # ─────────────────────────────────────────────────────────

    def gerer_clic(self, x, y):
        """Gère un clic de souris."""
        # Clic sur le bouton nouvelle partie
        if hasattr(self, 'rect_bouton') and self.rect_bouton.collidepoint(x, y):
            self.reinitialiser()
            return

        # Clic sur le bouton menu
        if hasattr(self, 'rect_bouton_menu') and self.rect_bouton_menu.collidepoint(x, y):
            self.mode = self.MODE_MENU
            self.ia = None
            self.ia2 = None
            self.ia_reflechit = False
            return

        if self.partie_finie or self.animations:
            return

        # Ne pas permettre de cliquer pendant le tour de l'IA
        if self.est_tour_ia():
            return

        ligne, col = self.pixel_vers_case(x, y)
        if ligne is None:
            return

        if (ligne, col) not in coups_valides(self.plateau, self.joueur_actuel):
            return

        self.effectuer_coup(ligne, col)

    def effectuer_coup(self, ligne, col):
        """Effectue un coup et lance les animations."""
        ancien_plateau = self.plateau
        nouveau_plateau, pions = jouer_coup(self.plateau, ligne, col, self.joueur_actuel)

        if nouveau_plateau is None:
            return

        # Enregistrer dans l'historique
        self.historique.append({
            'joueur': self.joueur_actuel,
            'position': (ligne, col),
            'pions_retournes': pions[:],
            'plateau_avant': [r[:] for r in ancien_plateau]
        })

        # Lancer les animations de retournement
        self.animations = []
        couleur_depart = COULEUR_BLANC if self.joueur_actuel == NOIR else COULEUR_NOIR
        couleur_fin = COULEUR_NOIR if self.joueur_actuel == NOIR else COULEUR_BLANC

        for i, (l, c) in enumerate(pions):
            delai = i * 50  # Décalage entre chaque animation
            anim = AnimationPion(l, c, couleur_depart, couleur_fin, duree=300)
            anim.debut += delai
            self.animations.append(anim)

        self.plateau = nouveau_plateau
        self.dernier_coup = (ligne, col)
        self.pions_retournes = pions[:]
        self.message = ""

        # Changer de joueur
        self.joueur_actuel = adversaire(self.joueur_actuel)

        # Vérifier si le prochain joueur peut jouer
        if not coups_valides(self.plateau, self.joueur_actuel):
            if est_partie_finie(self.plateau):
                self.partie_finie = True
                self.message = "Partie terminée !"
            else:
                # Le joueur doit passer son tour
                nom = "Blancs" if self.joueur_actuel == BLANC else "Noirs"
                self.message = f"{nom} passent leur tour"
                self.joueur_actuel = adversaire(self.joueur_actuel)

    # ─────────────────────────────────────────────────────────
    # Boucle principale
    # ─────────────────────────────────────────────────────────

    def executer(self):
        """Boucle principale du jeu."""
        en_cours = True

        while en_cours:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    en_cours = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.mode == self.MODE_MENU:
                        self.gerer_clic_menu(*event.pos)
                    else:
                        self.gerer_clic(*event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    if self.mode != self.MODE_MENU:
                        l, c = self.pixel_vers_case(*event.pos)
                        self.case_survolee = (l, c) if l is not None else None

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n and self.mode != self.MODE_MENU:
                        self.reinitialiser()
                    elif event.key == pygame.K_m or (event.key == pygame.K_ESCAPE
                                                      and self.mode != self.MODE_MENU):
                        self.mode = self.MODE_MENU
                        self.ia_reflechit = False
                    elif event.key == pygame.K_ESCAPE:
                        en_cours = False

            # ─── IA ───
            if self.mode != self.MODE_MENU:
                # Appliquer le coup de l'IA s'il est prêt
                if self.ia_coup_pret is not None:
                    self.appliquer_coup_ia()

                # Lancer la réflexion de l'IA si c'est son tour
                if (self.est_tour_ia() and not self.ia_reflechit
                        and not self.animations and not self.partie_finie):
                    # Petit délai pour que l'animation se termine visuellement
                    pygame.time.wait(200)
                    self.lancer_reflexion_ia()

            # ─── Dessin ───
            if self.mode == self.MODE_MENU:
                self.dessiner_menu()
            else:
                self.ecran.fill((20, 20, 20))
                self.dessiner_coordonnees()
                self.dessiner_plateau()
                self.dessiner_coups_valides()
                self.dessiner_survol()
                self.dessiner_pions()
                self.dessiner_animations()
                self.dessiner_ecran_fin()
                self.dessiner_panneau_info()

            pygame.display.flip()
            self.horloge.tick(FPS)

        pygame.quit()
        sys.exit()


# ─────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    jeu = JeuOthelloGUI()
    jeu.executer()
