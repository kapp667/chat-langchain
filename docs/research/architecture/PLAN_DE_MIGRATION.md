# Plan de Migration - Chat LangChain vers Architecture Moderne

**Date**: 30 septembre 2025
**Contexte**: Migration SawUp pour support Cloud Weaviate + MCP Claude Code
**Objectif**: Migrer vers LangChain 0.3 + Pydantic v2 + Weaviate v4

---

## Sommaire Exécutif

### Pourquoi cette migration ?

**Problème actuel**: Les clusters Weaviate Cloud créés après janvier 2024 sont incompatibles avec le client Weaviate Python v3.x utilisé dans ce projet.

**Besoins SawUp**:
- Base de données vectorielle distante (multi-utilisateurs)
- Backend stable et maintenable long terme
- Interface MCP pour Claude Code (questions LangChain en développement)
- Base pour système de connaissance d'entreprise

**Bénéfices de la migration**:
- ✅ Compatibilité avec Weaviate Cloud moderne
- ✅ Pérennité (Pydantic v1 EOL juin 2024)
- ✅ Versions stables et maintenues
- ✅ Meilleure performance (gRPC dans Weaviate v4)

---

## Analyse d'Impact

### Code Impacté

| Fichier | Lignes totales | Lignes à modifier | % Impact | Complexité |
|---------|----------------|-------------------|----------|------------|
| `backend/main.py` | 115 | ~10 | 8.7% | 🟢 FAIBLE |
| `backend/chain.py` | 278 | ~30-40 | 10-14% | 🟡 MODÉRÉE |
| `backend/ingest.py` | 166 | ~20-30 | 12-18% | 🟡 MODÉRÉE |
| **TOTAL** | **559** | **~50-80** | **9-14%** | **🟡 MODÉRÉE** |

### Dépendances Impactées

#### Avant (actuel)
```toml
langchain = "^0.1.12"
langchain-core = "0.1.31"
weaviate-client = "^3.23.2"
pydantic = "1.10"
```

#### Après (cible)
```toml
langchain = "^0.3.0"
langchain-core = "^0.3.0"
weaviate-client = "^4.17.0"
langchain-weaviate = "^0.0.5"
pydantic = "^2.8.0"
```

### Compatibilité des Dépendances

| Dépendance | Statut | Notes |
|------------|--------|-------|
| LangChain 0.3 + Pydantic v2 | ✅ Compatible | Support natif |
| FastAPI + Pydantic v2 | ✅ Compatible | FastAPI supporte Pydantic v2 |
| Weaviate v4 + Pydantic v2 | ✅ Compatible | Requis par v4 |
| langchain-core 0.1.31 | ⚠️ Transition | Supporte déjà `pydantic >=1,<3` |

---

## Plan de Migration Détaillé

### Phase 0 : Préparation (5 min)

#### 0.1 Sauvegarde
```bash
git checkout -b backup-before-migration
git commit -am "Backup avant migration vers LangChain 0.3"
git checkout langserve
git checkout -b feature/langchain-v3-weaviate-v4-migration
```

#### 0.2 Documentation de l'état actuel
```bash
poetry show > docs/dependencies-before-migration.txt
poetry export -f requirements.txt > docs/requirements-before-migration.txt
```

---

### Phase 1 : Mise à Jour des Dépendances (10-15 min)

#### 1.1 Upgrade Poetry dependencies

```bash
# Retirer l'ancienne version de weaviate-client
poetry remove weaviate-client

# Ajouter les nouvelles versions
poetry add langchain@^0.3
poetry add langchain-core@^0.3
poetry add weaviate-client@^4.17
poetry add langchain-weaviate@^0.0.5
poetry add pydantic@^2.8

# Mettre à jour les packages d'intégration LangChain
poetry add langchain-community@latest
poetry add langchain-openai@latest
poetry add langchain-anthropic@latest
```

#### 1.2 Vérification des conflits

```bash
poetry lock
poetry install
```

**Points de vigilance**:
- Vérifier que FastAPI reste compatible
- Vérifier que langserve fonctionne avec les nouvelles versions

#### 1.3 Installation de langchain-cli (pour migrations automatiques)

```bash
poetry add langchain-cli --group dev
```

---

### Phase 2 : Migration Automatisée avec langchain-cli (5 min)

#### 2.1 Exécuter les migrations automatiques

```bash
# Migration des imports deprecated
poetry run langchain-cli migrate backend/

# Migration pydantic.v1 → pydantic
poetry run langchain-cli migrate backend/ --disable-all --only pydantic-v1-removal
```

**Ce qui sera automatiquement migré**:
- `from langchain.chat_models import ChatOpenAI` → `from langchain_openai import ChatOpenAI`
- `from langchain_core.pydantic_v1 import BaseModel` → `from pydantic import BaseModel`
- Autres imports deprecated

#### 2.2 Vérifier les changements

```bash
git diff backend/
```

---

### Phase 3 : Migration Manuelle - Weaviate v4 (20-25 min)

#### 3.1 Migration de `backend/ingest.py`

**Changements requis** (lignes 11-18, 109-124):

##### Avant (Weaviate v3)
```python
import weaviate
from langchain_community.vectorstores import Weaviate

# Dans ingest_docs()
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
    startup_period=None,
)
vectorstore = Weaviate(
    client=client,
    index_name=WEAVIATE_DOCS_INDEX_NAME,
    text_key="text",
    embedding=embedding,
    by_text=False,
    attributes=["source", "title"],
)
```

##### Après (Weaviate v4)
```python
import weaviate
import weaviate.classes as wvc
from langchain_weaviate.vectorstores import WeaviateVectorStore

# Dans ingest_docs()
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
)

vectorstore = WeaviateVectorStore(
    client=client,
    index_name=WEAVIATE_DOCS_INDEX_NAME,
    text_key="text",
    embedding=embedding,
)
```

**Notes importantes**:
- Weaviate v4 utilise `connect_to_weaviate_cloud()` au lieu de `Client()`
- L'authentification utilise `wvc.init.Auth.api_key()` au lieu de `AuthApiKey`
- `WeaviateVectorStore` remplace `Weaviate` de langchain_community
- Les paramètres `by_text` et `attributes` sont gérés différemment (vérifier docs)

#### 3.2 Migration de `backend/chain.py`

**Changements requis** (lignes 5, 12, 129-142):

##### Avant (Weaviate v3)
```python
import weaviate
from langchain_community.vectorstores import Weaviate

def get_retriever() -> BaseRetriever:
    weaviate_client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
    )
    weaviate_client = Weaviate(
        client=weaviate_client,
        index_name=WEAVIATE_DOCS_INDEX_NAME,
        text_key="text",
        embedding=get_embeddings_model(),
        by_text=False,
        attributes=["source", "title"],
    )
    return weaviate_client.as_retriever(search_kwargs=dict(k=6))
```

##### Après (Weaviate v4)
```python
import weaviate
import weaviate.classes as wvc
from langchain_weaviate.vectorstores import WeaviateVectorStore

def get_retriever() -> BaseRetriever:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
    )

    vectorstore = WeaviateVectorStore(
        client=client,
        index_name=WEAVIATE_DOCS_INDEX_NAME,
        text_key="text",
        embedding=get_embeddings_model(),
    )

    return vectorstore.as_retriever(search_kwargs=dict(k=6))
```

#### 3.3 Gestion de la connexion Weaviate

**Important**: Weaviate v4 nécessite une gestion explicite du cycle de vie de la connexion.

Options:
1. **Utiliser un context manager** (recommandé pour scripts)
2. **Fermer explicitement** avec `client.close()`
3. **Singleton pattern** pour réutiliser la connexion

Pour `chain.py`, envisager un singleton:
```python
_weaviate_client = None

def get_weaviate_client():
    global _weaviate_client
    if _weaviate_client is None:
        _weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
        )
    return _weaviate_client
```

---

### Phase 4 : Migration Manuelle - Pydantic v2 (10 min)

#### 4.1 Migration de `backend/main.py`

**Classes à migrer** (lignes 36-42, 57-60, 97-98):

##### Avant (Pydantic v1)
```python
from pydantic import BaseModel

class SendFeedbackBody(BaseModel):
    run_id: UUID
    key: str = "user_score"
    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None
```

##### Après (Pydantic v2)
```python
from pydantic import BaseModel, ConfigDict

class SendFeedbackBody(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: UUID
    key: str = "user_score"
    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None
```

**Notes**:
- Pour ces modèles simples, le changement est minimal
- `ConfigDict` remplace `class Config` si besoin de configuration
- Les types standards (UUID, str, etc.) fonctionnent sans changement

#### 4.2 Migration de `backend/chain.py`

**Classe à migrer** (lignes 124-126):

##### Avant
```python
from langchain_core.pydantic_v1 import BaseModel

class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]]
```

##### Après
```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = None
```

**Note**: Ajouter une valeur par défaut `= None` pour les champs optionnels (best practice Pydantic v2)

---

### Phase 5 : Tests et Validation (20-30 min)

#### 5.1 Test de l'ingestion

```bash
# Charger les variables d'environnement
source setup_env.sh

# Tester l'ingestion (temps estimé: 10-15 min)
poetry run python backend/ingest.py
```

**Points de validation**:
- ✅ Connexion à Weaviate Cloud réussie
- ✅ Création du schéma/collection
- ✅ Documents chargés (LangChain docs, API docs, LangSmith docs)
- ✅ Documents splitté et vectorisés
- ✅ Index créé dans Weaviate
- ✅ Record manager PostgreSQL fonctionnel

**Logs attendus**:
```
INFO:root:Loaded XXXX docs from documentation
INFO:root:Loaded XXXX docs from API
INFO:root:Loaded XXXX docs from Langsmith
```

#### 5.2 Vérification Weaviate

Vérifier dans le dashboard Weaviate Cloud:
- Collection créée avec le bon nom (`langchain` ou valeur de `WEAVIATE_INDEX_NAME`)
- Nombre d'objets correspondant aux documents ingérés
- Schéma correct avec les propriétés `text`, `source`, `title`

#### 5.3 Test du backend

```bash
# Démarrer le serveur
poetry run uvicorn --app-dir=backend main:app --reload --port 8080
```

#### 5.4 Test de l'API /chat

```bash
# Test simple
curl -X POST http://localhost:8080/chat/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "question": "What is LangChain?",
      "chat_history": []
    }
  }'
```

**Validation**:
- ✅ Requête acceptée (200 OK)
- ✅ Retrieval fonctionne (documents retournés)
- ✅ LLM génère une réponse
- ✅ Citations présentes
- ✅ Pas d'erreurs de connexion Weaviate

#### 5.5 Test de retrieval avancé

```bash
# Test avec historique de conversation
curl -X POST http://localhost:8080/chat/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "question": "How do I use it?",
      "chat_history": [
        {"role": "user", "content": "What is LCEL?"},
        {"role": "assistant", "content": "LCEL is LangChain Expression Language..."}
      ]
    }
  }'
```

---

### Phase 6 : Nettoyage et Documentation (10 min)

#### 6.1 Suppression du code mort

```python
# Dans ingest.py et chain.py
# Supprimer les imports inutilisés de l'ancien Weaviate
# Vérifier avec:
poetry run ruff check backend/
```

#### 6.2 Mise à jour de la documentation

Mettre à jour `CLAUDE.md`:
```markdown
## Known Issues & Solutions

### Weaviate Cloud Compatibility Issue - RÉSOLU (September 2025)

**Solution Implémentée:**
Migration complète vers LangChain 0.3 + Weaviate v4 + Pydantic v2

**Version actuelle:**
- langchain: 0.3.x
- weaviate-client: 4.17.x
- pydantic: 2.8.x
```

#### 6.3 Commit des changements

```bash
git add .
git commit -m "Migration vers LangChain 0.3 + Weaviate v4 + Pydantic v2

- Upgrade dependencies to latest stable versions
- Migrate Weaviate client v3 → v4 (ingest.py, chain.py)
- Migrate Pydantic v1 → v2 (main.py, chain.py)
- Update imports following LangChain 0.3 conventions
- Tested ingestion and chat endpoints successfully

Fixes Weaviate Cloud compatibility issue with new clusters.

For SawUp enterprise knowledge base and Claude Code MCP integration."
```

---

## Rollback Plan

### Si la migration échoue

#### Option 1 : Rollback Git (rapide)
```bash
git checkout langserve
git branch -D feature/langchain-v3-weaviate-v4-migration
```

#### Option 2 : Rollback des dépendances
```bash
git checkout pyproject.toml poetry.lock
poetry install
```

#### Option 3 : Utiliser Docker Weaviate local
Si Weaviate Cloud reste problématique:
```bash
# Démarrer Weaviate local (compatible v3)
docker run -d \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  semitechnologies/weaviate:1.23.7
```

Puis dans `.env`:
```bash
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Vide pour mode anonyme
```

---

## Risques Identifiés et Mitigations

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Conflits de dépendances | 🔴 Élevé | 🟡 Moyen | Test sur branche séparée, rollback possible |
| API Weaviate v4 différente | 🟡 Moyen | 🟢 Faible | Documentation officielle + exemples |
| Breaking changes Pydantic | 🟡 Moyen | 🟢 Faible | Modèles simples, peu de features avancées |
| Performance dégradée | 🟢 Faible | 🟢 Faible | Weaviate v4 plus rapide (gRPC) |
| Données perdues | 🔴 Élevé | 🟢 Faible | Réingestion possible, backup instructions |

---

## Timeline Estimée

| Phase | Durée | Critique |
|-------|-------|----------|
| 0. Préparation | 5 min | 🟢 |
| 1. Dépendances | 10-15 min | 🟡 |
| 2. langchain-cli | 5 min | 🟢 |
| 3. Weaviate v4 | 20-25 min | 🔴 |
| 4. Pydantic v2 | 10 min | 🟢 |
| 5. Tests | 20-30 min | 🔴 |
| 6. Nettoyage | 10 min | 🟢 |
| **TOTAL** | **80-95 min** | **~1h30** |

---

## Critères de Succès

### Must Have ✅
- [ ] Ingestion complète sans erreurs
- [ ] API `/chat/invoke` répond correctement
- [ ] Retrieval retourne des documents pertinents
- [ ] LLM génère des réponses avec citations
- [ ] Connexion Weaviate Cloud stable

### Should Have ✅
- [ ] Performance égale ou meilleure qu'avant
- [ ] Code lint sans warnings (ruff)
- [ ] Documentation mise à jour
- [ ] Commit propre avec message descriptif

### Nice to Have 🎯
- [ ] Tests automatisés passent
- [ ] Métriques de performance documentées
- [ ] Guide de migration pour futurs projets

---

## Références

### Documentation Officielle
- [LangChain v0.3 Migration Guide](https://python.langchain.com/docs/versions/v0_3/)
- [Weaviate Python Client v4](https://weaviate.io/developers/weaviate/client-libraries/python)
- [Weaviate v3 to v4 Migration](https://weaviate.io/developers/weaviate/client-libraries/python/v3_v4_migration)
- [Pydantic v2 Migration](https://docs.pydantic.dev/latest/migration/)
- [LangChain Weaviate Integration](https://python.langchain.com/docs/integrations/vectorstores/weaviate/)

### Ressources Internes
- `CLAUDE.md` - Documentation du projet
- `RUN_LOCALLY.md` - Guide d'exécution locale
- `.env.gcp.yaml.example` - Template de configuration

---

## Notes de Maintenance

### Post-Migration
- Surveiller les logs pour détecter les warnings de dépréciation
- Planifier migration vers LangChain 0.4+ quand disponible
- Considérer LangGraph pour features avancées (multi-agent)
- Évaluer migration de Supabase vers solution auto-hébergée

### Pour SawUp
- **MCP Integration** : À planifier après migration réussie
- **Custom Frontend** : Peut utiliser les mêmes endpoints `/chat/invoke`
- **Enterprise Features** : Authentification, rate limiting, logging à ajouter

---

**Document maintenu par**: Claude + Stéphane (SawUp)
**Dernière mise à jour**: 30 septembre 2025
**Version**: 1.0