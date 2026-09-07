# Recal Backend

## Responsabilité

Ce service expose l’API consommée par Electron et exécute le pipeline de veille. Le frontend ne doit jamais appeler directement Amazon Bedrock, Strands, Tavily ou DynamoDB.

## Architecture

Le backend suit une architecture hexagonale :

- `src/recal/domain` contient les entités et règles métier sans dépendance externe.
- `src/recal/application` contient les ports et cas d’usage utilisés par l’API et le worker.
- `src/recal/adapters` contient les implémentations mémoire et les intégrations Tavily/Strands.
- `src/recal/infrastructure` contiendra la configuration AWS, DynamoDB et l’injection de dépendances.
- `src/recal/interfaces` contient les schémas d’API.

## Installation locale

Depuis le dossier `backend` :

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -e ".[dev,agent,search]"
```

Copier `.env.example` vers `.env`, puis renseigner uniquement la configuration locale sans jamais committer les secrets. Le venv isole les dépendances Python ; le fichier `.env` configure Recal ; les credentials AWS sont idéalement fournis par un profil AWS CLI/SSO nommé dans `AWS_PROFILE`.

### Configuration AWS locale recommandée

Depuis PowerShell, après installation d’AWS CLI :

```powershell
aws configure --profile recal-dev
$env:AWS_PROFILE = "recal-dev"
$env:AWS_REGION = "us-east-1"
```

Le backend utilise ensuite boto3 pour résoudre automatiquement les credentials du profil. Ne pas ajouter `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` ou `AWS_SESSION_TOKEN` dans le dépôt. Si des clés temporaires sont absolument nécessaires pour un environnement local, elles doivent être définies uniquement dans le gestionnaire de secrets ou les variables d’environnement de cette machine.

## Vérification

```bash
python -m pytest -q
python -m compileall -q src
```

## Lancer l’API

```bash
uvicorn recal.main:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

Documentation interactive : `http://127.0.0.1:8000/docs`.

## AWS et Bedrock

La région cible est `us-east-1`. Avant d’activer le runner cloud, il faut vérifier :

1. que le modèle Claude Haiku 4.5 choisi est réellement disponible dans cette région ;
2. que le rôle ou profil AWS dispose de `bedrock:InvokeModel` et, si nécessaire, `bedrock:InvokeModelWithResponseStream` ;
3. que l’identifiant exact du modèle est reporté dans `BEDROCK_MODEL_ID` ;
4. que la facturation et les crédits du compte couvrent les appels de test.

Le code de l’agent utilise la sortie structurée Pydantic de Strands afin de valider les opportunités avant leur entrée dans le domaine métier.

## Limites de sécurité et de coût

Le runner limite le nombre de recherches à trois par cycle. Tavily est appelé uniquement côté backend et les résultats sont bornés. Le score final est calculé côté application à partir des sous-scores retournés, et non accepté aveuglément depuis le modèle.

## Routes

Le contrat de référence se trouve dans `../contracts/openapi.yaml`. FastAPI expose aussi automatiquement `/docs`, `/redoc` et `/openapi.json` lorsque l’application est démarrée.
