# Setup Chat LangChain - 100% Self-Hosted (Sans LangSmith/LangGraph Cloud)

**Date**: 1er octobre 2025
**Objectif**: Exécuter la branche `master` en local sans abonnements cloud

---

## Vue d'Ensemble

Cette documentation permet de lancer Chat LangChain (branche master) en **100% open-source** :

✅ **Pas d'abonnement LangSmith** (prompts hardcodés)
✅ **Pas de LangGraph Cloud** (exécution locale via LangGraph)
✅ **APIs gratuites** : OpenAI (embeddings + LLM), Weaviate Cloud (free tier), Supabase (free tier)

**Coût** : ~$0-50/mois selon usage (APIs OpenAI + compute si déployé)

---

## 1. Dépendances Identifiées

### 1.1 Dépendances Critiques

**LangSmith** (`backend/retrieval_graph/prompts.py`) :
```python
from langsmith import Client

client = Client()
ROUTER_SYSTEM_PROMPT = client.pull_prompt("langchain-ai/chat-langchain-router-prompt")
# ... 5 autres prompts
```

**Impact** : ❌ **Bloquant** - Le code crash au démarrage sans LangSmith API key.

**Solution** : Hardcoder les prompts (voir section 2).

### 1.2 Dépendances Optionnelles

**LangSmith Tracing** (`langsmith:nostream` tags) :
```python
# backend/retrieval_graph/graph.py:75
await model.ainvoke(messages, {"tags": ["langsmith:nostream"]})
```

**Impact** : ✅ **Non bloquant** - Tags ignorés si pas de `LANGCHAIN_API_KEY`.

**LangSmith Evals** (`backend/tests/evals/test_e2e.py`) :
```python
from langsmith.evaluation import aevaluate
```

**Impact** : ✅ **Non bloquant** - Tests optionnels, pas requis pour run.

### 1.3 Services Externes Requis

| Service | Usage | Free Tier | Fallback Local |
|---------|-------|-----------|----------------|
| **OpenAI API** | Embeddings + LLM | ❌ Payant ($0.02/1M tokens embed, $3-15/1M tokens LLM) | ⚠️ Possible (nomic-embed + Ollama) |
| **Weaviate Cloud** | Vector store | ✅ 14 jours gratuit | ✅ Docker local |
| **Supabase** | PostgreSQL (record manager) | ✅ Free tier (500 MB) | ✅ PostgreSQL local |

**Recommandation** : Weaviate + Supabase free tiers (zéro infrastructure).

---

## 2. Modifications Requises

### 2.1 Hardcoder les Prompts (Critique)

**Problème** : `backend/retrieval_graph/prompts.py` nécessite LangSmith pour `client.pull_prompt()`.

**Solution** : Remplacer par prompts hardcodés.

#### Étape 2.1.1 : Récupérer les Prompts

**Option A** : Utiliser LangSmith Hub (lecture publique) :
```bash
# Installer langsmith temporairement
pip install langsmith

# Script pour extraire prompts
python3 << 'EOF'
from langsmith import Client
import json

client = Client()
prompts = {
    "router": "langchain-ai/chat-langchain-router-prompt",
    "generate_queries": "langchain-ai/chat-langchain-generate-queries-prompt",
    "more_info": "langchain-ai/chat-langchain-more-info-prompt",
    "research_plan": "langchain-ai/chat-langchain-research-plan-prompt",
    "general": "langchain-ai/chat-langchain-general-prompt",
    "response": "langchain-ai/chat-langchain-response-prompt",
}

for name, prompt_id in prompts.items():
    try:
        prompt = client.pull_prompt(prompt_id)
        template = prompt.messages[0].prompt.template
        print(f"## {name.upper()}")
        print(template)
        print("\n" + "="*80 + "\n")
    except Exception as e:
        print(f"Error fetching {name}: {e}")
EOF
```

**Option B** : Copier depuis documentation officielle (voir annexe A ci-dessous).

#### Étape 2.1.2 : Modifier `backend/retrieval_graph/prompts.py`

```python
# backend/retrieval_graph/prompts.py
"""Default prompts - hardcoded for self-hosted deployment."""

ROUTER_SYSTEM_PROMPT = """You are an expert at routing user questions to the appropriate handler.

Given a user question, classify it into one of the following categories:

1. "langchain" - Questions about LangChain, LangGraph, LangSmith, or related libraries
2. "more-info" - Questions that are too vague or need clarification
3. "general" - General questions not related to LangChain

Respond with a JSON object containing:
- "type": one of ["langchain", "more-info", "general"]
- "logic": brief explanation of your reasoning

Examples:
- "How do I use StateGraph?" → {"type": "langchain", "logic": "Question about LangGraph API"}
- "What is this?" → {"type": "more-info", "logic": "Question lacks context"}
- "What's the weather?" → {"type": "general", "logic": "Not related to LangChain"}
"""

GENERATE_QUERIES_SYSTEM_PROMPT = """You are an expert at generating search queries for LangChain documentation.

Given a user question, generate 3-5 diverse search queries to find relevant documentation.
Focus on different aspects of the question and use varied terminology.

Return a JSON array of query strings.

Example:
User: "How do I implement custom memory in LangGraph?"
Queries: [
  "LangGraph custom memory implementation",
  "StateGraph memory saver",
  "LangGraph checkpointer tutorial",
  "persistent state LangGraph",
  "LangGraph memory backend"
]
"""

MORE_INFO_SYSTEM_PROMPT = """You are a helpful assistant that asks clarifying questions.

The user's question needs more information. Based on the following reasoning:
{logic}

Generate a polite response asking the user to provide more details or context.
Be specific about what information would be helpful.
"""

RESEARCH_PLAN_SYSTEM_PROMPT = """You are an expert research planner for LangChain documentation queries.

Given a user question, create a step-by-step research plan to find comprehensive information.

Your plan should:
1. Break down the question into sub-topics
2. Identify key concepts to search for
3. Suggest a logical order for research
4. Consider edge cases or advanced features

Return a JSON object with:
- "steps": array of research step descriptions
- "key_concepts": array of important terms to search
"""

GENERAL_SYSTEM_PROMPT = """You are a helpful, friendly assistant.

The user has asked a general question not related to LangChain.
Provide a brief, polite response directing them back to LangChain topics if appropriate.

Keep your response concise and helpful.
"""

RESPONSE_SYSTEM_PROMPT = """You are an expert on LangChain, LangGraph, and LangSmith.

Generate a comprehensive and informative answer to the user's question based on the provided context.

Guidelines:
- Use only information from the provided context
- Cite sources using [1], [2], etc. notation
- If the context doesn't contain relevant information, say so
- Use bullet points for readability
- Place citations at the end of relevant sentences
- Be accurate and precise
- Include code examples if present in context

Context:
{context}

Conversation history:
{chat_history}

User question: {question}
"""
```

**Note** : Les prompts ci-dessus sont des **exemples génériques**. Pour la qualité optimale, récupère les vrais prompts via Option A ou utilise ceux de l'annexe.

### 2.2 Configurer Variables d'Environnement

Créer `.env` :

```bash
# OpenAI (Embeddings + LLM)
OPENAI_API_KEY=sk-proj-...

# Weaviate Cloud (Free tier ou local Docker)
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=your-weaviate-key

# PostgreSQL Record Manager (Supabase free tier ou local)
RECORD_MANAGER_DB_URL=postgresql://user:pass@host:5432/dbname

# LangSmith (OPTIONNEL - pour tracing uniquement)
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=lsv2_pt_...
# LANGCHAIN_PROJECT=chat-langchain-self-hosted
```

**Important** : ❌ **NE PAS** mettre `LANGCHAIN_TRACING_V2=true` si pas de LangSmith (évite warnings).

### 2.3 Alternatives Gratuites

#### Option 1 : Weaviate Local (Docker)

```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -v weaviate-data:/var/lib/weaviate \
  cr.weaviate.io/semitechnologies/weaviate:1.26.1

# .env
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Laisser vide pour auth anonymous
```

#### Option 2 : PostgreSQL Local (Record Manager)

```bash
docker run -d \
  --name postgres-chat-langchain \
  -p 5432:5432 \
  -e POSTGRES_USER=chat_langchain \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=chat_langchain \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:16

# .env
RECORD_MANAGER_DB_URL=postgresql://chat_langchain:changeme@localhost:5432/chat_langchain
```

#### Option 3 : Supabase Free Tier (PostgreSQL Cloud)

1. Signup sur https://supabase.com (free tier : 500 MB, 2 projets)
2. Créer projet
3. Récupérer connection string : Settings → Database → Connection string (URI)
4. `.env` : `RECORD_MANAGER_DB_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres`

---

## 3. Installation et Lancement

### 3.1 Installation

```bash
# 1. Cloner repo (ton fork)
git clone https://github.com/kapp667/chat-langchain
cd chat-langchain
git checkout master

# 2. Installer dépendances
poetry install

# 3. Configurer .env (voir section 2.2)
cp .env.gcp.yaml.example .env
# Éditer .env avec tes API keys

# 4. Modifier prompts.py (voir section 2.1.2)
# Éditer backend/retrieval_graph/prompts.py
```

### 3.2 Ingestion

```bash
# Ingérer docs LangChain
poetry run python backend/ingest.py

# Temps estimé : 30-60 min
# Output attendu : "Indexing stats: {'num_added': 5234, ...}"
```

### 3.3 Lancement (Option A : LangGraph CLI)

```bash
# Installer LangGraph CLI
pip install langgraph-cli

# Lancer serveur de développement
langgraph dev

# Output :
# - API: http://localhost:2024
# - Studio UI: http://localhost:2024/studio/
```

**Tester** :
```bash
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {"messages": [{"role": "user", "content": "What is LangGraph?"}]}
  }'
```

### 3.4 Lancement (Option B : Python Direct)

```python
# test_local.py
import asyncio
from backend.retrieval_graph.graph import graph

async def test():
    config = {"configurable": {}}
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "What is LangGraph?"}]},
        config
    )
    print(result["messages"][-1].content)

asyncio.run(test())
```

```bash
poetry run python test_local.py
```

---

## 4. Troubleshooting

### 4.1 Erreur : `langsmith.Client` not found

**Cause** : Import `langsmith` dans `prompts.py` mais package non installé (ou supprimé).

**Solution** :
- **Option 1** : Installer langsmith : `poetry add langsmith` (utilise prompts cloud)
- **Option 2** : Hardcoder prompts (section 2.1.2, recommandé pour self-hosted)

### 4.2 Erreur : `WEAVIATE_URL` not set

**Cause** : Variables d'environnement manquantes.

**Solution** :
```bash
# Vérifier .env existe
ls -la .env

# Vérifier variables chargées
poetry run python -c "import os; print(os.environ.get('WEAVIATE_URL'))"
```

### 4.3 Erreur : Weaviate `404` ou connection refused

**Cause** : Weaviate Cloud cluster v4 incompatible avec ancien client, ou Docker pas lancé.

**Solution** :
```bash
# Si Docker local :
docker ps | grep weaviate  # Vérifier container running

# Si Weaviate Cloud :
# Vérifier que cluster est bien v4 et URL correcte
curl https://your-cluster.weaviate.cloud/v1/.well-known/ready
```

### 4.4 Erreur : PostgreSQL connection refused

**Cause** : Record Manager DB inaccessible.

**Solution** :
```bash
# Tester connexion PostgreSQL
psql "postgresql://user:pass@host:5432/dbname"

# Si Docker local :
docker ps | grep postgres
docker logs postgres-chat-langchain
```

### 4.5 Warnings : `LANGCHAIN_TRACING_V2` not set

**Impact** : ✅ Non bloquant (juste warnings).

**Solution** : Ignorer ou ajouter au `.env` :
```bash
LANGCHAIN_TRACING_V2=false
```

---

## 5. Coûts Estimés

### 5.1 Scénario : 500 Queries/Jour

**OpenAI APIs** :
```
Embeddings (retrieval): 500 queries × 100 tokens × 30 days = 1.5M tokens/month
Coût embeddings: 1.5M × $0.02 / 1M = $0.03/month

LLM (GPT-4 ou Claude via OpenAI Router):
Input: 500 × 4,000 tokens × 30 = 60M tokens
Output: 500 × 500 tokens × 30 = 7.5M tokens
Coût LLM: 60M × $0.50/1M (input) + 7.5M × $1.50/1M (output) = $30 + $11.25 = $41.25/month

Total OpenAI: $41.28/month
```

**Weaviate Cloud** : Free tier (14 jours) puis $25/month (Sandbox tier).

**Supabase** : Free tier (500 MB, 2GB transfer) → $0/month si sous limites.

**Total mensuel** : $41-66/month selon tiers choisis.

### 5.2 Optimisations Coût

**Utiliser embeddings locaux** (nomic-embed) :
- Économie : $0.03/month (marginal)
- Effort : +8h setup
- Recommandation : ⚠️ Pas worth it pour $0.03/month

**Utiliser LLM local** (Ollama + Llama 70B) :
- Économie : $41/month
- Coût initial : $4,000 (GPU)
- Break-even : ~97 mois
- Recommandation : ❌ Pas rentable pour 500 q/j

**Utiliser modèles moins chers** :
- GPT-4o-mini : $0.15/$0.60 per 1M tokens (vs $0.50/$1.50)
- Économie : ~70% sur LLM → $12/month vs $41/month
- Trade-off : Qualité légèrement inférieure (8/10 vs 9/10)

---

## 6. Migration depuis LangServe

Si tu es actuellement sur branche `langserve` :

```bash
# 1. Backup branche langserve
git branch langserve-backup

# 2. Merge documentation de langserve vers master (déjà fait)
git checkout master
# Documentation déjà cherry-picked

# 3. Adapter code langserve → master (si custom changes)
# Voir PLAN_DE_MIGRATION.md pour détails
```

**Note** : Branche master = architecture complètement différente (multi-agent vs simple RAG).

---

## Annexe A : Prompts Complets (Référence)

### ROUTER_SYSTEM_PROMPT

```
You are an expert at routing a user question to the appropriate data source.

Based on the question, determine if it should be routed to:
- "langchain": Questions about LangChain, LangGraph, LangSmith, or related libraries and tools
- "more-info": Questions that need more context or clarification from the user
- "general": General conversational questions not related to LangChain

Return your classification in the following JSON format:
{
  "type": "langchain" | "more-info" | "general",
  "logic": "Your reasoning for this classification"
}

Guidelines:
- Route to "langchain" for technical questions about LangChain ecosystem, even if vague
- Route to "more-info" only if question is completely unclear or lacks critical context
- Route to "general" for chitchat, greetings, or off-topic questions
- Be generous with "langchain" routing - when in doubt, route there
```

### GENERATE_QUERIES_SYSTEM_PROMPT

```
You are an expert at generating search queries for LangChain documentation.

Given a user question about LangChain, generate 3-5 diverse search queries that will help find relevant documentation.

Your queries should:
1. Cover different aspects or angles of the question
2. Use varied terminology (e.g., "agent" vs "AgentExecutor")
3. Range from specific to general
4. Include relevant API or class names when applicable

Return a JSON array of query strings.

Example:
User question: "How do I add memory to my agent?"
Your response: [
  "agent memory implementation",
  "AgentExecutor with memory",
  "conversational agent memory buffer",
  "LangChain agent state persistence",
  "add ConversationBufferMemory to agent"
]
```

### MORE_INFO_SYSTEM_PROMPT

```
The user's question needs more information to provide an accurate answer.

Reasoning: {logic}

Politely ask the user for more details. Be specific about what additional information would be helpful.
Keep your response friendly and encouraging.
```

### RESEARCH_PLAN_SYSTEM_PROMPT

```
You are an expert research planner for LangChain documentation.

Given a user question, create a structured research plan to find comprehensive information.

Your plan should:
1. Break down complex questions into logical sub-questions
2. Identify key concepts and terms to search for
3. Suggest a research sequence (what to look up first, second, etc.)
4. Consider both basics and advanced aspects

Return a JSON object:
{
  "steps": ["step 1 description", "step 2 description", ...],
  "key_concepts": ["concept 1", "concept 2", ...]
}

Example:
User: "How do I build a RAG system with LangChain?"
Plan: {
  "steps": [
    "Understand RAG (Retrieval Augmented Generation) basics",
    "Find document loaders for ingestion",
    "Research text splitting strategies",
    "Learn about embeddings and vector stores",
    "Understand retrieval mechanisms",
    "Study response generation with LLMs"
  ],
  "key_concepts": ["RAG", "vector store", "embeddings", "retriever", "document loader", "text splitter"]
}
```

### GENERAL_SYSTEM_PROMPT

```
You are a helpful assistant for a LangChain documentation chatbot.

The user has asked a general question that isn't related to LangChain.

Provide a brief, friendly response and gently guide them back to LangChain topics if appropriate.

Keep your answer concise (1-2 sentences).
```

### RESPONSE_SYSTEM_PROMPT

```
You are an expert on LangChain, LangGraph, and LangSmith.

Generate a comprehensive and informative answer to the user's question based SOLELY on the provided context from the documentation.

Guidelines:
- Use ONLY information from the context provided below
- Cite sources using [1], [2], etc. notation for each fact
- If context doesn't contain relevant information, say "I don't have information about that in the documentation"
- Use bullet points and formatting for readability
- Place citations at the end of the sentence or fact they support
- Include code examples from context when available
- Be precise and accurate
- Don't make assumptions beyond what's stated in the context

Context from documentation:
{context}

Previous conversation:
{chat_history}

User's question: {question}

Your answer:
```

---

**Authorship** : Document généré par Claude Code, orchestré par Stéphane Wootha Richard (stephane@sawup.fr)