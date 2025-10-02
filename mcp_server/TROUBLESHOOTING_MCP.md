# Troubleshooting MCP Server - LangChain Expert

## Problème Résolu : "spawn uv ENOENT" (2 octobre 2025)

### Symptômes

Lors du démarrage de Claude Desktop, les erreurs suivantes apparaissent :

```
❌ Could not connect to MCP server langchain-expert
❌ MCP langchain-expert: spawn uv ENOENT 2
❌ MCP langchain-expert: Server disconnected
```

Dans les paramètres MCP de Claude Desktop :
- Server status: **failed**
- Erreur: "Server disconnected"

### Cause Racine

**Problème** : Claude Desktop (application GUI macOS) ne trouve pas la commande `uv` dans son PATH.

**Explication** :
- Les applications GUI macOS (lancées depuis Finder/Dock) n'héritent **PAS** du PATH shell configuré dans `.zshrc` ou `.bashrc`
- Le PATH des apps GUI est limité : `/usr/bin:/bin:/usr/sbin:/sbin`
- `uv` est installé dans un emplacement non-standard : `/Users/stephane/Library/Python/3.9/bin/uv`
- La commande `uv` fonctionne dans le terminal mais pas dans Claude Desktop

**Pourquoi `npx` fonctionne pour le serveur youtube ?**
- `npx` est installé via Homebrew ou Node.js dans un emplacement système standard (souvent `/usr/local/bin`)
- `/usr/local/bin` est généralement dans le PATH des apps GUI macOS

### Solution Appliquée

Utiliser le **chemin absolu** vers `uv` au lieu du nom de commande seul.

#### Configuration AVANT (ne fonctionne pas)

```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "uv",  // ❌ Ne sera pas trouvé par Claude Desktop
      "args": ["--directory", "...", "run", "..."]
    }
  }
}
```

#### Configuration APRÈS (fonctionne)

```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "/Users/stephane/Library/Python/3.9/bin/uv",  // ✅ Chemin absolu
      "args": [
        "--directory",
        "/Users/stephane/Documents/work/chat-langchain/mcp_server",
        "run",
        "--no-project",
        "python",
        "langchain_expert.py"
      ],
      "env": {
        "LANGGRAPH_URL": "http://localhost:2024"
      }
    }
  }
}
```

#### Fichier modifié

```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Vérification de la Solution

#### 1. Trouver le chemin absolu de `uv`

```bash
which uv
# Output: /Users/stephane/Library/Python/3.9/bin/uv
```

#### 2. Tester manuellement le serveur MCP

```bash
cd /Users/stephane/Documents/work/chat-langchain/mcp_server
/Users/stephane/Library/Python/3.9/bin/uv run --no-project python test_startup.py
```

**Résultat attendu** :
```
✅ Imports successful
✅ LangGraph connection OK - Version: 0.4.28
✅ MCP server instance created
✅ All startup checks passed!
```

#### 3. Redémarrer Claude Desktop

**Important** : Quitter complètement (Cmd+Q), pas juste fermer la fenêtre.

```bash
# 1. Quitter Claude Desktop : Cmd+Q
# 2. Relancer depuis Applications
```

#### 4. Vérifier la connexion dans Claude Desktop

Paramètres → MCP → Serveurs locaux :
- ✅ Server `langchain-expert` doit afficher le statut **connected** ou **ready**
- ❌ Si toujours "failed", voir les logs

### Logs pour Diagnostic

#### Logs Claude Desktop (macOS)

```bash
# Logs MCP en temps réel
tail -f ~/Library/Logs/Claude/mcp*.log

# Logs généraux de Claude Desktop
ls -lt ~/Library/Logs/Claude/
```

#### Vérification LangGraph backend

```bash
# Vérifier que langgraph dev est actif
ps aux | grep "langgraph dev" | grep -v grep

# Tester l'endpoint
curl http://localhost:2024/info

# Logs langgraph dev (si démarré en arrière-plan)
tail -f /tmp/langgraph_dev.log
```

### Autres Solutions Possibles

Si le problème persiste après avoir utilisé le chemin absolu :

#### Option A : Utiliser Python directement (sans `uv`)

```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "/usr/bin/python3",
      "args": [
        "/Users/stephane/Documents/work/chat-langchain/mcp_server/langchain_expert.py"
      ],
      "env": {
        "LANGGRAPH_URL": "http://localhost:2024",
        "PYTHONPATH": "/Users/stephane/Documents/work/chat-langchain/mcp_server"
      }
    }
  }
}
```

**Prérequis** : Installer les dépendances dans Python système ou virtualenv accessible.

#### Option B : Utiliser `poetry run`

```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "/usr/local/bin/poetry",
      "args": [
        "run",
        "-C",
        "/Users/stephane/Documents/work/chat-langchain/mcp_server",
        "python",
        "langchain_expert.py"
      ],
      "env": {
        "LANGGRAPH_URL": "http://localhost:2024"
      }
    }
  }
}
```

**Note** : Nécessite un `pyproject.toml` dans `mcp_server/`.

#### Option C : Script wrapper avec PATH complet

Créer `/Users/stephane/Documents/work/chat-langchain/mcp_server/run_mcp.sh` :

```bash
#!/bin/bash
export PATH="/Users/stephane/Library/Python/3.9/bin:$PATH"
cd /Users/stephane/Documents/work/chat-langchain/mcp_server
exec uv run --no-project python langchain_expert.py
```

Puis :

```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "/Users/stephane/Documents/work/chat-langchain/mcp_server/run_mcp.sh",
      "args": [],
      "env": {
        "LANGGRAPH_URL": "http://localhost:2024"
      }
    }
  }
}
```

**Attention** : Rendre le script exécutable avec `chmod +x run_mcp.sh`.

### Problèmes Connexes

#### "Server disconnected" après connexion initiale

**Cause** : langgraph dev n'est pas actif sur port 2024

**Solution** :
```bash
cd /Users/stephane/Documents/work/chat-langchain
langgraph dev --no-browser --port 2024
```

#### Timeout lors des requêtes

**Cause** : Initialisation du modèle GPT-5 mini (première requête)

**Normal** :
- Première requête : ~180s
- Requêtes suivantes : 8-20s

**Si toujours timeout** : Vérifier les clés API OpenAI dans `.env`

#### Import errors dans le serveur MCP

**Cause** : Dépendances non installées

**Solution** :
```bash
cd /Users/stephane/Documents/work/chat-langchain/mcp_server
/Users/stephane/Library/Python/3.9/bin/uv pip install mcp langgraph-sdk
```

### Commandes de Diagnostic Complètes

```bash
# === Script de diagnostic complet ===

echo "=== 1. Chemin uv ==="
which uv

echo ""
echo "=== 2. LangGraph dev status ==="
ps aux | grep "langgraph dev" | grep -v grep

echo ""
echo "=== 3. Port 2024 ==="
lsof -i :2024

echo ""
echo "=== 4. LangGraph info endpoint ==="
curl -s http://localhost:2024/info | python3 -m json.tool

echo ""
echo "=== 5. Dépendances MCP ==="
/Users/stephane/Library/Python/3.9/bin/uv pip list | grep -E "(mcp|langgraph)"

echo ""
echo "=== 6. Test startup MCP ==="
cd /Users/stephane/Documents/work/chat-langchain/mcp_server
/Users/stephane/Library/Python/3.9/bin/uv run --no-project python test_startup.py

echo ""
echo "=== 7. Config Claude Desktop ==="
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool
```

Sauvegarder comme `diagnose_mcp.sh` et exécuter :

```bash
chmod +x diagnose_mcp.sh
./diagnose_mcp.sh
```

### Résumé de la Solution

✅ **Problème identifié** : PATH incomplet dans les apps GUI macOS
✅ **Solution appliquée** : Chemin absolu vers `uv` dans `claude_desktop_config.json`
✅ **Vérification** : Test startup passé (`test_startup.py`)
✅ **Prochaine étape** : Redémarrer Claude Desktop (Cmd+Q puis relancer)

---

**Fichier créé** : 2 octobre 2025
**Problème résolu** : Configuration PATH pour MCP server
**Impact** : MCP server peut maintenant démarrer correctement dans Claude Desktop

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Stéphane Wootha Richard <stephane@sawup.fr>
