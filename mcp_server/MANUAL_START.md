# Guide de Démarrage Manuel - MCP LangChain Expert

## 🎯 Utilisation au Quotidien

### Démarrage Complet du Système

Quand vous redémarrez votre machine ou souhaitez utiliser le MCP LangChain Expert :

**1. Démarrer le serveur LangGraph backend**

```bash
cd /Users/stephane/Documents/work/chat-langchain
langgraph dev --no-browser --port 2024
```

Ce serveur doit rester en cours d'exécution. Vous verrez :
```
✅ Registering graph with id 'chat'
✅ Starting 1 background workers
Server ready at http://localhost:2024
```

**Astuce** : Laissez ce terminal ouvert ou exécutez en arrière-plan :
```bash
langgraph dev --no-browser --port 2024 > /tmp/langgraph_dev.log 2>&1 &
echo $! > /tmp/langgraph_dev.pid
```

**2. Vérifier que le serveur est opérationnel**

```bash
curl http://localhost:2024/info 2>/dev/null && echo "✅ Server is running"
```

**3. Lancer Claude Desktop**

Le MCP server se connecte automatiquement au démarrage de Claude Desktop (configuration déjà en place).

---

## 🔍 Vérification Rapide

### Le serveur LangGraph tourne-t-il ?

```bash
ps aux | grep "langgraph dev" | grep -v grep
```

Si rien ne s'affiche, le serveur n'est pas démarré.

### Le MCP est-il configuré ?

```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep -A 5 langchain-expert
```

Doit afficher la configuration du serveur `langchain-expert`.

---

## 🧪 Test du Système

Une fois Claude Desktop ouvert, testez dans Claude Code :

```
Utilise check_langchain_expert_status pour vérifier que le système fonctionne.
```

Réponse attendue :
```
✅ LangChain Expert System: OPERATIONAL

Server: http://localhost:2024
Available Assistants: chat
Active Sessions: 0
Indexed Documents: 15,061+ (LangChain/LangGraph documentation)

Models Available:
- openai/gpt-5-mini-2025-08-07 (default)
...
```

---

## 🛑 Arrêt du Système

### Arrêter proprement le serveur LangGraph

**Si démarré au premier plan** : `Ctrl+C` dans le terminal

**Si démarré en arrière-plan** :
```bash
# Trouver le PID
cat /tmp/langgraph_dev.pid

# Ou chercher le processus
ps aux | grep "langgraph dev" | grep -v grep

# Tuer le processus
kill $(cat /tmp/langgraph_dev.pid)
# Ou
pkill -f "langgraph dev"
```

### Vérifier l'arrêt
```bash
lsof -i :2024  # Ne doit rien afficher
```

---

## 📊 Monitoring des Logs

### Logs du serveur LangGraph

**Si démarré au premier plan** : Les logs s'affichent directement dans le terminal

**Si démarré en arrière-plan** :
```bash
tail -f /tmp/langgraph_dev.log
```

### Logs du MCP server

Les logs MCP apparaissent dans les logs de Claude Desktop :
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

---

## 🐛 Dépannage

### Le MCP n'apparaît pas dans Claude Code

1. **Vérifier que langgraph dev tourne** :
   ```bash
   curl http://localhost:2024/info
   ```

2. **Redémarrer Claude Desktop complètement** :
   - Quitter : `Cmd+Q` (pas juste fermer la fenêtre)
   - Relancer depuis Applications

3. **Vérifier la syntaxe JSON de la config** :
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool
   ```

### Timeout ou erreurs de connexion

1. **Vérifier que le serveur répond** :
   ```bash
   curl http://localhost:2024/info
   ```

2. **Voir les logs récents** :
   ```bash
   tail -50 /tmp/langgraph_dev.log
   ```

3. **Redémarrer le serveur LangGraph** :
   ```bash
   pkill -f "langgraph dev"
   cd /Users/stephane/Documents/work/chat-langchain
   langgraph dev --no-browser --port 2024
   ```

### Le port 2024 est déjà utilisé

```bash
# Identifier le processus
lsof -i :2024

# Tuer le processus si nécessaire
kill -9 $(lsof -t -i:2024)
```

---

## 📝 Commandes Utiles

### Démarrage rapide (une seule commande)

```bash
cd /Users/stephane/Documents/work/chat-langchain && langgraph dev --no-browser --port 2024 > /tmp/langgraph_dev.log 2>&1 & echo "PID: $!" | tee /tmp/langgraph_dev.pid
```

### Status complet

```bash
echo "=== LangGraph Status ==="
ps aux | grep "langgraph dev" | grep -v grep
echo ""
echo "=== Port 2024 ==="
lsof -i :2024
echo ""
echo "=== Recent Logs ==="
tail -20 /tmp/langgraph_dev.log
```

### Nettoyage complet

```bash
# Arrêter tous les processus
pkill -f "langgraph dev"

# Nettoyer les fichiers temporaires
rm -f /tmp/langgraph_dev.log /tmp/langgraph_dev.pid

# Vérifier
lsof -i :2024  # Doit être vide
```

---

## 💡 Conseils d'Utilisation

1. **Laissez le serveur LangGraph tourner** pendant vos sessions de développement
   - Il consomme peu de ressources (~500 MB RAM, <2% CPU au repos)
   - Évite les délais de démarrage à chaque utilisation

2. **Utilisez les sessions** pour les conversations multi-tours :
   ```
   Utilise langchain_expert pour expliquer les checkpoints (session "debug-checkpoints")
   ```

3. **GPT-5 mini par défaut** = rapide et économique
   - Pour des questions complexes, spécifiez explicitement GPT-5 complet si besoin

4. **Consultez les logs** en cas de problème
   - Logs LangGraph : `/tmp/langgraph_dev.log`
   - Logs MCP : `~/Library/Logs/Claude/`

---

## 🔗 Ressources

- **README principal** : `mcp_server/README.md`
- **Guide de test rapide** : `mcp_server/QUICK_START.md`
- **Code du serveur MCP** : `mcp_server/langchain_expert.py`
- **Configuration backend** : `backend/retrieval_graph/configuration.py`

---

## 📌 Configuration Actuelle

- **Serveur LangGraph** : `http://localhost:2024`
- **Modèle par défaut** : `openai/gpt-5-mini-2025-08-07`
- **Documents indexés** : 15,061+ (LangChain + LangGraph)
- **Timeout par défaut** : 180 secondes
- **MCP installé** : `~/Library/Application Support/Claude/claude_desktop_config.json`
