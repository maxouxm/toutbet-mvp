"""
=======================================================================
 ToutBet' – Tests automatisés des Abuse Stories (Étape 3 – E2E)
=======================================================================
Objectif : vérifier que l'API rejette correctement les requêtes malveillantes.

Abuse stories testées :
  1. Pari à montant négatif  → doit être rejeté (400 / 422)
  2. Pari sur un marché clôturé → doit être rejeté (400)
  3. Injection XSS dans le titre d'un marché → doit être rejeté (422)
     ou, si accepté, signalé comme VULNÉRABLE (XSS stocké)

Usage :
  Assurez-vous que le backend tourne sur http://127.0.0.1:8010, puis :
    python tests_abuse_stories.py
"""

import datetime
import json
import requests

# ── Configuration ────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8010"

# Compte de test créé dynamiquement par le script lui-même
USER_EMAIL    = "abuse_tester@example.com"
USER_PASSWORD = "TestPassword123!"

# Payload XSS classique à injecter dans le champ titre d'un marché
XSS_PAYLOAD = "<script>alert('XSS')</script>"

# ── Résultats accumulés ───────────────────────────────────────────────
resultats: list[dict] = []


# ── Helpers ───────────────────────────────────────────────────────────

def register_test_user(email: str, password: str) -> None:
    """Enregistre le compte de test si celui-ci n'existe pas encore."""
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "accept_terms": True},
        timeout=10,
    )
    if resp.status_code == 201:
        print(f"    Compte de test créé : {email}")
    elif resp.status_code == 400 and "already" in resp.text.lower():
        print(f"    Compte de test existant : {email}")
    else:
        raise RuntimeError(f"Erreur à la création du compte: HTTP {resp.status_code}: {resp.text}")


def login(email: str, password: str) -> str:
    """Authentifie un utilisateur et retourne son access token JWT."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Échec de connexion pour {email} – HTTP {resp.status_code}: {resp.text}"
        )
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    """Retourne les en-têtes HTTP avec le token Bearer."""
    return {"Authorization": f"Bearer {token}"}


def enregistrer_resultat(
    nom: str,
    payload: object,
    status_code: int,
    resultat: str,
    detail: str = "",
) -> None:
    """Stocke le résultat d'un test et l'affiche dans la console."""
    entree = {
        "nom":         nom,
        "payload":     json.dumps(payload, ensure_ascii=False),
        "status_http": status_code,
        "resultat":    resultat,   # "SÉCURISÉ" | "VULNÉRABLE"
        "detail":      detail,
    }
    resultats.append(entree)

    icone = "✅" if resultat == "SÉCURISÉ" else "❌"
    print(f"\n{icone}  [{nom}]")
    print(f"   Payload      : {entree['payload']}")
    print(f"   Statut HTTP  : {status_code}")
    print(f"   Résultat     : {resultat}")
    if detail:
        print(f"   Détail       : {detail}")


def get_open_and_resolved_markets(token: str) -> tuple[int | None, int | None]:
    """
    Récupère l'identifiant d'un marché ouvert et d'un marché résolu
    parmi la liste pubqliue des marchés.
    Retourne (open_id, resolved_id) – None si introuvable.
    """
    resp = requests.get(f"{BASE_URL}/public/markets", timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Impossible de récupérer les marchés: HTTP {resp.status_code}")

    markets = resp.json()
    open_id     = None
    resolved_id = None

    for m in markets:
        if m["status"] == "open"     and open_id     is None:
            open_id = m["id"]
        if m["status"] == "resolved" and resolved_id is None:
            resolved_id = m["id"]
        if open_id and resolved_id:
            break

    return open_id, resolved_id


# ── Tests ─────────────────────────────────────────────────────────────

def test_pari_negatif(token: str, open_market_id: int) -> None:
    """
    ABUSE STORY 1 – Pari à montant négatif
    ----------------------------------------
    Un attaquant envoie amount_tokens = -50 pour tenter d'augmenter
    son solde au lieu de le décrémenter.
    Attendu : 400 ou 422  →  SÉCURISÉ
    Si 201 retourné       →  VULNÉRABLE (solde corrompu)
    """
    payload = {"side": "yes", "amount_tokens": -50}
    resp = requests.post(
        f"{BASE_URL}/api/markets/{open_market_id}/bets",
        json=payload,
        headers=auth_headers(token),
        timeout=10,
    )

    if resp.status_code in (400, 422):
        enregistrer_resultat(
            nom="Pari à montant négatif",
            payload=payload,
            status_code=resp.status_code,
            resultat="SÉCURISÉ",
            detail="Le serveur a correctement rejeté le montant invalide.",
        )
    else:
        enregistrer_resultat(
            nom="Pari à montant négatif",
            payload=payload,
            status_code=resp.status_code,
            resultat="VULNÉRABLE",
            detail=(
                "ÉCHEC DE SÉCURITÉ : le serveur a accepté un montant négatif. "
                "Le solde de l'utilisateur pourrait être corrompu."
            ),
        )


def test_pari_marche_cloture(token: str, resolved_market_id: int) -> None:
    """
    ABUSE STORY 2 – Pari hors délai (marché clôturé)
    --------------------------------------------------
    Un attaquant tente de parier sur un marché dont le statut est 'resolved'.
    Attendu : 400  →  SÉCURISÉ
    Si 201 retourné →  VULNÉRABLE (intégrité du marché compromise)
    """
    payload = {"side": "yes", "amount_tokens": 10}
    resp = requests.post(
        f"{BASE_URL}/api/markets/{resolved_market_id}/bets",
        json=payload,
        headers=auth_headers(token),
        timeout=10,
    )

    if resp.status_code in (400, 403, 422):
        enregistrer_resultat(
            nom="Pari sur marché clôturé",
            payload={**payload, "market_id": resolved_market_id},
            status_code=resp.status_code,
            resultat="SÉCURISÉ",
            detail="Le serveur a correctement refusé le pari sur un marché résolu.",
        )
    else:
        enregistrer_resultat(
            nom="Pari sur marché clôturé",
            payload={**payload, "market_id": resolved_market_id},
            status_code=resp.status_code,
            resultat="VULNÉRABLE",
            detail=(
                "ÉCHEC DE SÉCURITÉ : le serveur a accepté un pari sur un marché clôturé. "
                "Les pools et le solde ont pu être modifiés illégitimement."
            ),
        )


def test_xss_injection(token: str) -> None:
    """
    ABUSE STORY 3 – Injection XSS dans le titre d'un marché
    ---------------------------------------------------------
    Un attaquant crée un marché dont le titre contient du JavaScript.
    Si l'API stocke ce contenu tel quel et que le frontend le rend
    sans échappement, cela déclenche un XSS stocké.
    Attendu : 422 (validation Pydantic)  →  SÉCURISÉ
    Si 201 retourné                       →  VULNÉRABLE (XSS stocké potentiel)
    """
    payload = {
        "title":       XSS_PAYLOAD,
        "description": (
            "Description de test pour vérifier la résistance au XSS. "
            "Ce champ doit être suffisamment long pour passer la validation."
        ),
    }
    resp = requests.post(
        f"{BASE_URL}/api/markets",
        json=payload,
        headers=auth_headers(token),
        timeout=10,
    )

    if resp.status_code == 422:
        enregistrer_resultat(
            nom="Injection XSS dans le titre",
            payload=payload,
            status_code=resp.status_code,
            resultat="SÉCURISÉ",
            detail="Le serveur a rejeté le payload XSS via la validation Pydantic.",
        )
    elif resp.status_code == 201:
        enregistrer_resultat(
            nom="Injection XSS dans le titre",
            payload=payload,
            status_code=resp.status_code,
            resultat="VULNÉRABLE",
            detail=(
                "ÉCHEC DE SÉCURITÉ : le payload XSS a été accepté et stocké en base. "
                "Si le frontend affiche ce titre sans échappement HTML, "
                "le script s'exécutera dans le navigateur de toute victime consultant le marché."
            ),
        )
    else:
        enregistrer_resultat(
            nom="Injection XSS dans le titre",
            payload=payload,
            status_code=resp.status_code,
            resultat="VULNÉRABLE",
            detail=f"Réponse inattendue du serveur: {resp.text[:200]}",
        )


# ── Génération du compte-rendu ────────────────────────────────────────

def generer_compte_rendu() -> None:
    """Écrit le fichier compte_rendu_tests.txt avec le résumé de tous les tests."""
    chemin = "compte_rendu_tests.txt"
    lignes: list[str] = []
    separateur = "=" * 70

    lignes.append(separateur)
    lignes.append("  COMPTE-RENDU – TESTS ABUSE STORIES – ToutBet'")
    lignes.append(f"  Généré le : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lignes.append(f"  Cible     : {BASE_URL}")
    lignes.append(separateur)
    lignes.append("")

    securise  = sum(1 for r in resultats if r["resultat"] == "SÉCURISÉ")
    vulnerable = sum(1 for r in resultats if r["resultat"] == "VULNÉRABLE")

    lignes.append(f"  Résumé : {securise} SÉCURISÉ(s)  |  {vulnerable} VULNÉRABLE(s)  "
                  f"|  {len(resultats)} test(s) au total")
    lignes.append("")

    for i, r in enumerate(resultats, start=1):
        lignes.append(f"─── Test {i} : {r['nom']} " + "─" * max(0, 50 - len(r['nom'])))
        lignes.append(f"  Payload envoyé  : {r['payload']}")
        lignes.append(f"  Statut HTTP     : {r['status_http']}")
        lignes.append(f"  Résultat        : {r['resultat']}")
        if r["detail"]:
            lignes.append(f"  Détail          : {r['detail']}")
        lignes.append("")

    lignes.append(separateur)
    lignes.append("  FIN DU RAPPORT")
    lignes.append(separateur)

    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))

    print(f"\n📄  Compte-rendu généré : {chemin}")


# ── Point d'entrée ─────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  ToutBet' – Tests Abuse Stories (Étape 3)")
    print("=" * 60)

    # 1. Création du compte de test + authentification
    print(f"\n🔐  Préparation du compte de test ({USER_EMAIL}) ...")
    register_test_user(USER_EMAIL, USER_PASSWORD)
    token = login(USER_EMAIL, USER_PASSWORD)
    # Créditer le compte pour pouvoir parier (fonds nécessaires pour test 2)
    requests.post(
        f"{BASE_URL}/api/fund",
        json={"amount_eur": 100},
        headers=auth_headers(token),
        timeout=10,
    )
    print("    Token obtenu ✓")

    # 2. Récupération des marchés de référence
    print("\n🔍  Recherche d'un marché ouvert et d'un marché clôturé ...")
    open_id, resolved_id = get_open_and_resolved_markets(token)

    if open_id is None:
        print("    ⚠️  Aucun marché ouvert trouvé – test 1 ignoré.")
    else:
        print(f"    Marché ouvert    : ID {open_id}")

    if resolved_id is None:
        print("    ⚠️  Aucun marché clôturé trouvé – test 2 ignoré.")
    else:
        print(f"    Marché clôturé   : ID {resolved_id}")

    # 3. Exécution des tests
    print("\n🧪  Lancement des tests ...\n" + "-" * 60)

    if open_id is not None:
        test_pari_negatif(token, open_id)

    if resolved_id is not None:
        test_pari_marche_cloture(token, resolved_id)

    test_xss_injection(token)

    # 4. Compte-rendu
    generer_compte_rendu()

    print("\n" + "=" * 60)
    print("  Tests terminés.")
    print("=" * 60)

    # Exit code non-zéro si au moins une vulnérabilité détectée
    # (permet au pipeline CI de signaler l'échec correctement)
    nb_vulnerables = sum(1 for r in resultats if r["resultat"] == "VULNÉRABLE")
    if nb_vulnerables:
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
