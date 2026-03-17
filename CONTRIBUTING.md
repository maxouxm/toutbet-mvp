# Contributing to ToutBet'

Merci de votre intérêt pour contribuer à ToutBet' !

## Processus de contribution

1. **Fork** le projet
2. Créez une **branche** pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. **Committez** vos changements (`git commit -m 'Add some AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une **Pull Request**

## Standards de code

### Backend (Python)
- Suivez les conventions PEP 8
- Utilisez des type hints
- Documentez les fonctions complexes
- Écrivez des tests pour les nouvelles fonctionnalités

### Frontend (TypeScript/React)
- Utilisez TypeScript strict
- Suivez les conventions de nommage React
- Composants fonctionnels avec hooks
- Styles avec Tailwind CSS

## Configuration de développement

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # ou .\.venv\Scripts\activate sur Windows
pip install -r requirements.txt
cp .env.example .env
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
```

## Tests

Avant de soumettre une PR, assurez-vous que :
- Le code compile sans erreurs
- Les tests existants passent
- Vous avez ajouté des tests pour les nouvelles fonctionnalités

## Sécurité

Si vous découvrez une vulnérabilité de sécurité, veuillez NE PAS ouvrir une issue publique. 
Contactez-nous directement à [security@toutbet.com](mailto:security@toutbet.com).

## Questions ?

N'hésitez pas à ouvrir une issue pour poser des questions ou discuter de nouvelles idées !
