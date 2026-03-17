# Politique de sécurité

## Versions supportées

| Version | Supportée          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Signaler une vulnérabilité

La sécurité de ToutBet' est une priorité. Si vous découvrez une vulnérabilité de sécurité, nous apprécions votre aide pour la divulguer de manière responsable.

**Merci de NE PAS signaler les vulnérabilités de sécurité via les issues publiques GitHub.**

À la place, veuillez envoyer un email à **security@toutbet.com** avec :

- Une description de la vulnérabilité
- Les étapes pour reproduire le problème
- Les versions affectées
- Tout correctif ou solution de contournement que vous avez identifié

### Ce que vous pouvez attendre

- Accusé de réception dans les 48 heures
- Mise à jour régulière sur la progression
- Crédit dans les notes de version (si vous le souhaitez)

## Pratiques de sécurité

ToutBet' implémente plusieurs mesures de sécurité :

- **Authentification JWT** avec tokens d'accès à courte durée de vie (15 min)
- **Refresh tokens** en cookies HttpOnly
- **Rate limiting** sur toutes les routes API
- **RBAC** (Role-Based Access Control) strict
- **Validation stricte** des entrées utilisateur
- **Logs d'audit** signés HMAC pour la non-répudiation
- **CORS** strict configuré
- **Protection OWASP Top 10**

## Meilleures pratiques pour les contributeurs

- Ne committez jamais de secrets, clés API, ou credentials
- Utilisez toujours les fichiers `.env.example` comme templates
- Validez toutes les entrées utilisateur
- Utilisez des requêtes paramétrées pour éviter les injections SQL
- Échappez les sorties pour prévenir XSS
- Implémentez une gestion appropriée des erreurs sans exposer d'informations sensibles
