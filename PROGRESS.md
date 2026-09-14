# Recal — Suivi d’avancement

## Statut global

**Phase actuelle :** MVP cloud opérationnel. L’agent veille seul dans AWS (étape 6 terminée) ; prochaine phase : frontend Electron et notifications.

**État :** worker Lambda `recal-worker-dev` déployé et validé en conditions réelles (cycle complet : Parallel Search → Claude Haiku 4.5 → scoring → déduplication → 3 opportunités persistées en DynamoDB). Réveil EventBridge `recal-watch-dev` chaque heure, DLQ SQS, IAM least-privilege (rôle Lambda limité au modèle Haiku 4.5 exact, multi-régions US pour l’inference profile). Infrastructure complète décrite dans `infra/template.yaml` (SAM), déployable en 2 commandes. Pipeline CI DevSecOps, tests (34), Ruff, Mypy.

## Validation AWS

Compte `039892245550`, utilisateur IAM `recal_dev`, région `us-east-1`. Modèle `us.anthropic.claude-haiku-4-5-20251001-v1:0` actif. Bedrock validé en réel (local et cloud). Policy de déploiement `recal-deploy-policy` (fichier `infra/recal-deploy-policy.json`) : attachée à `recal_dev`, couvre CloudFormation/S3/IAM/Lambda/DynamoDB/Scheduler/SQS/Logs, tout scopé `recal-*`.

## Déploiement cloud

| Ressource | Nom | Rôle |
|---|---|---|
| Stack CloudFormation | `recal-dev` | Déploiement tout-en-un via SAM. |
| Lambda | `recal-worker-dev` | Cycle de veille complet (timeout 600 s). |
| EventBridge Scheduler | `recal-watch-dev` | Réveil `rate(1 hour)`, fenêtre flexible 5 min, retry 1, DLQ. |
| DynamoDB | `recal-opportunities-dev`, `recal-profiles-dev`, `recal-runs-dev`, `recal-watch-state-dev` | Persistance cloud (PITR activé sur opportunités). |
| SQS | `recal-worker-dlq-dev` | Cycles en échec, rétention 14 jours. |

Procédure : `sam build --use-container --template infra/template.yaml` puis `sam deploy --stack-name recal-dev --resolve-s3 --capabilities CAPABILITY_IAM`. Build Docker obligatoire (pywin32 bloque la résolution pip sous Windows via la dépendance `mcp`).

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
| Configuration de veille | Terminé | `WatchSettings` (enabled, frequency_minutes, allowed_domains, opportunity_types, minimum_relevance_score, daily_max_runs, quotas) exposée via `PUT /api/v1/profile`. |
| État de veille | Terminé | `WatchState` (last_run_at, next_run_at, last_successful_run_at, compteur quotidien, URLs traitées) persisté dans SQLite via `SQLiteWatchStateRepository`. |
| Domaines autorisés | Terminé | Catalogue par défaut par type (`domain/catalog.py`) : liste vide = catalogue, liste explicite = filtrage strict par suffixe de domaine. |
| Recherche web réelle | Terminé | `ParallelSearchAdapter` (MCP JSON-RPC, `https://search.parallel.ai/mcp`) : gratuit, sans clé, testé en conditions réelles. Tavily conservé en fallback optionnel. |
| Cycle local complet | Terminé | Recherche Parallel réelle + filtrage domaines + dédup URLs + Claude Haiku 4.5 + persistance SQLite : `scripts/local_cycle.py`. Validé via container `.env` (Parallel + Strands). |
| Analyseur Claude | Terminé | `StrandsOpportunityAnalyzer` branché : `ANALYZER_PROVIDER=strands` dans `.env`. Cycle réel persiste opportunités avec deadline, organisation, raisons de pertinence. |
| Garde-fous worker | Terminé | Cycle scheduled vérifie : veille activée, pas de cycle actif (queued/running), fréquence respectée, quota quotidien. Skip sans erreur Lambda (`WatchSkippedError`). |
| Persistance DynamoDB | Terminé | Adaptateurs complets (profils avec watch, runs avec URLs, état, verrous `get_active`). Scores convertis en `Decimal` pour boto3. |
| Worker Lambda | Terminé | `recal-worker-dev` déployé, cycle réel validé : 3 opportunités persistées (dont HackMIT 2026, score 80.25). |
| EventBridge Scheduler | Terminé | `recal-watch-dev` : réveil horaire, fenêtre flexible, retry, DLQ SQS avec policy autorisant `scheduler.amazonaws.com`. |
| Infrastructure as Code | Terminé | `infra/template.yaml` (SAM) : tables, Lambda, schedule, DLQ, IAM least-privilege (Bedrock limité au modèle exact). |

## En cours

| Élément | Statut | Prochaine action |
|---|---|---|
| Structure physique du dépôt | Terminé | Dossiers backend, contrats, infrastructure et scripts créés. |
| Contrat OpenAPI | Terminé | `contracts/openapi.yaml` créé avec les routes versionnées et les schémas principaux. À mettre à jour avec `watch` et `urls_processed`. |
| Socle FastAPI | Terminé | Routes reliées aux cas d’usage, validation Pydantic, erreurs uniformes, identifiant de requête, headers de sécurité et CORS ajoutés. Les cycles exposent leur origine `manual` ou `scheduled`. |
| Domaine métier | Terminé | Entités, ports, cas d’usage, runner applicatif et adaptateurs mémoire créés. |

## À faire et intégrations restantes

| Élément | Dépendance |
|---|---|
| Stabilité recherche | Les résultats Parallel varient ; certains cycles ramènent des pages de listing rejetées par l’analyseur (comportement correct). Pistes : augmenter `max_queries_per_run`, affiner les requêtes, ajouter des domaines au catalogue. |
| TTL DynamoDB | Terminé : champ `ttl` calculé par cycle (`deadline` + 30 jours, sinon `verified_at` + 90 jours), `TimeToLiveSpecification` active sur `recal-opportunities-dev`. |
| API cloud | L’API FastAPI tourne en local ; le frontend Electron devra consommer soit cette API locale, soit une API hébergée. Décision d’architecture à prendre. |
| Frontend Electron | Contrat OpenAPI disponible et routes testées. |
| Notifications natives | Intégration frontend et endpoint de nouvelles opportunités. |
| Catalogue domaines | Liste initiale générique en place ; à affiner avec les domaines réellement observés et vérifiés. |
| Tests d’intégration AWS | Cycle cloud validé manuellement (invoke + scan DynamoDB). Automatiser en CI plus tard. Les contrôles locaux passent : 34 tests, Ruff, formatage et Mypy. |
| Documentation de déploiement | Procédure SAM documentée (build + deploy). Variables Sentry, contrôles Secure List, registre `SECURITY.md`, workflow CI documentés. |
| Vidéo et démonstration | MVP complet et reproductible. |

## Décisions importantes

1. SQLite est réservé aux tests locaux ; la persistance cloud cible sera DynamoDB.
2. Les clés AWS et Tavily ne seront jamais embarquées dans Electron.
3. Le backend reste l’unique propriétaire du scoring, de la déduplication et des règles métier.
4. Les routes seront versionnées et documentées avant l’intégration du frontend.
5. AgentCore reste une option ultérieure et ne doit pas bloquer le MVP.
6. Parallel Search MCP est le provider de recherche par défaut : gratuit, sans clé, validé en conditions réelles. Tavily reste disponible en fallback (`SEARCH_PROVIDER=tavily`).
7. L’analyseur par défaut est l’heuristique locale (`ANALYZER_PROVIDER=fake`) pour valider le pipeline sans AWS ; Strands/Claude sera activé par simple changement de variable.
8. Un cycle planifié ignoré (fréquence, quota, verrou, veille désactivée) est un comportement normal : le worker renvoie `skipped` sans faire échouer le scheduler.
9. Le build SAM sous Windows exige `--use-container` (pywin32, dépendance de `mcp`, casse la résolution pip native). Le CodeUri pointe vers `backend/src` contenant son propre `requirements.txt`.
10. Bedrock via inference profile US route dynamiquement entre régions : la policy du rôle Lambda couvre `bedrock:*` (toutes régions) mais uniquement le modèle `anthropic.claude-haiku-4-5-20251001-v1:0` exact.
11. Les nombres DynamoDB exigent `Decimal` (boto3 refuse les floats) : conversion via `_to_decimal` à la sérialisation.

## Critères de sortie de la prochaine étape

Frontend Electron connecté au backend : affichage des opportunités filtrées, notification des nouvelles opportunités, gestion du profil. Préalable : décider où héberger l’API consommée par Electron.

## Journal

### Initialisation

Le projet Recal était vide. Les décisions d’architecture et les responsabilités des couches ont été documentées avant l’implémentation afin de permettre au frontend de consommer un contrat stable.

### Veille locale

Ajout de la configuration et de l’état de veille (garde-fous, quota, URLs traitées), du catalogue de domaines autorisés, de l’adaptateur Parallel Search MCP, du filtrage et de la déduplication dans le runner, des dépôts SQLite correspondants et de l’analyseur heuristique local. Cycle complet validé en conditions réelles : recherche Parallel, opportunités persistées ; second appel scheduled correctement ignoré (`frequency_not_respected`).

### Claude Haiku 4.5 (validation AWS)

Compte et permissions Bedrock validés (modèle actif, invocation testée). Requêtes du runner réorientées vers des pages d’événements plutôt que des agrégateurs. Correctif de pagination SQLite (LIMIT/OFFSET inversés) découvert grâce au cycle réel. `ANALYZER_PROVIDER=strands` activé : cycle complet container persiste des opportunités réelles avec scores, deadlines et raisons.

### Déploiement cloud (étape 6)
Infrastructure as Code SAM (`infra/template.yaml`) : 4 tables DynamoDB, Lambda worker, EventBridge Scheduler horaire avec DLQ SQS, IAM least-privilege. Déploiement réel après itérations IAM (policy `recal-deploy-policy` affinée action par action : CreateChangeSet sur transform SAM, tags S3, DetachRolePolicy, PassRole vers scheduler, GetTemplateSummary) et correctifs template (`FLEXIBLE` majuscule, CodeUri). Bugs runtime corrigés grâce aux invocations réelles : dépendances manquantes (build sans container), `Decimal` exigé par boto3, permissions Bedrock multi-régions. Validation finale : cycle cloud complet persiste 3 opportunités réelles (dont HackMIT 2026, score 80.25) dans `recal-opportunities-dev`.

### Frontend Electron (phase 2)

Stack React + Vite + Tailwind, palette Stitch (Inter + JetBrains Mono, dark). 5 pages : onboarding 4 étapes (langue FR/EN, profil, veille, lancement narratif), Aujourd'hui (grille + modal détail), Sauvegardés (onglets statut + tri), Profil (identité, veille, domaines, état agent live). API consommée en sidecar local → DynamoDB partagé avec le worker cloud. Tray système (fermeture = veille en arrière-plan), splash avec spinner, titlebar overlay. Fix environnementaux : CORS pour localhost:5173/5174, quota quotidien réservé aux cycles planifiés (manuels jamais bloqués), filtre `since` pour nouveautés, notifications automatiques + badge tray via polling 60 s. Fix Electron : path.txt en UTF-16 corrompu (écrire en UTF-8), extraction manuelle du binaire via miroir npmmirror.

### Catalogue enrichi (sources Perplexity, profil Bénin)

Intégration de ~50 nouvelles sources par catégorie : hackathons (hackathon.com, devfolio.co, zindi.africa, kaggle.com, ethglobal.com, hackathons.space), stages (glassdoor.com, wellfound.com, relocate.me, remoteok.com, weworkremotely.com, careers.un.org, app.unv.org, euraxess), fellowships (GSoC, outreachy.org, LFX, profellow.com, africanleadershipacademy.org), bourses (campusfrance.org, Erasmus Mundus, educanada.ca, Commonwealth, scholarshippositions.com, wemakescholars.com, findamasters.com, studyportals.com), conférences (10times.com, eventbrite.com, meetup.com, lu.ma, IEEE, ACM, pydata.org, owasp.org, africatechsummit.com), certifications (netacad.com, grow.google, skillsbuild.org, skillbuilder.aws, cisco.com, fortinet, isc2.org, linuxfoundation.org). Agrégateurs tout-en-un (youthop.com, opportunitydesk.org, polenexus.com, etc.) toujours inclus via SHARED_AGGREGATORS. Requêtes conference/certification ajoutées. 40 tests verts.

### Relooking dark modernisé + interactions instantanées

Motion system CSS (fade-in, rise en cascade, scale-in, shimmer, glass, respect prefers-reduced-motion). Accent vivid `#8fa0ff` + ombres glow sur hover. Cartes : lift + glow au survol, press au clic. UI optimiste : Sauver/Passer appliqués instantanément avec rollback si l'API échoue (Today + Saved). Modal détail en glass + blur + scale-in. Skeletons shimmer au lieu de pulse brut. Fondu à chaque navigation. Boutons primary avec glow + press. Étapes onboarding animées.

### i18n FR/EN complet

Dictionnaires typés (`src/i18n/dictionaries.ts`), `LanguageProvider` + hook `useLanguage`, persistance `recal:lang`, attribut `lang` HTML synchronisé. Tout l'UI converti : nav, onboarding (toggle live + options traduites), Today (onglets, modal, dates localisées), Saved, Profil (synchro bidirectionnelle avec `profile.language` backend). Notifications toasts traduites. Build vert.

### API cloud pour le jury (Lambda Function URL + clé API)

`recal-api-dev` : FastAPI exposée via Mangum sur Function URL publique (AuthType NONE, protection par middleware `x-api-key` actif uniquement si `API_KEY` configurée). Paramètre SAM `ApiKey` (NoEcho). CORS ouvert via `CORS_ALLOW_ALL` pour l'Electron packagé (origin file://). Sécurité : clé jamais loggée/committée, rate-limit 429 + quota quotidien DynamoDB comme remparts coûts, Bedrock limité au modèle exact. Frontend : header `x-api-key` depuis `VITE_API_KEY` (absent en dev = pas de header), erreur 401 explicite. 6 tests `test_api_auth.py` (ouvert/fermé/mauvaise clé/health/preflight). 46 tests verts.

### Refonte Convex cream-paper (branche feat/try-refonte)

Brief DESIGN.md : toile crème #f6f6f6, encre #141414, Inter, hairlines #e5e5e5, zéro ombre, accents sémantiques. Implémentation par remap complet de la palette Tailwind (mêmes tokens, nouvelles valeurs — bonus : `bg-surface-container` jusque-là absent de la config, donc transparent, est réparé). Boutons primary encre remplie, badges deadline clairs (rouge #b91c1c / ambre #92400e), badges type en teintes lisibles (iris, plum, ember), sliders encre, modal détail en carte blanche (fini le glass sombre), skeletons clairs, sélection de texte ink-on-cream. Overlay Electron et fond de fenêtre passés en crème (boutons natifs sinon invisibles). Motion system conservé.

### Gestion erreurs offline + suppression cadratins

Client API : `BACKEND_OFFLINE` levé sur échec réseau (TypeError), distingué des erreurs métier. Panneaux offline dédiés (icône cloud_off, titre localisé, bouton Réessayer qui recharge) sur Today, Saved, Profil (fini les skeletons infinis et le "Failed to fetch" brut). Save/run mappent le code vers le message localisé. Zéro "—" restant dans tout l'UI : remplacés par "·", placeholders localisés ("Sans échéance", "Non renseigné", "Jamais").

### Mode hors-ligne + toggle clair/sombre

Tokens Tailwind résolus via variables CSS (`:root` = Convex cream, `.dark` = palette sombre d'origine) : le thème commute instantanément sans recharger. Store `src/theme.ts` (persisté `recal:theme`, défaut = préférence OS), script anti-flash dans index.html, overlay natif Electron synchronisé via IPC `recal:setTheme`. Toggle Clair/Sombre dans Profil. Cache localStorage des 50 dernières opportunités : backend coupé = bannière "Mode hors-ligne · dernière synchro" + bouton Réessayer sur Today et Saved (au lieu du panneau d'erreur quand un cache existe). Badges et sliders passés en tokens adaptatifs aux deux thèmes.

### Contrat OpenAPI synchronisé

`contracts/openapi.yaml` aligné sur l'implémentation (vérifié par diff automatique : 8 chemins identiques, 19 refs résolues) : route `GET /api/v1/watch` + schéma `WatchState`, paramètre `?since=`, `securityScheme ApiKeyAuth` (x-api-key) sur toutes les routes sauf `/health`, réponses 401/409/429, types `conference`/`certification`, champs profil (`full_name`, `language`, `mobility_countries`, `watch`), schéma `WatchSettings` complet, champs `Run` manquants (`error_message`, `urls_processed`).
