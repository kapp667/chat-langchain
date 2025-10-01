# Prompts Statiques LangSmith

Ce dossier contient les prompts extraits de LangSmith Hub pour permettre un déploiement 100% auto-hébergé sans dépendance à l'API LangSmith au runtime.

## Origine des Prompts

- **Source**: LangSmith Hub (namespace `langchain-ai/*`)
- **Endpoint API**: `https://api.smith.langchain.com/commits/langchain-ai/chat-langchain-{nom}-prompt/latest`
- **Date d'extraction**: 1er octobre 2025
- **Version**: Prompts de production utilisés par chat.langchain.com

## Prompts Inclus

| Fichier | Description | Variables d'entrée |
|---------|-------------|-------------------|
| `router.txt` | Classification des questions (langchain/more-info/general) | Aucune |
| `generate_queries.txt` | Génération de 3-5 requêtes de recherche diverses | Aucune |
| `more_info.txt` | Demande d'informations supplémentaires à l'utilisateur | `{logic}` |
| `research_plan.txt` | Planification de recherche multi-étapes | Aucune |
| `general.txt` | Réponse polie aux questions hors-sujet | `{logic}` |
| `response.txt` | Génération de réponse finale avec citations | `{context}` |

## Usage

### Option 1: Prompts Statiques (Recommandé pour Auto-Hébergement)

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts_static"

ROUTER_SYSTEM_PROMPT = (PROMPTS_DIR / "router.txt").read_text()
GENERATE_QUERIES_SYSTEM_PROMPT = (PROMPTS_DIR / "generate_queries.txt").read_text()
MORE_INFO_SYSTEM_PROMPT = (PROMPTS_DIR / "more_info.txt").read_text()
RESEARCH_PLAN_SYSTEM_PROMPT = (PROMPTS_DIR / "research_plan.txt").read_text()
GENERAL_SYSTEM_PROMPT = (PROMPTS_DIR / "general.txt").read_text()
RESPONSE_SYSTEM_PROMPT = (PROMPTS_DIR / "response.txt").read_text()
```

### Option 2: LangSmith Hub API (Nécessite API Key)

```python
from langsmith import Client

client = Client()
ROUTER_SYSTEM_PROMPT = (
    client.pull_prompt("langchain-ai/chat-langchain-router-prompt")
    .messages[0]
    .prompt.template
)
# ... etc
```

## Mise à Jour des Prompts

Pour mettre à jour les prompts avec la dernière version de production:

```bash
cd backend/prompts_static
./update_prompts.sh
```

Ou manuellement:

```bash
export LANGCHAIN_API_KEY="lsv2_pt_..."

for prompt in router generate-queries more-info research-plan general response; do
  curl -s -H "x-api-key: ${LANGCHAIN_API_KEY}" \
    "https://api.smith.langchain.com/commits/langchain-ai/chat-langchain-${prompt}-prompt/latest" \
    | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['manifest']['kwargs']['messages'][0]['kwargs']['prompt']['kwargs']['template'])" \
    > ${prompt//-/_}.txt
done
```

## Avantages des Prompts Statiques

✅ **Zéro dépendance runtime** - Pas besoin d'API Key LangSmith au démarrage
✅ **Démarrage instantané** - Pas d'appels réseau au lancement
✅ **Déploiement offline** - Fonctionne sans connexion Internet
✅ **Versioning Git** - Historique complet des modifications de prompts
✅ **Débogage facile** - Prompts lisibles en texte brut

## Inconvénients

❌ **Mises à jour manuelles** - Nécessite script de synchronisation
❌ **Divergence possible** - Peut différer de la production LangChain

## Recommandation

Pour un environnement de production auto-hébergé, utilisez les prompts statiques. Pour un environnement de développement synchronisé avec chat.langchain.com, utilisez l'API LangSmith Hub.
