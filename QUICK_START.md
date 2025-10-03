# Quick Start - MCP Server pour Claude Desktop

Ce guide vous permet de démarrer le serveur MCP LangChain Expert en 15 minutes.

---

## Prérequis (5 min)

### Logiciels Requis
- **Docker Desktop** - [Télécharger](https://www.docker.com/products/docker-desktop)
- **Python 3.11+** - Vérifier: `python3 --version`
- **Poetry** - Installer: `curl -sSL https://install.python-poetry.org | python3 -`
- **Claude Desktop** - [Télécharger](https://claude.ai/download)

### Clés API Requises
- **OpenAI API Key** - Pour embeddings et LLM ([obtenir ici](https://platform.openai.com/api-keys))
- **LangSmith API Key** (optionnel) - Pour tracing ([obtenir ici](https://smith.langchain.com))

---

## Installation Rapide (10 min)

### 1. Infrastructure Docker (2 min)

Démarrer PostgreSQL, Weaviate et Redis :

```bash
docker compose up -d
```

Vérifier que les 3 conteneurs tournent :
```bash
docker ps
# Doit afficher: postgres, weaviate, redis
```

### 2. Configuration Environment (1 min)

Copier le template et éditer avec vos clés :

```bash
cp .env.example .env
# Éditer .env avec votre éditeur
```

**Variables essentielles dans `.env` :**
```bash
# OpenAI (REQUIS)
OPENAI_API_KEY=sk-proj-...

# Weaviate (local Docker)
WEAVIATE_URL=http://localhost:8088

# PostgreSQL (local Docker)
POSTGRES_CONNECTION_STRING=postgresql://postgres:password@localhost:5432/chat_langchain

# LangSmith (OPTIONNEL - free tier 5k traces/mois)
LANGSMITH_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
```

### 3. Installation Dependencies (2 min)

```bash
poetry install
```

### 4. Ingestion Documentation (30-60 min - à faire 1x)

Cette étape indexe toute la documentation LangChain :

```bash
PYTHONPATH=. poetry run python backend/ingest.py
```

**Progression attendue :**
```
Indexing LangChain documentation...
✓ Fetched 1,200+ pages
✓ Split into 15,061 chunks
✓ Created embeddings (OpenAI text-embedding-3-small)
✓ Stored in Weaviate
✓ Updated Record Manager (PostgreSQL)
Done! 15,061 documents indexed
```

> **Note:** Cette étape prend 30-60 min mais ne se fait qu'une fois. Les runs suivants seront incrémentaux (seulement nouveaux docs).

### 5. Démarrer LangGraph Server (1 min)

Terminal dédié pour le serveur :

```bash
langgraph dev --no-browser --port 2024
```

**Succès si vous voyez :**
```
✓ Compiled graph successfully
✓ Server running on http://localhost:2024
✓ Endpoints: /threads, /runs/stream, /state
```

> **Important:** Garder ce terminal ouvert pendant l'utilisation du MCP.

### 6. Configuration Claude Desktop (2 min)

Éditer le fichier de configuration :

**macOS:**
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Ajouter cette configuration :**
```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/VOTRE_USER/Documents/work/chat-langchain/mcp_server",
        "run",
        "langchain_expert.py"
      ]
    }
  }
}
```

> **Remplacer** `/Users/VOTRE_USER/` par votre chemin absolu réel.

### 7. Redémarrer Claude Desktop (30 sec)

```bash
# macOS: Cmd+Q pour quitter
# Puis relancer Claude Desktop
```

---

## Vérification Installation

### Test 1: Vérifier Status MCP

Dans Claude Desktop, taper :
```
Check LangChain expert status
```

**Réponse attendue :**
```
✅ LangGraph Server: Connected (http://localhost:2024)
✅ Documents indexed: 15,061
✅ Models available: GPT-5 mini (default), Claude Sonnet 4.5, DeepSeek, Llama 3.3 70B
✅ Weaviate: Connected (15,061 vectors)
✅ PostgreSQL: Connected (checkpoints + record manager)
```

### Test 2: Question Simple

```
I need to save conversation history to PostgreSQL. Which class should I use?
```

**Réponse attendue :**
```
Based on the documentation, you should use PostgresChatMessageHistory...
[réponse avec citations et code examples]
```

### Test 3: Question Complexe

```
How do I build a research assistant that breaks down complex questions into sub-questions, searches for each, and synthesizes findings?
```

**Réponse attendue :**
```
Based on the documentation, here's how to structure your research assistant using LangGraph:
[architecture complète avec code TypeScript/Python]
```

---

## Utilisation Quotidienne

### Démarrage Rapide (après installation initiale)

```bash
# 1. Démarrer infrastructure (si arrêtée)
docker compose up -d

# 2. Démarrer LangGraph server
langgraph dev --no-browser --port 2024

# 3. Lancer Claude Desktop
```

### Arrêt Propre

```bash
# 1. Arrêter LangGraph (Ctrl+C dans terminal)

# 2. Arrêter infrastructure (optionnel)
docker compose down
```

---

## Commandes Utiles

### Mise à Jour Documentation

Pour re-indexer (nouveaux docs LangChain) :

```bash
FORCE_UPDATE=true PYTHONPATH=. poetry run python backend/ingest.py
```

### Vérifier Infrastructure

```bash
# Vérifier Docker containers
docker ps

# Vérifier PostgreSQL
docker exec -it postgres psql -U postgres -d chat_langchain -c "SELECT COUNT(*) FROM langchain_pg_collection;"

# Vérifier Weaviate
curl http://localhost:8088/v1/meta
```

### Logs Debugging

```bash
# Logs LangGraph server (si problèmes)
# Visible dans le terminal où vous avez lancé 'langgraph dev'

# Logs Docker
docker logs postgres
docker logs weaviate
docker logs redis
```

---

## Modèles Disponibles

Le MCP server supporte plusieurs modèles LLM :

| Modèle | Usage | Vitesse | Qualité |
|--------|-------|---------|---------|
| **GPT-5 mini** | Default (upstream) | 60s | 4/5 |
| Claude Sonnet 4.5 | HERO (recommandé) | 35s | 5/5 ⭐ |
| Llama 3.3 70B (Groq) | PRAGMATIC ultra-rapide | 9s | 4.6/5 |
| DeepSeek Chat | Économique | 45s | 4.4/5 |

> **Recommandation:** Configurer Sonnet 4.5 comme default pour qualité maximale (5/5). Qualité supérieure justifie le délai (voir [docs/research/benchmarks/ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md](./docs/research/benchmarks/ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md)). Configuration par défaut upstream utilise GPT-5 mini.

---

## Prochaines Étapes

✅ **Installation terminée !**

- 📚 **Documentation complète:** Voir [CLAUDE.md](./CLAUDE.md)
- 🔧 **Troubleshooting:** Voir [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- 🏗️ **Architecture:** Voir [docs/upstream/CONCEPTS.md](./docs/upstream/CONCEPTS.md)
- 🎯 **Personnalisation:** Voir [docs/upstream/MODIFY.md](./docs/upstream/MODIFY.md)

### Questions Fréquentes

**Q: Le serveur MCP ne répond pas ?**
→ Vérifier que `langgraph dev` tourne sur port 2024

**Q: "404 Not Found /invoke" ?**
→ Vous utilisez le mauvais pattern API, voir [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#problème-404-not-found-invoke)

**Q: Réponses lentes (> 60s) ?**
→ Normal pour questions complexes avec Sonnet 4.5. Utiliser Llama 3.3 70B si vitesse critique.

**Q: Hallucinations détectées ?**
→ Wrappers PNL anti-hallucination actifs par défaut (voir [docs/mcp_development/DOCUMENTATION_WRAPPERS_PNL.md](./docs/mcp_development/DOCUMENTATION_WRAPPERS_PNL.md))

---

## Support

- **Issues GitHub:** [chat-langchain/issues](https://github.com/langchain-ai/chat-langchain/issues)
- **Documentation officielle:** [python.langchain.com](https://python.langchain.com)
- **LangGraph docs:** [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph)
