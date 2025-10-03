# Observabilité sans LangSmith : Alternatives Open-Source

**Date**: 30 septembre 2025
**Contexte**: Investigation des alternatives d'observabilité pour déploiement self-hosted de Chat LangChain (branche master)

## Résumé Exécutif

**Question centrale**: Sommes-nous dépendants de LangSmith pour l'observabilité des applications LangChain/LangGraph ?

**Réponse**: ❌ NON - Plusieurs alternatives open-source matures existent avec support natif LangChain/LangGraph.

**Recommandation pour SawUp**:
- **Option A (Recommandée)**: **Langfuse** - Mature, Docker Compose ready, intégration native LangChain
- **Option B**: **Phoenix (Arize)** - Excellent pour cas d'usage RAG/expérimental
- **Option C**: **Helicone** - Gateway approach, caching inclus

**Effort d'intégration**: 1-2 heures (modifications minimales du code master)

---

## 1. Analyse de Dépendance LangSmith

### 1.1 Dépendances Actuelles (Branche Master)

```python
# backend/retrieval_graph/graph.py
# Aucun import de langsmith dans le code principal

# Les callbacks LangSmith sont optionnels via configuration:
from langchain_core.runnables import RunnableConfig

# LangSmith activé uniquement si LANGSMITH_API_KEY présent
# Pas de hard dependency dans le code
```

**Verdict**: ✅ **Dépendance OPTIONNELLE** - Le code fonctionne sans LangSmith, tracing désactivé simplement.

### 1.2 Limitations LangSmith

| Aspect | LangSmith Cloud | LangSmith Self-Hosted |
|--------|-----------------|----------------------|
| **Licence** | Propriétaire | Propriétaire |
| **Coût** | Gratuit (5k traces/mois) puis payant | Enterprise license (payant) |
| **Code source** | ❌ Fermé | ❌ Fermé |
| **Self-hosting** | N/A | ⚠️ Requires Enterprise license |
| **Vendor lock-in** | ⚠️ Élevé | ⚠️ Élevé |

---

## 2. Alternatives Open-Source

### 2.1 Langfuse ⭐ (Recommandé)

**Site**: https://langfuse.com
**GitHub**: https://github.com/langfuse/langfuse
**Licence**: Apache 2.0 (MIT pour SDK)

#### Caractéristiques

| Feature | Support |
|---------|---------|
| **Tracing LangChain** | ✅ Natif via `langfuse-langchain` package |
| **Tracing LangGraph** | ✅ Natif via callback handlers |
| **Self-hosting** | ✅ Docker Compose officiel |
| **Prompt Management** | ✅ Versioning, A/B testing |
| **Evaluations** | ✅ LLM-as-judge, datasets |
| **Analytics** | ✅ Dashboards, coûts, latence |
| **API** | ✅ REST API complète |
| **UI** | ✅ Interface web moderne |

#### Intégration avec Master Branch

**Installation**:
```bash
pip install langfuse langfuse-langchain
```

**Modification minimale** (`backend/retrieval_graph/graph.py`):
```python
from langfuse.callback import CallbackHandler

# Ajouter au début de la fonction de compilation du graph
def create_graph():
    # Configuration Langfuse (optionnelle, comme LangSmith)
    langfuse_handler = None
    if os.environ.get("LANGFUSE_PUBLIC_KEY"):
        langfuse_handler = CallbackHandler(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
        )

    # Le graph reste identique, callbacks passés via config
    graph = StateGraph(AgentState, config_schema=AgentConfiguration)
    # ... reste du code inchangé

    return graph.compile(callbacks=[langfuse_handler] if langfuse_handler else [])
```

**Docker Compose** (ajout au `docker-compose.yml`):
```yaml
services:
  langfuse-db:
    image: postgres:16
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    volumes:
      - langfuse-db:/var/lib/postgresql/data

  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
      NEXTAUTH_SECRET: changeme-32-character-secret-key
      NEXTAUTH_URL: http://localhost:3000
      SALT: changeme-salt
    depends_on:
      - langfuse-db

volumes:
  langfuse-db:
```

**Effort d'intégration**: ⏱️ **1-2 heures**

#### Avantages
- ✅ Support natif LangChain/LangGraph (maintenu par Langfuse team)
- ✅ Docker Compose officiel (production-ready)
- ✅ UI moderne et intuitive
- ✅ Features complètes (tracing + evaluation + prompt management)
- ✅ Licence permissive (Apache 2.0)
- ✅ Documentation exhaustive

#### Inconvénients
- ⚠️ Nécessite PostgreSQL additionnel (comme master branch)
- ⚠️ Courbe d'apprentissage UI (mais intuitive)

---

### 2.2 Phoenix (Arize AI)

**Site**: https://phoenix.arize.com
**GitHub**: https://github.com/Arize-ai/phoenix
**Licence**: Elastic License 2.0 (ELv2)

#### Caractéristiques

| Feature | Support |
|---------|---------|
| **Tracing LangChain** | ✅ Via OpenTelemetry instrumentation |
| **Tracing LangGraph** | ✅ Via OpenTelemetry instrumentation |
| **Self-hosting** | ✅ Docker, simple standalone |
| **Hallucination Detection** | ✅ Built-in RAG evaluation |
| **Embeddings Analysis** | ✅ UMAP visualization |
| **LLM Evals** | ✅ Factuality, toxicity, relevance |
| **OpenTelemetry** | ✅ Standard protocol |
| **UI** | ✅ Focus on experimentation |

#### Intégration avec Master Branch

**Installation**:
```bash
pip install arize-phoenix openinference-instrumentation-langchain
```

**Modification** (`backend/retrieval_graph/graph.py`):
```python
from openinference.instrumentation.langchain import LangChainInstrumentor
import phoenix as px

# Au démarrage de l'application
if os.environ.get("PHOENIX_ENABLED"):
    # Lancer Phoenix en mode embedded OU se connecter à instance externe
    session = px.launch_app() if os.environ.get("PHOENIX_EMBEDDED") else None

    # Instrumenter automatiquement toutes les chaînes LangChain
    LangChainInstrumentor().instrument()

    # Configuration OpenTelemetry endpoint
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = os.environ.get(
        "PHOENIX_COLLECTOR_ENDPOINT",
        "http://localhost:6006"
    )
```

**Docker Compose**:
```yaml
services:
  phoenix:
    image: arizephoenix/phoenix:latest
    ports:
      - "6006:6006"  # UI
      - "4317:4317"  # gRPC collector
      - "4318:4318"  # HTTP collector
    environment:
      PHOENIX_SQL_DATABASE_URL: sqlite:////data/phoenix.db
    volumes:
      - phoenix-data:/data

volumes:
  phoenix-data:
```

**Effort d'intégration**: ⏱️ **30 minutes - 1 heure**

#### Avantages
- ✅ Setup ultra-simple (instrumentation automatique)
- ✅ Excellent pour RAG evaluation (hallucination detection)
- ✅ OpenTelemetry standard (interopérabilité)
- ✅ Mode embedded possible (no external service)
- ✅ Visualizations avancées (embeddings UMAP)

#### Inconvénients
- ⚠️ Licence ELv2 (pas pure open-source comme Apache 2.0)
- ⚠️ UI orientée expérimentation (moins "production dashboard")
- ⚠️ Documentation LangGraph moins exhaustive que Langfuse

---

### 2.3 Helicone

**Site**: https://helicone.ai
**GitHub**: https://github.com/Helicone/helicone
**Licence**: Apache 2.0

#### Caractéristiques

| Feature | Support |
|---------|---------|
| **Architecture** | Gateway/Proxy LLM |
| **Tracing LangChain** | ✅ Via proxy ou async logging |
| **Self-hosting** | ✅ Docker disponible |
| **Caching** | ✅ Built-in (économies API) |
| **Rate Limiting** | ✅ Built-in |
| **Threat Detection** | ✅ Prompt injection detection |
| **Multi-provider** | ✅ OpenAI, Anthropic, etc. |

#### Approche Architecture

**Différence clé**: Helicone = **Gateway** entre app et LLM providers (intercepte requêtes).

```
Application → Helicone Proxy → OpenAI/Anthropic
                ↓
            Logs/Cache/Analytics
```

**Intégration** (approche proxy):
```python
# Modifier configuration LLM pour passer par Helicone proxy
import os
from langchain_openai import ChatOpenAI

# Au lieu de:
# model = ChatOpenAI(model="gpt-4")

# Utiliser:
model = ChatOpenAI(
    model="gpt-4",
    openai_api_base="https://oai.helicone.ai/v1",  # ou instance self-hosted
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ['HELICONE_API_KEY']}"
    }
)
```

**Docker Compose**:
```yaml
services:
  helicone:
    image: helicone/helicone:latest
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://helicone:helicone@helicone-db:5432/helicone
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    depends_on:
      - helicone-db

  helicone-db:
    image: postgres:16
    environment:
      POSTGRES_USER: helicone
      POSTGRES_PASSWORD: helicone
      POSTGRES_DB: helicone
    volumes:
      - helicone-db:/var/lib/postgresql/data

volumes:
  helicone-db:
```

**Effort d'intégration**: ⏱️ **2-3 heures** (refactor config LLM partout)

#### Avantages
- ✅ Caching built-in (économies coûts API)
- ✅ Rate limiting / threat detection
- ✅ Licence Apache 2.0
- ✅ Support multi-providers (OpenAI, Anthropic, etc.)

#### Inconvénients
- ⚠️ Architecture gateway = point de passage obligatoire
- ⚠️ Nécessite refactor de toutes les instanciations LLM
- ⚠️ Latence additionnelle (proxy)
- ⚠️ Setup plus complexe (Supabase dépendance)

---

### 2.4 OpenLLMetry (Traceloop)

**Site**: https://traceloop.com/openllmetry
**GitHub**: https://github.com/traceloop/openllmetry
**Licence**: Apache 2.0

#### Caractéristiques

**Approche**: Framework d'instrumentation OpenTelemetry, pas de backend propre.

| Feature | Support |
|---------|---------|
| **Tracing LangChain** | ✅ Auto-instrumentation |
| **Tracing LangGraph** | ✅ Auto-instrumentation |
| **Backend agnostic** | ✅ Envoie vers n'importe quel backend OpenTelemetry |
| **Multi-framework** | ✅ LangChain, LlamaIndex, OpenAI SDK, etc. |

#### Intégration

```python
from traceloop.sdk import Traceloop

# Initialiser au démarrage
Traceloop.init(
    app_name="chat-langchain",
    api_endpoint="http://localhost:4318",  # Endpoint OpenTelemetry (ex: Jaeger)
    disable_batch=False
)

# Auto-instrumentation de toutes les bibliothèques supportées
# Aucune autre modification nécessaire
```

**Backends compatibles**:
- Jaeger (open-source tracing)
- Grafana Tempo
- Zipkin
- Datadog
- New Relic
- Etc.

**Effort d'intégration**: ⏱️ **30 minutes** (+ setup backend OpenTelemetry)

#### Avantages
- ✅ Auto-instrumentation (zero code change après init)
- ✅ Standard OpenTelemetry (portabilité)
- ✅ Choix libre du backend

#### Inconvénients
- ⚠️ Pas de backend propre (nécessite Jaeger/Tempo/etc.)
- ⚠️ UI dépend du backend choisi
- ⚠️ Features LLM-specific limitées (pas de prompt management)

---

## 3. Comparaison Matricielle

### 3.1 Features

| Feature | LangSmith Cloud | Langfuse | Phoenix | Helicone | OpenLLMetry |
|---------|-----------------|----------|---------|----------|-------------|
| **Licence** | Propriétaire | Apache 2.0 | ELv2 | Apache 2.0 | Apache 2.0 |
| **Self-hosting gratuit** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Tracing LangChain** | ✅ | ✅ Natif | ✅ OpenTelemetry | ✅ Proxy | ✅ Auto |
| **Tracing LangGraph** | ✅ | ✅ Natif | ✅ OpenTelemetry | ⚠️ Partiel | ✅ Auto |
| **Prompt Management** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Evaluations** | ✅ | ✅ | ✅ | ⚠️ Basic | ❌ |
| **Datasets** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Caching** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Analytics UI** | ✅ | ✅ | ✅ | ✅ | Backend-dependent |
| **Cost Tracking** | ✅ | ✅ | ✅ | ✅ | Backend-dependent |
| **OpenTelemetry** | ❌ | ⚠️ Partiel | ✅ | ❌ | ✅ |

### 3.2 Effort d'Intégration

| Solution | Code Changes | Infrastructure | Setup Time | Maintenance |
|----------|--------------|----------------|------------|-------------|
| **LangSmith** | Minimal (déjà présent) | Cloud (gratuit 5k) | 5 min | Bas |
| **Langfuse** | Minimal (1 fichier) | +PostgreSQL | 1-2h | Bas |
| **Phoenix** | Minimal (1 fichier) | +Service léger | 30-60 min | Bas |
| **Helicone** | Moyen (refactor LLM) | +PostgreSQL+Supabase | 2-3h | Moyen |
| **OpenLLMetry** | Minimal (init) | +Backend OpenTelemetry | 1-2h | Moyen |

### 3.3 Cas d'Usage

| Objectif | Meilleure Solution |
|----------|-------------------|
| **Remplacement 1:1 LangSmith** | Langfuse ⭐ |
| **RAG/Embeddings Analysis** | Phoenix ⭐ |
| **Cost optimization (caching)** | Helicone ⭐ |
| **Standard OpenTelemetry** | Phoenix ou OpenLLMetry ⭐ |
| **Experimentation rapide** | Phoenix (mode embedded) ⭐ |
| **Production self-hosted** | Langfuse ⭐ |

---

## 4. Recommandation pour SawUp

### 4.1 Contexte SawUp

**Objectif 1**: Chatbot ultra-performant LangChain/LangGraph via MCP
**Objectif 2**: PoC base de connaissances enterprise
**Contrainte**: Self-hosting préféré (maîtrise données)

### 4.2 Recommandation Primaire: **Langfuse**

**Justification**:
1. ✅ **Remplacement 1:1 LangSmith** - Features équivalentes
2. ✅ **Support natif LangChain/LangGraph** - Intégration maintenue
3. ✅ **Production-ready** - Docker Compose officiel
4. ✅ **Licence permissive** - Apache 2.0
5. ✅ **Prompt management** - Utile pour objectif 1 (itération prompts MCP)
6. ✅ **Evaluations** - Utile pour objectif 2 (qualité réponses enterprise)
7. ✅ **Coût** - Gratuit, self-hosted
8. ✅ **Effort** - 1-2h d'intégration

**Architecture suggérée**:
```
┌─────────────────────────────────────────────────┐
│ Master Branch (Self-Hosted)                    │
│ ┌─────────────────────────────────────────────┐ │
│ │ LangGraph Application                       │ │
│ │   ├─ Retrieval Graph                        │ │
│ │   ├─ Researcher Sub-graph                   │ │
│ │   └─ Callbacks → Langfuse Handler           │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────┐  ┌──────────┐  ┌─────────────┐ │
│ │ PostgreSQL  │  │  Redis   │  │  Weaviate   │ │
│ │ (State)     │  │ (Queue)  │  │  (Vectors)  │ │
│ └─────────────┘  └──────────┘  └─────────────┘ │
└─────────────────────────────────────────────────┘
                      ↓ Traces
┌─────────────────────────────────────────────────┐
│ Langfuse (Self-Hosted)                          │
│ ┌─────────────────────────────────────────────┐ │
│ │ UI (localhost:3000)                         │ │
│ │   ├─ Tracing Dashboard                      │ │
│ │   ├─ Prompt Management                      │ │
│ │   ├─ Evaluations                            │ │
│ │   └─ Analytics                              │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ PostgreSQL (Langfuse)                       │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 4.3 Alternative Complémentaire: **Phoenix**

**Usage suggéré**: Analyse RAG spécifique (en complément Langfuse)

**Justification**:
- ✅ Hallucination detection (objectif 2 - qualité réponses)
- ✅ Embeddings visualization (debug retrieval)
- ✅ Mode embedded (no infrastructure)
- ✅ OpenTelemetry (portabilité)

**Approche hybride possible**:
```python
# backend/retrieval_graph/graph.py
from langfuse.callback import CallbackHandler
from openinference.instrumentation.langchain import LangChainInstrumentor

# Langfuse pour production tracing
langfuse_handler = CallbackHandler(...)

# Phoenix pour RAG debugging (mode embedded, on-demand)
if os.environ.get("PHOENIX_DEBUG"):
    import phoenix as px
    px.launch_app()
    LangChainInstrumentor().instrument()

# Utiliser les deux simultanément
callbacks = [langfuse_handler]
```

---

## 5. Plan d'Implémentation

### Phase 1: Setup Langfuse (1-2h)

**Étape 1.1**: Ajouter Langfuse au `docker-compose.yml`
```bash
# Copier config de section 2.1
# Adapter secrets (NEXTAUTH_SECRET, SALT)
```

**Étape 1.2**: Installer dépendances Python
```bash
poetry add langfuse langfuse-langchain
```

**Étape 1.3**: Modifier `backend/retrieval_graph/graph.py`
```python
# Ajouter import et handler (voir section 2.1)
# Tester avec trace simple
```

**Étape 1.4**: Lancer stack et vérifier
```bash
docker compose up -d
# Accéder http://localhost:3000
# Créer projet "chat-langchain"
# Copier public/secret keys dans .env
```

**Étape 1.5**: Tester tracing end-to-end
```bash
# Faire query au chatbot
# Vérifier trace apparaît dans Langfuse UI
```

### Phase 2: Validation Production (2-4h)

**Étape 2.1**: Tester scénarios complexes
- Multi-step research queries
- Streaming responses
- Error handling

**Étape 2.2**: Configurer évaluations
- Créer dataset de test queries
- Définir critères qualité (relevance, factuality)
- Lancer évaluations automatiques

**Étape 2.3**: Documentation
- Ajouter section Langfuse à CLAUDE.md
- Documenter procédure setup
- Créer guide debug avec Langfuse

### Phase 3 (Optionnel): Ajout Phoenix (30-60 min)

**Étape 3.1**: Setup Phoenix pour debug RAG
```bash
poetry add arize-phoenix openinference-instrumentation-langchain
# Ajouter service Phoenix au docker-compose.yml
```

**Étape 3.2**: Instrumentation mode debug
```python
# Activer uniquement si PHOENIX_DEBUG=true
# Tester hallucination detection sur queries ambiguës
```

---

## 6. Conclusion

### État des Lieux Observabilité

**Question**: Sommes-nous dépendants de LangSmith/LangGraph Cloud ?

**Réponse définitive**: ❌ **NON**

**Preuves**:
1. ✅ **Code master** - Aucune dépendance hard à LangSmith
2. ✅ **Alternatives matures** - 4+ solutions open-source production-ready
3. ✅ **Intégration simple** - 1-2h d'effort pour remplacement 1:1
4. ✅ **Features équivalentes** - Tracing, evaluations, prompt management disponibles
5. ✅ **Self-hosting gratuit** - Pas de license fees contrairement LangSmith Enterprise

### Sélection pour SawUp

**Recommandation finale**: **Langfuse** comme solution principale

**Ratio bénéfice/effort**: ⭐⭐⭐⭐⭐ (5/5)
- Effort: 1-2 heures
- Qualité: Production-ready
- Features: Équivalent LangSmith
- Coût: Gratuit (self-hosted)
- Maintenance: Faible (Docker Compose)

**Prochaines étapes**:
1. ✅ Documentation complétée (ce fichier)
2. ⏭️ Implémenter Phase 1 (setup Langfuse)
3. ⏭️ Valider tracing avec queries complexes
4. ⏭️ Intégrer à workflow de développement SawUp

---

**Authorship**: Document généré par Claude Code, orchestré par Stéphane Wootha Richard (stephane@sawup.fr)