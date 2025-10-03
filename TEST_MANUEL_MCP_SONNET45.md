# Test Manuel - Claude Desktop MCP avec Sonnet 4.5

**Date:** 3 octobre 2025
**Objectif:** Valider que Claude Desktop MCP utilise bien Sonnet 4.5 et constater l'amélioration

## Pré-requis

✅ Backend LangGraph en cours d'exécution (`http://localhost:2024`)
✅ Claude Desktop installé et configuré
✅ MCP server `langchain-expert` actif

## Test 1 : Question Simple (Baseline)

### Question à Poser
```
@langchain-expert I need to save conversation history to PostgreSQL.
Which class should I use?
```

### Résultat Attendu avec Sonnet 4.5

**⏱️ Vitesse:** ~22-30 secondes
**📏 Longueur:** ~1,400-1,500 caractères
**✅ Qualité:** Réponse complète avec :
- Nom de la classe précis (`PostgresChatMessageHistory`)
- Exemple de code Python et JavaScript
- Variantes (Google Cloud SQL)
- Mention du `session_id`

### Comparaison GPT-5 Mini (Ancien)
- **Vitesse:** ~60 secondes (2× plus lent)
- **Longueur:** ~1,000-1,200 caractères
- **Qualité:** Bonne mais moins de détails

## Test 2 : Question Complexe (Challenge)

### Question à Poser
```
@langchain-expert I want to build a research assistant that:
(1) breaks down complex questions into sub-questions,
(2) searches documentation for each sub-question,
(3) synthesizes findings.
How should I structure this?
```

### Résultat Attendu avec Sonnet 4.5

**⏱️ Vitesse:** ~35-45 secondes
**📏 Longueur:** ~3,900-4,200 caractères
**✅ Qualité:** Réponse ultra-détaillée avec :
- Architecture overview avec LangGraph
- Code examples pour chaque composant
- Query decomposition node
- Retrieval node
- Synthesis node
- Agent vs Chain comparaison
- Liens vers documentation

### Comparaison GPT-5 Mini (Ancien)
- **Vitesse:** ~120 secondes (2.7× plus lent)
- **Longueur:** ~2,500 caractères
- **Qualité:** Bonne mais moins exhaustive

## Test 3 : Question Ultra-Complexe (Stress Test)

### Question à Poser
```
@langchain-expert I want to create a planning agent that explores
multiple solution paths, can backtrack when hitting dead ends, and
maintains a tree of attempted strategies. How do I implement this
with LangGraph?
```

### Résultat Attendu avec Sonnet 4.5

**⏱️ Vitesse:** ~45-50 secondes
**📏 Longueur:** ~5,700+ caractères
**✅ Qualité:** Réponse exhaustive avec :
- Tree-of-Thoughts pattern explanation
- State management code
- Backtracking logic
- Send API pour parallélisation
- BFS vs DFS strategies
- Complete example code
- **Pas de troncature** (crucial!)

### Comparaison GPT-5 Mini (Ancien)
- **Vitesse:** ~160+ secondes (3.3× plus lent)
- **Longueur:** ~3,000 caractères
- **Qualité:** Bonne mais **risque de troncature**

## Grille d'Évaluation

| Critère | Attendu Sonnet 4.5 | Observé | ✅/❌ |
|---------|-------------------|---------|------|
| **Test 1 - Vitesse** | 22-30s | ___ s | ___ |
| **Test 1 - Longueur** | 1,400-1,500 chars | ___ chars | ___ |
| **Test 1 - Complétude** | Classes + exemples + variantes | ___ | ___ |
| **Test 2 - Vitesse** | 35-45s | ___ s | ___ |
| **Test 2 - Longueur** | 3,900-4,200 chars | ___ chars | ___ |
| **Test 2 - Architecture** | Overview + 3 nodes + code | ___ | ___ |
| **Test 3 - Vitesse** | 45-50s | ___ s | ___ |
| **Test 3 - Longueur** | 5,700+ chars | ___ chars | ___ |
| **Test 3 - Pas de troncature** | Réponse complète jusqu'au bout | ___ | ___ |

## Résultats de Benchmark (Référence)

D'après `hero_vs_pragmatic_sonnet45_results.json` :

| Question | Complexité | Temps | Chars | Statut |
|----------|-----------|-------|-------|--------|
| Q1 (PostgreSQL class) | Trivial | 22.4s | 1,440 | ✅ |
| Q2 (Configuration) | Simple | 28.7s | 1,695 | ✅ |
| Q3 (Integration) | Modéré | 35.1s | 3,054 | ✅ |
| Q4 (Debugging) | Modéré-complexe | 39.1s | 4,016 | ✅ |
| Q5 (Architecture) | Complexe | 41.0s | 3,928 | ✅ |
| **Q6 (Planning agent)** | **Ultra-complexe** | **47.1s** | **5,734** | ✅ |

## Expérience Utilisateur Attendue

### Avant (GPT-5 Mini)
```
Question posée → ⏳ Attente 60-120s → Réponse bonne mais basique
→ Parfois besoin de re-questionner pour détails
→ Frustration sur questions complexes (lenteur)
```

### Après (Sonnet 4.5)
```
Question posée → ⏳ Attente 30-45s → Réponse exhaustive immédiatement
→ Rarement besoin de follow-up
→ Satisfaction : vitesse + qualité
```

**Gain de productivité estimé:** 2-3× (vitesse + moins de re-questions)

## Troubleshooting

### Réponse trop lente (>60s)
1. Vérifier backend : `curl http://localhost:2024/ok`
2. Vérifier logs : `docker logs langgraph-backend`
3. Vérifier modèle configuré :
   ```bash
   grep "query_model" backend/retrieval_graph/configuration.py
   # Doit afficher: default="anthropic/claude-sonnet-4-5-20250929"
   ```

### Réponse courte (<1000 chars sur questions complexes)
1. Possible problème de troncature
2. Vérifier version du modèle (doit être `20250929`)
3. Signaler dans monitoring (semaine 1)

### Réponse semble identique à avant
1. Vérifier que le backend a bien redémarré après changement config
2. Relancer : `docker compose restart langgraph`
3. Retester après 30 secondes

## Validation Finale

**Pour confirmer que Sonnet 4.5 est actif :**

✅ **Vitesse** : Questions complexes < 45s (vs ~120s avant)
✅ **Qualité** : Réponses ultra-détaillées (3,000-5,700 chars)
✅ **Complétude** : Pas de troncature sur questions ultra-complexes
✅ **Expérience** : Réponses "wow" dès la première fois

**Si tous ces critères sont remplis → Sonnet 4.5 confirmé ! 🎉**

---

**Date de test:** _______________
**Testeur:** _______________
**Verdict:** ✅ Sonnet 4.5 actif / ❌ Problème détecté

**Notes:**
```


```

**Co-authored-by: Stéphane Wootha Richard <stephane@sawup.fr>**
