# Recal - Agent autonome de veille d’opportunités

## Vision

Recal est un agent personnel qui surveille automatiquement les hackathons, stages, fellowships et bourses correspondant au profil d’un étudiant. Il recherche les opportunités, comprend leur contexte, vérifie leur compatibilité avec le profil, calcule un score explicable, élimine les doublons et notifie uniquement les résultats utiles.

## Objectif du MVP

Le MVP doit exécuter un cycle complet et reproductible : un déclencheur planifié lance le backend, l’agent Strands utilise Tavily pour rechercher des opportunités, Claude Haiku 4.5 extrait les informations structurées, le backend valide et score les résultats, la persistance évite les doublons, puis le frontend pourra récupérer les nouvelles opportunités et afficher une notification.

## Principes d’architecture

Le frontend Electron et le backend sont séparés. Le frontend ne possède aucune clé AWS, Bedrock ou Tavily et communique uniquement avec l’API backend documentée.

Le backend adopte une architecture hexagonale inspirée de la Clean Architecture. Le domaine ne dépend d’aucun framework, les cas d’utilisation orchestrent les règles métier, les ports définissent les contrats et les adaptateurs relient les services externes comme Strands, Bedrock, Tavily et DynamoDB.

## Architecture cible

```text
Electron frontend
        │ HTTPS / REST / JSON
        ▼
Backend API — FastAPI
        │
        ├── Domain : Opportunity, UserProfile, Notification
        ├── Application : use cases et ports
        ├── Adapters : HTTP, Strands, Tavily, persistance
        ├── Infrastructure : configuration, AWS, observabilité
        └── Interfaces : routes REST, schémas API
                │
                ├── Strands Agents SDK
                ├── Amazon Bedrock — Claude Haiku 4.5
                ├── Tavily Search API
                └── DynamoDB

EventBridge Scheduler → Lambda worker → même couche application
```

## Architecture des dossiers

```text
Recal/
├── PROJECT.md
├── PROGRESS.md
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/recal/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── adapters/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   ├── tests/
│   └── docs/
├── contracts/
│   └── openapi.yaml
├── infra/
│   └── README.md
└── scripts/
```

## Modules backend

| Module | Responsabilité |
|---|---|
| `domain` | Entités, value objects, règles métier et erreurs métier. |
| `application` | Cas d’utilisation : lancer une veille, évaluer une opportunité, dédupliquer, gérer le profil. |
| `adapters` | Implémentations concrètes des ports : Tavily, Strands, DynamoDB, horloge et notifications. |
| `infrastructure` | Configuration, injection de dépendances, clients AWS, logs et démarrage. |
| `interfaces` | Routes FastAPI, modèles de requêtes/réponses et gestion des erreurs HTTP. |

## Contrat frontend/backend initial

Les routes seront versionnées sous `/api/v1` et documentées automatiquement avec OpenAPI :

| Méthode | Route | Usage |
|---|---|---|
| `GET` | `/api/v1/health` | Vérifier la disponibilité du backend. |
| `GET` | `/api/v1/profile` | Lire le profil courant. |
| `PUT` | `/api/v1/profile` | Modifier les préférences utilisateur. |
| `GET` | `/api/v1/opportunities` | Lister les opportunités filtrées et paginées. |
| `GET` | `/api/v1/opportunities/{id}` | Lire le détail d’une opportunité. |
| `POST` | `/api/v1/opportunities/{id}/feedback` | Enregistrer un intérêt ou un refus. |
| `POST` | `/api/v1/runs` | Déclencher manuellement un cycle en développement. |
| `GET` | `/api/v1/runs/{id}` | Consulter le statut d’un cycle. |

## Dépendances externes

Le modèle cible est Claude Haiku 4.5 via Amazon Bedrock dans `us-east-1`. L’accès réel au modèle, les permissions IAM et l’identifiant exact du modèle devront être validés avant le déploiement. La clé Tavily restera uniquement côté backend et sera fournie par variable d’environnement ou gestionnaire de secrets.

## Règles de qualité

Le domaine et les cas d’utilisation doivent être testables sans AWS. Les adaptateurs externes doivent être remplaçables par des fakes dans les tests. Les routes ne doivent contenir aucune logique métier complexe. Chaque cycle doit être idempotent et limité en durée, en nombre de recherches et en consommation de modèle.

## Feuille de route

1. Initialiser la structure backend et les contrats API.
2. Implémenter le domaine et les cas d’utilisation sans dépendances cloud.
3. Ajouter les routes FastAPI et la documentation OpenAPI.
4. Ajouter l’adaptateur Tavily et l’agent Strands avec Claude Haiku 4.5.
5. Ajouter la persistance locale de test puis DynamoDB.
6. Déployer le worker avec Lambda et EventBridge.
7. Connecter le frontend Electron aux routes documentées.
8. Ajouter observabilité, sécurité, tests d’intégration et préparation de la démonstration.


