# TECHCORP_IA

DevAssist-GPT est un assistant expérimental pour les questions sur Python,
FastAPI, les API REST, Git et Docker. Il s'appuie sur Ollama pour exécuter le
modèle localement, sur FastAPI pour l'API et sur Streamlit pour l'interface de
chat.

## Prérequis

- Docker Desktop avec Docker Compose.
- Une connexion Internet au premier démarrage pour télécharger l'image Ollama
  et le modèle `qwen2.5:7b`.
- Plusieurs gigaoctets d'espace disque disponibles pour le modèle.

Les fichiers GGUF du modèle ne sont pas stockés dans GitHub. Ollama télécharge
le modèle automatiquement dans son volume Docker au premier démarrage.

## Démarrer l'application

Depuis la racine du projet :

```powershell
docker compose -f deploy/compose.yml up --build
```

À la première exécution, le téléchargement du modèle peut prendre du temps.
Quand les services sont prêts :

- Interface de chat : <http://localhost:8501>
- API et documentation interactive : <http://localhost:8000/docs>
- Vérification de disponibilité : <http://localhost:8000/health>

Arrêter les services avec `Ctrl+C`, ou dans un autre terminal :

```powershell
docker compose -f deploy/compose.yml down
```

Le modèle téléchargé est conservé dans un volume Docker. Pour supprimer aussi
ce modèle et les autres données persistées, exécuter
`docker compose -f deploy/compose.yml down --volumes`.

## Utiliser l'API

Exemple PowerShell :

```powershell
$body = @{
  messages = @(
    @{ role = "user"; content = "Explique la différence entre GET et POST." }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Uri http://localhost:8000/api/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

L'API accepte jusqu'à 20 messages `user`/`assistant` par conversation. Le
dernier message doit venir de l'utilisateur.

## Lancer les tests

Avec Python 3.11 ou plus récent :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r api/requirements-dev.txt
python -m pytest
```

## Structure

```text
api/          API FastAPI et tests
dataset/      Exemples de questions et réponses
deploy/       Configuration Docker Compose
frontend/     Interface Streamlit
model/        Modelfile Ollama (les poids du modèle sont exclus)
```

## Sécurité et confidentialité

Cette application est un prototype destiné à être exécuté localement. L'API et
l'interface sont liées à `127.0.0.1` dans Docker Compose et ne sont pas prévues
pour être exposées directement sur Internet. Ajouter une authentification, des
limites de requêtes et une configuration de déploiement sécurisée avant tout
hébergement public. Ne placez pas de secrets ni de données confidentielles
dans le dépôt ou dans les conversations.
