"""
Benchmark : fait jouer les 4 stratégies IA entre elles.
Collecte les résultats pour le tableau du rapport.
"""
import time
import sys
from othello import (
    TAILLE, VIDE, NOIR, BLANC,
    creer_plateau, coups_valides, est_partie_finie,
    compter_pions, gagnant, adversaire
)
from ia import (
    IAOthello, jouer_coup_rapide, coups_valides_rapide,
    STRAT_POSITIONNEL, STRAT_ABSOLU, STRAT_MOBILITE, STRAT_MIXTE, STRATEGIES
)


def jouer_partie(strat_blanc, strat_noir, profondeur=6, temps_max=2.0, verbose=False):
    """Joue une partie complète entre deux IA. Retourne (gagnant_couleur, score_blanc, score_noir, stats)."""
    plateau = creer_plateau()
    ia_blanc = IAOthello(BLANC, profondeur_max=profondeur, temps_max=temps_max, strategie=strat_blanc)
    ia_noir = IAOthello(NOIR, profondeur_max=profondeur, temps_max=temps_max, strategie=strat_noir)

    joueur = BLANC
    total_noeuds_b, total_noeuds_n = 0, 0
    total_temps_b, total_temps_n = 0.0, 0.0
    total_coupes_b, total_coupes_n = 0, 0
    coups_b, coups_n = 0, 0
    passes = 0

    while not est_partie_finie(plateau):
        cv = coups_valides(plateau, joueur)
        if not cv:
            passes += 1
            if passes >= 2:
                break
            joueur = adversaire(joueur)
            continue
        passes = 0

        ia = ia_blanc if joueur == BLANC else ia_noir
        ia.couleur = joueur
        coup = ia.choisir_coup(plateau)
        stats = ia.obtenir_stats()

        if coup is None:
            joueur = adversaire(joueur)
            continue

        # Jouer le coup
        from othello import jouer_coup
        nouveau, _ = jouer_coup(plateau, coup[0], coup[1], joueur)
        if nouveau is None:
            break
        plateau = nouveau

        if joueur == BLANC:
            total_noeuds_b += stats['noeuds']
            total_temps_b += stats['temps']
            total_coupes_b += stats['coupes']
            coups_b += 1
        else:
            total_noeuds_n += stats['noeuds']
            total_temps_n += stats['temps']
            total_coupes_n += stats['coupes']
            coups_n += 1

        joueur = adversaire(joueur)

    noirs, blancs = compter_pions(plateau)
    g = gagnant(plateau)

    result_stats = {
        'blanc': {
            'noeuds_moy': total_noeuds_b / max(coups_b, 1),
            'temps_moy': total_temps_b / max(coups_b, 1),
            'coupes_moy': total_coupes_b / max(coups_b, 1),
            'nb_coups': coups_b,
        },
        'noir': {
            'noeuds_moy': total_noeuds_n / max(coups_n, 1),
            'temps_moy': total_temps_n / max(coups_n, 1),
            'coupes_moy': total_coupes_n / max(coups_n, 1),
            'nb_coups': coups_n,
        },
    }

    return g, blancs, noirs, result_stats


def main():
    strats = [STRAT_POSITIONNEL, STRAT_ABSOLU, STRAT_MOBILITE, STRAT_MIXTE]
    NB_PARTIES = 10  # 1 partie par paire
    PROFONDEUR = 6
    TEMPS = 3.0

    # Matrice de victoires
    victoires = {s: {s2: 0 for s2 in strats} for s in strats}
    scores = {s: {s2: [] for s2 in strats} for s in strats}

    print("=" * 60)
    print("BENCHMARK IA OTHELLO — Confrontation des stratégies")
    print(f"Profondeur: {PROFONDEUR}, Temps max: {TEMPS}s, Parties par paire: {NB_PARTIES}")
    print("=" * 60)

    all_stats = {}

    for i, s1 in enumerate(strats):
        for j, s2 in enumerate(strats):
            if i == j:
                continue

            nom1 = STRATEGIES[s1]
            nom2 = STRATEGIES[s2]
            print(f"\n--- {nom1} (Blanc) vs {nom2} (Noir) ---")

            for p in range(NB_PARTIES):
                t0 = time.time()
                g, blancs, noirs, st = jouer_partie(s1, s2, PROFONDEUR, TEMPS)
                dt = time.time() - t0

                if g == BLANC:
                    victoires[s1][s2] += 1
                    res = f"{nom1} gagne"
                elif g == NOIR:
                    victoires[s2][s1] += 1
                    res = f"{nom2} gagne"
                else:
                    res = "Nul"

                scores[s1][s2].append((blancs, noirs))
                print(f"  Partie {p+1}: {blancs}-{noirs} ({res}) [{dt:.1f}s]")

                key = (s1, s2, p)
                all_stats[key] = st

    # Résumé
    print("\n" + "=" * 60)
    print("TABLEAU DES VICTOIRES (lignes = Blanc, colonnes = Noir)")
    print("=" * 60)

    header = f"{'':>14s}"
    for s in strats:
        header += f" {STRATEGIES[s]:>12s}"
    print(header)

    for s1 in strats:
        row = f"{STRATEGIES[s1]:>14s}"
        for s2 in strats:
            if s1 == s2:
                row += f" {'--':>12s}"
            else:
                row += f" {victoires[s1][s2]:>12d}"
        print(row)

    # Statistiques moyennes globales par stratégie
    print("\n" + "=" * 60)
    print("STATISTIQUES MOYENNES PAR STRATEGIE")
    print("=" * 60)

    for s in strats:
        noeuds_total, temps_total, coupes_total, nb = 0, 0.0, 0, 0
        for key, st in all_stats.items():
            s_blanc, s_noir, _ = key
            if s_blanc == s:
                noeuds_total += st['blanc']['noeuds_moy']
                temps_total += st['blanc']['temps_moy']
                coupes_total += st['blanc']['coupes_moy']
                nb += 1
            if s_noir == s:
                noeuds_total += st['noir']['noeuds_moy']
                temps_total += st['noir']['temps_moy']
                coupes_total += st['noir']['coupes_moy']
                nb += 1
        if nb > 0:
            print(f"{STRATEGIES[s]:>14s}: nœuds/coup={noeuds_total/nb:,.0f}, "
                  f"temps/coup={temps_total/nb:.2f}s, coupes/coup={coupes_total/nb:,.0f}")

    # Total victories
    print("\n" + "=" * 60)
    print("CLASSEMENT (total victoires)")
    print("=" * 60)
    totaux = {s: sum(victoires[s][s2] for s2 in strats if s != s2) for s in strats}
    for s, v in sorted(totaux.items(), key=lambda x: -x[1]):
        print(f"  {STRATEGIES[s]:>14s}: {v} victoires")


if __name__ == "__main__":
    main()
