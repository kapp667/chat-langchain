# Statut du Serveur MCP LangChain Expert

**Date de création** : 1er octobre 2025
**Dernière mise à jour** : 2 octobre 2025 (refactorisation depth)
**Statut** : ✅ Opérationnel - 4 outils avec intelligence configurable

---

## ✅ Configuration Complétée

### Backend LangGraph
- [x] Modèle configuré : `openai/gpt-5-mini-2025-08-07`
- [x] Serveur langgraph dev opérationnel (port 2024)
- [x] 15,061+ documents indexés (LangChain + LangGraph)
- [x] Hot-reload activé pour développement

### Serveur MCP
- [x] Code implémenté : `mcp_server/langchain_expert.py` (341 lignes)
- [x] Dépendances installées (mcp, langgraph-sdk)
- [x] **4 outils exposés** :
  - `ask_langchain_expert` - Outil principal avec **3 niveaux d'intelligence** :
    - `depth="quick"` : GPT-4o-mini (~5-10s) - Questions simples
    - `depth="standard"` : GPT-5 mini (~10-20s) - Usage normal [DÉFAUT]
    - `depth="deep"` : GPT-5 full (~60-180s, max 4min*) - Analyse complexe

    \*Limité à 4 minutes par le timeout client de Claude Desktop
  - `clear_session` - Gestion de session (usage normal)
  - `list_sessions` - [DEBUG] Inspection sessions actives
  - `check_langchain_expert_status` - [MONITORING] Health check
- [x] Thread management implémenté
- [x] Session management pour conversations multi-tours
- [x] Fonction interne DRY (`_ask_expert_internal`)
- [x] Tests validés avec succès

### Intégration Claude Desktop
- [x] Configuration ajoutée à `~/Library/Application Support/Claude/claude_desktop_config.json`
- [x] **Problème PATH résolu** : Utilisation du chemin absolu vers `uv` (2 oct 2025)
  - Avant : `"command": "uv"` ❌ (spawn ENOENT)
  - Après : `"command": "/Users/stephane/Library/Python/3.9/bin/uv"` ✅
- [x] Coexiste avec le serveur MCP `youtube` existant
- [x] Test de démarrage validé (`test_startup.py`)
- [x] Prêt à l'emploi après redémarrage de Claude Desktop

---

## 📚 Documentation Créée

1. **README.md** - Documentation complète du serveur MCP (298 lignes)
   - Installation
   - Configuration
   - Usage des 5 outils
   - Troubleshooting
   - Architecture

2. **QUICK_START.md** - Guide de test rapide
   - Vérification de la configuration
   - Commandes de test dans Claude Code
   - Résultats attendus

3. **MANUAL_START.md** - Guide de démarrage manuel ⭐
   - Démarrage du système complet
   - Vérifications
   - Arrêt propre
   - Dépannage
   - Commandes utiles

4. **STATUS.md** (ce fichier) - État du projet

5. **TROUBLESHOOTING_MCP.md** - Guide de dépannage PATH ⭐ (2 oct 2025)
   - Problème "spawn uv ENOENT" résolu
   - Solutions alternatives (Python direct, poetry, script wrapper)
   - Script de diagnostic complet
   - Logs et vérifications

6. **test_startup.py** - Test de démarrage du serveur MCP
   - Vérifie les imports (mcp, langgraph-sdk)
   - Teste la connexion LangGraph
   - Confirme la création de l'instance MCP

---

## 🚀 Prochaines Étapes

### Pour Tester Maintenant (5 minutes)

1. **Redémarrer Claude Desktop**
   ```bash
   # Quitter complètement (Cmd+Q)
   # Puis relancer depuis Applications
   ```

2. **Vérifier que langgraph dev tourne**
   ```bash
   ps aux | grep "langgraph dev" | grep -v grep
   ```
   Si non : `langgraph dev --no-browser --port 2024`

3. **Tester dans Claude Code**
   ```
   Utilise check_langchain_expert_status
   ```

### Utilisation Quotidienne

**Voir le guide complet** : `MANUAL_START.md`

**Commande rapide** (si serveur arrêté) :
```bash
cd /Users/stephane/Documents/work/chat-langchain
langgraph dev --no-browser --port 2024 > /tmp/langgraph_dev.log 2>&1 &
```

---

## 🎯 Fonctionnalités Validées

✅ **Connexion au backend LangGraph**
- Thread creation via API
- Streaming des réponses
- Configuration des modèles

✅ **Qualité des réponses**
- Réponses expertes avec citations
- Sources documentées ([1], [2], etc.)
- Structure organisée (concepts → pratique)
- Exemples de code inclus

✅ **Performance**
- Première requête : ~180s (initialisation modèle)
- Requêtes suivantes : 8-20s
- GPT-5 mini = coût-efficace (~95% moins cher que full GPT-5)

✅ **Gestion des sessions**
- Conversations multi-tours avec même `session_id`
- Cache de threads en mémoire
- Nettoyage de sessions

---

## 💡 Exemples d'Utilisation

### Question Simple
```
Utilise langchain_expert : "Qu'est-ce que LangChain ?"
```

### Question Complexe
```
Utilise langchain_expert : "Comment implémenter un système multi-agent avec LangGraph incluant human-in-the-loop et checkpoints PostgreSQL ?"
```

### Conversation Multi-tours
```
Utilise langchain_expert : "Explique les checkpoints LangGraph" (session "debug")

[Après réponse]

Utilise langchain_expert : "Comment les implémenter avec AsyncPostgresSaver ?" (session "debug")
```

### Model Upgrade (questions complexes)
```
Utilise ask_langchain_expert_advanced : "Conçois une architecture production-grade pour un agent LangGraph avec observabilité complète"
```

---

## 📊 Configuration Technique

```json
{
  "Backend": {
    "query_model": "openai/gpt-5-mini-2025-08-07",
    "response_model": "openai/gpt-5-mini-2025-08-07",
    "documents": "15,061+",
    "url": "http://localhost:2024"
  },
  "MCP Server": {
    "tools": 5,
    "default_timeout": 180,
    "session_management": true,
    "streaming": true
  },
  "Claude Desktop": {
    "config_path": "~/Library/Application Support/Claude/claude_desktop_config.json",
    "mcp_servers": ["youtube", "langchain-expert"]
  }
}
```

---

## 🔗 Fichiers Importants

**Code Source**
- `mcp_server/langchain_expert.py` - Serveur MCP (309 lignes)
- `backend/retrieval_graph/configuration.py` - Configuration modèles

**Configuration**
- `~/Library/Application Support/Claude/claude_desktop_config.json` - Config MCP
- `.env` - Variables d'environnement (OpenAI API key, etc.)
- `langgraph.json` - Configuration LangGraph

**Documentation**
- `mcp_server/README.md` - Doc complète
- `mcp_server/MANUAL_START.md` - Guide démarrage manuel
- `mcp_server/QUICK_START.md` - Guide test rapide

**Tests**
- `mcp_server/archive/test_mcp.py` - Tests complets
- `mcp_server/archive/test_model_verification.py` - Vérification modèle

---

## 🐛 Support

En cas de problème, consultez dans cet ordre :

1. **MANUAL_START.md** - Section Dépannage
2. **Logs** :
   - LangGraph : `/tmp/langgraph_dev.log`
   - MCP : `~/Library/Logs/Claude/`
3. **README.md** - Section Troubleshooting

**Commande de diagnostic rapide** :
```bash
echo "=== LangGraph Status ==="
ps aux | grep "langgraph dev" | grep -v grep
echo ""
echo "=== Port 2024 ==="
lsof -i :2024
echo ""
echo "=== MCP Config ==="
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep -A 10 langchain-expert
```

---

**Système prêt à l'emploi !** 🎉

Redémarrez Claude Desktop et testez avec `check_langchain_expert_status`
