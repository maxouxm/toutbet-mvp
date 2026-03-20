## ToutBet' (MVP) — P2P binary betting (secure-by-default)

Plateforme web **mobile-first** de paris personnalisés entre particuliers.

### Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy 2, Pydantic v2, SQLite, JWT (python-jose), bcrypt (passlib), **SlowAPI** (rate-limit)
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, React Router v6, lucide-react

### Sécurité (résumé)

- **JWT access (15 min)** + **refresh (7 jours)**:
  - refresh en **cookie HttpOnly** (Secure en prod)
  - access en **localStorage** (header `Authorization: Bearer ...`)
- **RBAC** strict + claim `role` dans JWT
- **Rate limiting**: SlowAPI
- **Immutabilité**: paris append-only, résolution admin-only, audit logs append-only + **signés HMAC**
- **OWASP Top 10 (2025)**: validation stricte, auth robuste, CORS strict, erreurs contrôlées, headers, séparation des privilèges

---

## Démarrage rapide

### 1) Backend

Pré-requis: Python 3.12.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m scripts.init_db
python -m scripts.migrate_terms_acceptance
python -m scripts.create_admin
python -m scripts.seed_demo
 python -m uvicorn main:app --reload --host 127.0.0.1 --port 8010
```

API: `http://127.0.0.1:8000` (Swagger: `/docs`)

Admin test:
- email: `admin@toutbet.com`
- password: `admin123`

### 2) Frontend

Pré-requis: Node.js 18+.

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

App: `http://127.0.0.1:5173`

Si ton backend tourne sur un port différent (ex: 8001), configure le frontend :

```powershell
copy .env.example .env
notepad .env
```

Puis relance `npm.cmd run dev`.

---

## Dépannage (Windows)

### `uvicorn` : “not recognized…”

Lance toujours Uvicorn via Python:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### `npm.ps1` bloqué (ExecutionPolicy PowerShell)

Sans changer la policy, utilise `npm.cmd` (comme ci-dessus) ou lance via `cmd.exe`:

```cmd
cd frontend
npm install
npm run dev
```

---

## Variables d’environnement

Voir `backend/.env.example`.

---

## Notes fonctionnelles (MVP)

- Marchés **publics** (pas d’invitation).
- Marchés binaires **Oui/Non**.
- **1 € = 1 jeton** (approvisionnement mock).
- Pools séquestrés: `yes_pool`, `no_pool`.
- Odds dynamiques (lecture):
  - \(prob\_yes = no\_pool / total\_pool\)
  - \(prob\_no = yes\_pool / total\_pool\)
  - Si aucun pari: valeur aléatoire 40–60% (tests)
- Résolution: **ADMIN seulement**, gains crédités automatiquement, **audit logs immutables**.

