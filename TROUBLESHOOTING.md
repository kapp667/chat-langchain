# Troubleshooting - MCP Server LangChain Expert

Ce guide résout les problèmes courants rencontrés lors de l'installation et l'utilisation du MCP server LangChain Expert.

---

## Table des Matières

1. [Problèmes d'Installation](#problèmes-dinstallation)
2. [Problèmes de Connexion](#problèmes-de-connexion)
3. [Problèmes de Performance](#problèmes-de-performance)
4. [Problèmes de Qualité](#problèmes-de-qualité)
5. [Problèmes d'Infrastructure](#problèmes-dinfrastructure)
6. [Debugging Avancé](#debugging-avancé)

---

## Problèmes d'Installation

### Erreur: `command not found: langgraph`

**Symptômes:**
```bash
$ langgraph dev
zsh: command not found: langgraph
```

**Cause:** LangGraph CLI n'est pas installé ou pas dans le PATH.

**Solution:**
```bash
# Installer LangGraph CLI
pip install langgraph-cli

# Vérifier installation
langgraph --version
```

---

### Erreur: Python 3.9 au lieu de 3.11+

**Symptômes:**
```bash
$ langgraph dev
Error: Python 3.11 or higher is required
```

**Cause:** LangGraph 0.4.5+ nécessite Python 3.11 minimum.

**Solution:**
```bash
# Installer Python 3.11+ (macOS Homebrew)
brew install python@3.11

# Créer un nouvel environnement Poetry
poetry env use python3.11
poetry install
```

---

### Erreur: Dependencies conflicts (Pydantic, LangChain)

**Symptômes:**
```
ERROR: ResolutionImpossible
pydantic>=2.8.0 required but 1.10.x installed
```

**Cause:** Incompatibilité entre versions Pydantic v1 et v2.

**Solution:**
```bash
# Nettoyer environnement
poetry env remove python
rm poetry.lock

# Réinstaller avec contraintes
poetry install

# Si problème persiste, forcer Pydantic v2
poetry add pydantic@^2.9
```

---

## Problèmes de Connexion

### Problème: 404 Not Found `/invoke`

**Symptômes:**
```
httpx.HTTPStatusError: 404 Client Error: Not Found for url: http://localhost:2024/invoke
```

**Cause:** ❌ **Pattern API incorrect** - Endpoint `/invoke` n'existe pas dans LangGraph.

**Solution:** ✅ Utiliser LangGraph SDK avec le pattern `client.runs.stream()`

**Code INCORRECT (cause l'erreur 404):**
```python
import httpx

response = httpx.post(
    "http://localhost:2024/invoke",  # ❌ MAUVAIS endpoint
    json={"input": {"messages": [{"role": "user", "content": question}]}}
)
```

**Code CORRECT (fonctionne):**
```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

async for chunk in client.runs.stream(
    thread_id=None,
    assistant_id="agent",
    input={"messages": [{"role": "user", "content": question}]},
    stream_mode="updates"
):
    # Traiter chunks
    pass
```

**Référence complète:** Voir [CLAUDE.md - Issue 4](./CLAUDE.md#issue-4-api-404-not-found-invoke-blocker---september-2025)

---

### Problème: LangGraph Server non démarré

**Symptômes:**
```
Connection refused on http://localhost:2024
```

**Cause:** Le serveur `langgraph dev` n'est pas lancé.

**Solution:**
```bash
# Terminal dédié
langgraph dev --no-browser --port 2024

# Vérifier que le serveur tourne
curl http://localhost:2024/ok
# Doit retourner: {"ok": true}
```

**Vérifications:**
- Port 2024 n'est pas déjà utilisé: `lsof -i :2024`
- Graph compilé sans erreur (voir output terminal)
- PostgreSQL et Redis accessibles

---

### Problème: Claude Desktop ne voit pas le MCP server

**Symptômes:**
- Icône MCP n'apparaît pas dans Claude Desktop
- Commandes MCP ne retournent rien

**Cause:** Configuration `claude_desktop_config.json` incorrecte.

**Solution:**

1. **Vérifier le chemin du fichier de config:**
   ```bash
   # macOS
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Windows
   code %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Vérifier le chemin absolu du MCP server:**
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

   ⚠️ **Remplacer `/Users/VOTRE_USER/` par votre chemin absolu réel**

3. **Vérifier que `uv` est installé:**
   ```bash
   uv --version
   # Si erreur, installer: curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **Redémarrer Claude Desktop complètement:**
   - macOS: Cmd+Q puis relancer
   - Windows: Quitter depuis barre d'état système puis relancer

---

## Problèmes de Performance

### Problème: Réponses très lentes (> 60s)

**Symptômes:**
```
Question posée dans Claude Desktop
... 90 secondes d'attente ...
Réponse finalement reçue
```

**Causes possibles:**
1. Question ultra-complexe (normal pour HERO - Sonnet 4.5)
2. Timeout trop court dans le MCP server
3. Graph LangGraph avec trop de récursions

**Solutions:**

**Solution 1: Accepter la latence (HERO quality)**
- Sonnet 4.5 = 22-47s normal (voir benchmark)
- Qualité 5/5 justifie le délai
- Si vitesse critique, utiliser Llama 3.3 70B (8-10s, qualité 4.6/5)

**Solution 2: Augmenter timeout MCP**
```python
# mcp_server/langchain_expert.py
async for chunk in client.runs.stream(
    thread_id=None,
    assistant_id="agent",
    input={"messages": [...]},
    stream_mode="updates",
    config={"configurable": {"thread_id": str(uuid.uuid4())}},
    # Augmenter timeout
    timeout=180.0  # 3 minutes au lieu de 60s
):
    ...
```

**Solution 3: Augmenter récursion limit**
```python
# backend/retrieval_graph/graph.py
graph = builder.compile(
    checkpointer=PostgresSaver(connection_string),
    interrupt_before=[],
    interrupt_after=[],
    recursion_limit=50  # Augmenter de 25 (défaut) à 50
)
```

**Solution 4: Activer streaming progressif**
- Actuellement: MCP retourne réponse complète
- Futur: Streamer chunks au fur et à mesure (TODO)

---

### Problème: Timeout après 30s exactement

**Symptômes:**
```
Error: Request timed out after 30000ms
```

**Cause:** Timeout par défaut du client HTTP.

**Solution:**
```python
# mcp_server/langchain_expert.py
from langgraph_sdk import get_client
import httpx

# Créer client HTTP avec timeout augmenté
http_client = httpx.AsyncClient(timeout=120.0)  # 2 minutes

client = get_client(
    url="http://localhost:2024",
    http_client=http_client
)
```

---

## Problèmes de Qualité

### Problème: Hallucinations détectées dans les réponses

**Symptômes:**
- Réponses contenant des informations non vérifiables
- Citations vers des URLs inexistantes
- Code examples avec APIs qui n'existent pas

**Cause:** LLM génère du contenu plausible mais incorrect.

**Solution: Wrappers PNL anti-hallucination (DÉJÀ ACTIFS)**

Le système inclut des wrappers PNL (Programmation Neuro-Linguistique) qui réduisent les hallucinations:

**Pour Groq (Llama 3.3 70B):**
```python
# backend/groq_wrapper.py
PNL_ANTI_HALLUCINATION_PREFIX = """
Tu es un expert LangChain/LangGraph qui répond UNIQUEMENT avec des informations
vérifiables depuis les documents fournis.

RÈGLES ABSOLUES:
1. Cite TOUJOURS les sources avec [source](URL)
2. Si information absente des documents: dis "Je n'ai pas trouvé..."
3. JAMAIS inventer d'API, de classes, ou de méthodes
4. JAMAIS générer d'URLs fictives
...
"""
```

**Pour DeepSeek:**
```python
# backend/deepseek_wrapper.py
# Même pattern PNL
```

**Vérifier activation:**
```bash
# Vérifier que wrappers sont importés
grep -r "groq_wrapper" backend/
grep -r "deepseek_wrapper" backend/
```

**Référence complète:** [docs/mcp_development/DOCUMENTATION_WRAPPERS_PNL.md](./docs/mcp_development/DOCUMENTATION_WRAPPERS_PNL.md)

---

### Problème: Réponses de mauvaise qualité (vagues, incomplètes)

**Symptômes:**
- Réponses trop courtes (< 500 chars)
- Pas de code examples
- Pas de citations

**Cause possible:** Modèle PRAGMATIC (Llama 3.3 70B) au lieu de HERO (Sonnet 4.5).

**Solution: Vérifier configuration modèle**

```bash
# Vérifier backend/retrieval_graph/configuration.py
grep -A 5 "model_name" backend/retrieval_graph/configuration.py
```

**Doit contenir:**
```python
model_name: str = Field(
    default="anthropic/claude-sonnet-4-20250514",  # ✅ HERO
    # default="groq/llama-3.3-70b-versatile",      # ❌ PRAGMATIC
    ...
)
```

**Si besoin de changer:**
```python
# Option 1: Modifier configuration.py (permanent)
# Option 2: Passer via configurable au runtime (temporaire)
config = {
    "configurable": {
        "model_name": "anthropic/claude-sonnet-4-20250514"
    }
}
```

**Benchmark qualité:** Voir [ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md](./ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md)

---

## Problèmes d'Infrastructure

### Problème: PostgreSQL connexion refusée

**Symptômes:**
```
psycopg2.OperationalError: connection refused
FATAL: database "chat_langchain" does not exist
```

**Solution:**

**Vérifier Docker container:**
```bash
docker ps | grep postgres
# Doit afficher: postgres:16

# Si absent, démarrer infrastructure
docker compose up -d
```

**Vérifier database existe:**
```bash
docker exec -it postgres psql -U postgres -c "\l"
# Doit lister: chat_langchain

# Si absent, créer:
docker exec -it postgres psql -U postgres -c "CREATE DATABASE chat_langchain;"
```

**Vérifier connection string dans .env:**
```bash
grep POSTGRES .env
# Doit contenir:
# POSTGRES_CONNECTION_STRING=postgresql://postgres:password@localhost:5432/chat_langchain
```

---

### Problème: Weaviate connexion refusée

**Symptômes:**
```
weaviate.exceptions.WeaviateConnectionError: Cannot connect to Weaviate
```

**Solution:**

**Pour Weaviate Cloud:**
```bash
# Vérifier .env
grep WEAVIATE .env
# Doit contenir URL cluster (https://...)
# WEAVIATE_URL=https://your-cluster.weaviate.network
# WEAVIATE_API_KEY=your-key

# Tester connexion
curl -H "Authorization: Bearer YOUR_KEY" https://your-cluster.weaviate.network/v1/meta
```

**Pour Weaviate local Docker:**
```bash
# Vérifier container
docker ps | grep weaviate
# Doit afficher: weaviate:1.32

# Si absent, démarrer
docker compose up -d weaviate

# Tester connexion
curl http://localhost:8088/v1/meta
```

---

### Problème: Redis connexion refusée

**Symptômes:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Vérifier Docker container
docker ps | grep redis

# Si absent, démarrer
docker compose up -d redis

# Tester connexion
docker exec -it redis redis-cli ping
# Doit retourner: PONG
```

---

### Problème: Ingestion échoue (0 documents indexés)

**Symptômes:**
```bash
$ PYTHONPATH=. poetry run python backend/ingest.py
Indexing LangChain documentation...
✗ Failed: 0 documents indexed
```

**Causes possibles:**
1. Weaviate non accessible
2. OpenAI API key invalide
3. URLs documentation inaccessibles

**Solutions:**

**Vérifier OpenAI API key:**
```bash
grep OPENAI_API_KEY .env
# Doit commencer par: sk-proj-...

# Tester key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
# Doit retourner liste de modèles
```

**Vérifier Weaviate accessible:**
```bash
# Voir section Weaviate ci-dessus
```

**Relancer ingestion avec logs détaillés:**
```bash
PYTHONPATH=. poetry run python backend/ingest.py --verbose
```

**Forcer re-indexation complète:**
```bash
FORCE_UPDATE=true PYTHONPATH=. poetry run python backend/ingest.py
```

---

## Debugging Avancé

### Activer logs LangSmith (tracing)

**Configuration:**
```bash
# .env
LANGSMITH_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=chat-langchain-local
```

**Consulter traces:**
1. Aller sur https://smith.langchain.com
2. Sélectionner projet `chat-langchain-local`
3. Voir traces détaillées de chaque requête

**Désactiver tracing (si problème de performance):**
```bash
# .env
LANGCHAIN_TRACING_V2=false
```

---

### Logs détaillés LangGraph

**Activer logs debug:**
```bash
# Avant lancement
export LANGGRAPH_DEBUG=1

langgraph dev --no-browser --port 2024
```

**Voir état du graph:**
```bash
# Pendant exécution
curl http://localhost:2024/threads
curl http://localhost:2024/runs
```

---

### Inspecter état PostgreSQL (checkpoints)

```bash
# Nombre de checkpoints
docker exec -it postgres psql -U postgres -d chat_langchain -c \
  "SELECT COUNT(*) FROM checkpoints;"

# Derniers threads
docker exec -it postgres psql -U postgres -d chat_langchain -c \
  "SELECT thread_id, checkpoint_ns, created_at FROM checkpoints ORDER BY created_at DESC LIMIT 5;"
```

---

### Inspecter Weaviate (vectors)

```bash
# Nombre de documents
curl http://localhost:8088/v1/objects?class=LangChain_General_Guides_And_Tutorials | jq '.objects | length'

# Ou avec Weaviate Cloud:
curl -H "Authorization: Bearer YOUR_KEY" \
  https://your-cluster.weaviate.network/v1/objects?class=LangChain_General_Guides_And_Tutorials
```

---

## Support et Documentation

### Documentation Complète

- **Installation:** [QUICK_START.md](./QUICK_START.md)
- **Architecture:** [CLAUDE.md](./CLAUDE.md)
- **Wrappers PNL:** [docs/mcp_development/DOCUMENTATION_WRAPPERS_PNL.md](./docs/mcp_development/DOCUMENTATION_WRAPPERS_PNL.md)
- **Benchmark qualité:** [ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md](./ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md)

### Problème Non Résolu?

1. **Vérifier CLAUDE.md:** Section "Known Issues & Solutions"
2. **Consulter logs:**
   - Terminal `langgraph dev`: Erreurs backend
   - Claude Desktop: Developer Tools (Help → Toggle Developer Tools)
3. **GitHub Issues:** [chat-langchain/issues](https://github.com/langchain-ai/chat-langchain/issues)
4. **LangGraph Docs:** [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph)

---

## Checklist Diagnostic Rapide

Avant de créer un issue, vérifier:

- [ ] Docker containers tournent (`docker ps` montre postgres, weaviate, redis)
- [ ] LangGraph server lancé (`curl http://localhost:2024/ok` retourne `{"ok": true}`)
- [ ] Variables d'environnement configurées (`.env` contient OPENAI_API_KEY, WEAVIATE_URL, POSTGRES_CONNECTION_STRING)
- [ ] Ingestion complétée (15,061 documents indexés)
- [ ] Claude Desktop config correcte (`claude_desktop_config.json` avec chemin absolu)
- [ ] Python 3.11+ (`python3 --version`)
- [ ] Dependencies à jour (`poetry install`)

Si tous ces points sont OK et problème persiste, c'est un bug potentiel → créer issue GitHub.
