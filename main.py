"""
Othello - Interface graphique Pygame
Jeu complet : Humain vs Humain (l'IA sera ajoutée plus tard)
"""

import pygame
import sys
import math
from othello import (
    TAILLE, VIDE, NOIR, BLANC,
    creer_plateau, coups_valides, jouer_coup,
    compter_pions, est_partie_finie, gagnant, adversaire
)

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

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Othello")

        self.ecran = pygame.display.set_mode((LARGEUR_FENETRE, HAUTEUR_FENETRE))
        self.horloge = pygame.time.Clock()

        # Polices
        self.police_titre = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.police_info = pygame.font.SysFont("Segoe UI", 20)
        self.police_score = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.police_petit = pygame.font.SysFont("Segoe UI", 16)
        self.police_bouton = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.police_fin = pygame.font.SysFont("Segoe UI", 40, bold=True)

        # État du jeu
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
        self.historique = []        # Pour rejouer la partie
        self.tour_passe = False
        self.case_survolee = None

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
            tour_texte = "Tour des Blancs" if self.joueur_actuel == BLANC else "Tour des Noirs"
            tour = self.police_info.render(tour_texte, True, COULEUR_TEXTE)
            self.ecran.blit(tour, (x_centre - tour.get_width() // 2, y))
            y += 30

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
        """Dessine le bouton 'Nouvelle Partie'."""
        largeur_btn = 180
        hauteur_btn = 40
        x_btn = x_panneau + (LARGEUR_PANNEAU - largeur_btn) // 2
        y_btn = HAUTEUR_FENETRE - 60

        self.rect_bouton = pygame.Rect(x_btn, y_btn, largeur_btn, hauteur_btn)

        # Vérifier si survolé
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
    # Logique de jeu
    # ─────────────────────────────────────────────────────────

    def gerer_clic(self, x, y):
        """Gère un clic de souris."""
        # Clic sur le bouton nouvelle partie
        if hasattr(self, 'rect_bouton') and self.rect_bouton.collidepoint(x, y):
            self.reinitialiser()
            return

        if self.partie_finie or self.animations:
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
                    self.gerer_clic(*event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    l, c = self.pixel_vers_case(*event.pos)
                    self.case_survolee = (l, c) if l is not None else None

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        self.reinitialiser()
                    elif event.key == pygame.K_ESCAPE:
                        en_cours = False

            # ─── Dessin ───
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
