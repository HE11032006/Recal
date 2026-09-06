# Recal — Suivi d’avancement

## Statut global

**Phase actuelle :** initialisation de l’architecture backend et des contrats frontend/backend.

**État :** structure du dépôt, documentation de vision, contrat OpenAPI et socle FastAPI initial créés.

## Terminé

| Élément | Statut | Détails |
|---|---|---|
| Orientation AWS | Terminé | Le projet est réorienté vers AWS Agents for Humans. |
| Région cible | Défini | `us-east-1`, à confirmer dans les configurations AWS. |
| Modèle cible | Défini | Claude Haiku 4.5 via Amazon Bedrock, sous réserve de validation de l’identifiant et des permissions. |
| Séparation frontend/backend | Défini | Electron consommera uniquement l’API backend. |
| Architecture backend | Défini | Architecture hexagonale inspirée de Clean Architecture. |
| Document de vision | Terminé | Voir `PROJECT.md`. |
| Contrat initial des routes | Défini | Routes versionnées sous `/api/v1`, à formaliser dans OpenAPI. |

## En cours

| Élément | Statut | Prochaine action |
|---|---|---|
| Structure physique du dépôt | Terminé | Dossiers backend, contrats, infrastructure et scripts créés. |
| Contrat OpenAPI | Terminé | `contracts/openapi.yaml` créé avec les routes versionnées et les schémas principaux. |
| Socle FastAPI | En cours | Application FastAPI, documentation interactive et `/api/v1/health` créés ; tests à ajouter. |
| Domaine métier | En cours | Entités et ports applicatifs initiaux créés ; cas d’usage et adaptateurs à compléter. |

## Non commencé

| Élément | Dépendance |
|---|---|
| Agent Strands | Socle backend et configuration Bedrock. |
| Intégration Tavily | Variable d’environnement et adaptateur de recherche. |
| Scoring explicable | Entités et cas d’utilisation stabilisés. |
| Déduplication | Modèle d’opportunité et persistance définis. |
| DynamoDB | Schéma de persistance et clés d’idempotence. |
| Lambda worker | Pipeline applicatif fonctionnel localement. |
| EventBridge Scheduler | Worker déployable et permissions IAM. |
| Frontend Electron | Contrat OpenAPI disponible et routes testées. |
| Notifications natives | Intégration frontend et endpoint de nouvelles opportunités. |
| Tests d’intégration AWS | Services cloud accessibles dans `us-east-1`. |
| Documentation de déploiement | Infrastructure et variables d’environnement stabilisées. |
| Vidéo et démonstration | MVP complet et reproductible. |

## Décisions importantes

1. SQLite est réservé aux tests locaux ; la persistance cloud cible sera DynamoDB.
2. Les clés AWS et Tavily ne seront jamais embarquées dans Electron.
3. Le backend reste l’unique propriétaire du scoring, de la déduplication et des règles métier.
4. Les routes seront versionnées et documentées avant l’intégration du frontend.
5. AgentCore reste une option ultérieure et ne doit pas bloquer le MVP.

## Critères de sortie de la prochaine étape

La prochaine étape sera considérée comme terminée lorsque le dépôt contiendra la structure backend, `contracts/openapi.yaml`, une API FastAPI démarrable, la route `/api/v1/health`, les modèles de requêtes/réponses principaux et des tests unitaires de base.

## Journal

### Initialisation

Le projet Recal était vide. Les décisions d’architecture et les responsabilités des couches ont été documentées avant l’implémentation afin de permettre au frontend de consommer un contrat stable.
