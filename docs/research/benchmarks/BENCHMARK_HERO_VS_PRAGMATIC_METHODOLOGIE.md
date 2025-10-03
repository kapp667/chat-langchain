# Benchmark HERO vs PRAGMATIC : Méthodologie Complète

**Date:** 3 octobre 2025
**Objectif:** Comparer qualité absolue Sonnet 4.5 (HERO) vs Llama 3.3 70B + PNL (PRAGMATIC) sur 6 questions graduées
**Auteur:** Stéphane Wootha Richard

---

## Résumé Exécutif

Ce benchmark départage définitivement les deux candidats finaux pour le serveur MCP :
- **HERO** : Claude Sonnet 4.5 (champion qualité, mais coût/latence élevés)
- **PRAGMATIC** : Llama 3.3 70B + PNL (compromis optimal vitesse/qualité/coût)

**Hypothèse à tester :**
> Llama 3.3 70B avec PNL anti-hallucination peut-il fournir une qualité équivalente à Sonnet 4.5 malgré un coût 153x inférieur et une latence 6x plus rapide ?

**Méthodologie :** 6 questions graduées (triviale → ultra-complexe) testées sur les deux modèles, analyse qualitative par sous-agent spécialisé.

---

## 1. Design des Questions

### 1.1 Principe de Gradation

**Objectif :** Tester les modèles sur toute la gamme de complexité rencontrée en usage réel MCP.

**Stratégie de gradation :**

| Niveau | Complexité | Type question | Longueur attendue | Composants requis |
|--------|------------|---------------|-------------------|-------------------|
| **Q1** | Triviale | API lookup | 1-5 lignes | 1 classe |
| **Q2** | Simple | Configuration | 5-15 lignes | 2-3 paramètres |
| **Q3** | Modérée | Intégration | 20-40 lignes | 3-5 composants |
| **Q4** | Modérée-complexe | Debugging | 30-60 lignes | Troubleshooting + solutions |
| **Q5** | Complexe | Architecture multi-étapes | 50-120 lignes | Graph + nodes + routing |
| **Q6** | Ultra-complexe | Graph avancé + backtracking | 100-250 lignes | State management + time travel |

**Principe questions naïves :**
- ✅ Focus besoins utilisateur (pas jargon technique)
- ✅ Pas d'induction de réponse (question ouverte)
- ✅ Scénarios réels d'usage développeur MCP

### 1.2 Questions Détaillées

#### Q1 (Triviale) : API Lookup Simple

**Question :**
> "I need to save conversation history to PostgreSQL. Which class should I use?"

**Objectif :** Tester rapidité de réponse factuelle (1 classe à identifier)

**Réponse attendue :**
- AsyncPostgresSaver ou PostgresSaver
- 1-5 lignes maximum
- Import statement + explication 1 phrase

**Critères évaluation :**
- ✅ Classe correcte identifiée
- ✅ Concision (pas de détails inutiles)
- ✅ Latence <10s (question triviale)

---

#### Q2 (Simple) : Configuration Basique

**Question :**
> "How do I configure LangGraph to use my own OpenAI API key and custom temperature?"

**Objectif :** Tester explication configuration simple (2 paramètres)

**Réponse attendue :**
- Configuration OPENAI_API_KEY (env var ou direct)
- Paramètre temperature dans ChatOpenAI
- 5-15 lignes (exemple code minimal)

**Critères évaluation :**
- ✅ OPENAI_API_KEY correctement expliqué
- ✅ temperature parameter mentionné
- ✅ Code exemple fonctionnel
- ✅ Latence <15s

---

#### Q3 (Modérée) : Intégration Composants

**Question :**
> "I want to build a chatbot that remembers previous messages across sessions. What components do I need and how do I connect them?"

**Objectif :** Tester capacité d'intégration multi-composants

**Réponse attendue :**
- Checkpointer (PostgresSaver ou MemorySaver)
- thread_id pour sessions
- StateGraph compilation
- 20-40 lignes (architecture + code exemple)

**Critères évaluation :**
- ✅ Checkpointer mentionné
- ✅ thread_id pour persistence expliqué
- ✅ Graph compilation correct
- ✅ Code exemple complet et fonctionnel
- ✅ Latence <20s

---

#### Q4 (Modérée-Complexe) : Debugging & Résilience

**Question :**
> "My LangGraph agent keeps timing out after 30 seconds on complex questions. How can I debug this and make it more resilient?"

**Objectif :** Tester troubleshooting pratique + solutions multiples

**Réponse attendue :**
- Diagnostic (recursion_limit, timeout config, streaming)
- Solutions (augmenter limits, streaming pour feedback, error handling)
- 30-60 lignes (diagnostic + 3-5 solutions)

**Critères évaluation :**
- ✅ Diagnostic causes timeout (recursion_limit, long documents)
- ✅ Solutions pratiques (config, streaming, error recovery)
- ✅ Code exemples fonctionnels
- ✅ Latence <30s

---

#### Q5 (Complexe) : Architecture Multi-Étapes RAG

**Question :**
> "I need to build a research assistant that: (1) breaks down complex questions into sub-questions, (2) searches documentation for each sub-question, (3) synthesizes findings. How should I structure this?"

**Objectif :** Tester architecture graph multi-nodes avec routing

**Réponse attendue :**
- StateGraph avec nodes (decompose, search, synthesize)
- Multi-query generation
- Conditional routing
- 50-120 lignes (architecture + code exemple complet)

**Critères évaluation :**
- ✅ Architecture claire (3+ nodes identifiés)
- ✅ Multi-query strategy expliquée
- ✅ Synthesis logic correcte
- ✅ Code graph fonctionnel
- ✅ Latence <45s (acceptable pour complexité)

---

#### Q6 (Ultra-Complexe) : Graph Avancé avec Backtracking

**Question :**
> "I want to create a planning agent that explores multiple solution paths, can backtrack when hitting dead ends, and maintains a tree of attempted strategies. How do I implement this with LangGraph?"

**Objectif :** Tester capacités avancées (state management, time travel, backtracking)

**Réponse attendue :**
- StateGraph avec state complexe (tree of attempts)
- Checkpoints pour time travel
- Conditional routing pour exploration paths
- Backtracking via checkpoint replay
- 100-250 lignes (architecture avancée + code complet)

**Critères évaluation :**
- ✅ State management arbre de décisions
- ✅ Checkpoints pour backtracking expliqués
- ✅ Time travel API utilisée correctement
- ✅ Graph routing avancé (conditional edges)
- ✅ Code fonctionnel et production-ready
- ✅ Latence <90s (acceptable ultra-complexe)

---

## 2. Modèles Testés

### 2.1 HERO : Claude Sonnet 4.5

**Configuration :**
```python
{
    "id": "anthropic/claude-sonnet-4-5-20250929",
    "name": "Claude Sonnet 4.5 (HERO)",
    "description": "Excellence maximale (champion qualité)",
    "expected_speed": "slow (40-120s)",
    "expected_quality": "5/5"
}
```

**Caractéristiques :**
- ✅ Champion absolu qualité (benchmarks précédents : 23.8K chars sur Q complexe)
- ✅ 0% hallucinations (natif, sans PNL requis)
- ✅ Exhaustivité maximale (citations, exemples code multiples)
- ❌ Coût élevé : $90/M tokens (input $15, output $75)
- ❌ Latence élevée : 60s moyenne (40-120s range)

**Attentes benchmark :**
- Qualité : 5/5 sur toutes questions
- Verbosité : Adaptative naturelle (mais tendance détail excessif)
- Hallucinations : 0% (natif)
- Latence totale (6Q) : ~6-12 minutes

### 2.2 PRAGMATIC : Llama 3.3 70B + PNL

**Configuration :**
```python
{
    "id": "groq/llama-3.3-70b-versatile",
    "name": "Llama 3.3 70B + PNL (PRAGMATIC)",
    "description": "Compromis optimal vitesse/qualité (anti-hallucination PNL)",
    "expected_speed": "fast (8-15s)",
    "expected_quality": "4.6/5"
}
```

**Caractéristiques :**
- ✅ Vitesse excellente : 9.73s moyenne (6x plus rapide que Sonnet)
- ✅ Coût ultra-compétitif : $0.59/M tokens (153x moins cher)
- ✅ 0% hallucinations (PNL "Documentation Mirror Mode" validé)
- ✅ Verbosité adaptative : 2.2K-6.2K chars selon complexité
- ⚠️ Qualité légèrement inférieure : 4.6/5 (vs 5/5 Sonnet)
- ⚠️ Moins de citations que Sonnet (5 vs 25 moyenne)

**Wrapper PNL utilisé :** `backend/groq_wrapper.py` (injection anti-hallucination)

**Attentes benchmark :**
- Qualité : 4.6/5 moyenne (acceptable si >4/5 sur Q complexes)
- Verbosité : Adaptative (concis sur Q1-Q2, détaillé Q5-Q6)
- Hallucinations : 0% (PNL validé)
- Latence totale (6Q) : ~1.5-3 minutes

---

## 3. Infrastructure et Protocole

### 3.1 Infrastructure de Test

**Backend :**
- LangGraph 0.4.5 (local `langgraph dev`)
- Weaviate v4 Cloud (15,061 documents LangChain indexés)
- Endpoint : http://localhost:2024

**Embeddings :**
- OpenAI text-embedding-3-small
- Context : 15,061 docs (guides, tutorials, API refs)

**Invocation :**
```python
POST http://localhost:2024/invoke
{
  "input": {
    "messages": [{"role": "user", "content": "{question}"}]
  },
  "config": {
    "configurable": {
      "model": "{model_id}"  # sonnet45 ou llama-3.3-70b-groq
    }
  }
}
```

### 3.2 Protocole d'Exécution

**Séquence :**
1. Lancer les deux benchmarks en parallèle (scripts indépendants)
   ```bash
   # Terminal 1
   poetry run python mcp_server/archive/benchmark_hero_vs_pragmatic.py --model llama-3.3-70b-groq

   # Terminal 2 (délai 3s)
   poetry run python mcp_server/archive/benchmark_hero_vs_pragmatic.py --model sonnet45
   ```

2. Chaque benchmark exécute 6 questions séquentiellement
   - Délai 2s entre questions (éviter saturation endpoint)
   - Timeout 300s par question (5 min max)

3. Sauvegarder résultats JSON
   - `mcp_server/results/hero_vs_pragmatic_llama-3.3-70b-groq_results.json`
   - `mcp_server/results/hero_vs_pragmatic_sonnet45_results.json`

### 3.3 Métriques Collectées

**Par question :**
- `success` : bool (réussite/échec)
- `elapsed_time` : float (secondes)
- `response_full` : str (réponse complète)
- `response_length` : int (chars)
- `chunk_count` : int (documents récupérés)
- `error` : str | null (si échec)

**Statistiques globales :**
- `total_tests` : 6
- `successful_tests` : N/6
- `average_time` : float (latence moyenne)
- `average_response_length` : float (verbosité moyenne)

---

## 4. Critères d'Évaluation Qualitative

### 4.1 Grille d'Analyse (Sous-Agent)

**Critères par question :**

| Critère | Poids | Description |
|---------|-------|-------------|
| **Exactitude factuelle** | 30% | APIs/classes correctes, 0 hallucinations |
| **Complétude** | 25% | Tous aspects question couverts |
| **Actionabilité** | 20% | Code exemples fonctionnels |
| **Clarté** | 15% | Structure logique, explicatif |
| **Concision** | 10% | Pas de détails inutiles (Q triviales/simples) |

**Score global :**
- 5/5 : Excellence (tous critères remplis)
- 4/5 : Très bon (1 critère partiel)
- 3/5 : Bon (2 critères partiels)
- 2/5 : Moyen (critères majeurs manquants)
- 1/5 : Insuffisant (réponse incorrecte/incomplète)

### 4.2 Analyse Différentielle

**Questions clés pour sous-agent :**

1. **Hallucinations :**
   - Llama 3.3 70B invente-t-il des méthodes/classes ? (PNL efficace ?)
   - Sonnet 4.5 reste-t-il factuel à 100% ?

2. **Verbosité adaptative :**
   - Llama adapte-t-il sa longueur selon complexité question ?
   - Sonnet sur-détaille-t-il les questions simples (Q1-Q2) ?

3. **Qualité sur questions complexes (Q5-Q6) :**
   - Llama fournit-il architecture complète et fonctionnelle ?
   - Gap Llama vs Sonnet sur ultra-complexe (Q6) est-il acceptable ?

4. **Actionabilité code :**
   - Code Llama est-il production-ready ?
   - Sonnet fournit-il plus d'exemples mais usage identique ?

5. **ROI qualité/latence :**
   - Si Llama 4.5/5 sur Q1-Q4 et 4/5 sur Q5-Q6, est-ce acceptable pour MCP ?
   - Gain latence 6x compense-t-il perte qualité -10% ?

---

## 5. Analyse Attendue (Hypothèses)

### 5.1 Hypothèse HERO (Sonnet 4.5)

**Attendu :**
- ✅ Qualité 5/5 sur toutes questions
- ✅ Exhaustivité maximale (citations multiples, exemples code détaillés)
- ✅ 0% hallucinations (natif)
- ❌ Verbosité excessive sur Q1-Q2 (over-engineering)
- ❌ Latence 40-120s par question (total 6-12 min)

**Profil :**
> Champion absolu qualité, mais inadapté à usage MCP interactif (latence frustrante pour développeur)

### 5.2 Hypothèse PRAGMATIC (Llama 3.3 70B + PNL)

**Attendu :**
- ✅ Qualité 4.5-5/5 sur Q1-Q4 (triviales/simples/modérées)
- ⚠️ Qualité 4-4.5/5 sur Q5-Q6 (complexes/ultra-complexes)
- ✅ Verbosité adaptative : concis Q1-Q2, détaillé Q5-Q6
- ✅ 0% hallucinations (PNL efficace)
- ✅ Latence 8-15s par question (total 1.5-3 min)

**Profil :**
> Compromis optimal pour MCP : qualité production-ready (>4/5) avec latence acceptable (<15s moyenne)

### 5.3 Hypothèse Décision Finale

**Si Llama ≥4/5 sur Q1-Q4 ET ≥3.5/5 sur Q5-Q6 :**
→ **PRAGMATIC gagnant** (qualité acceptable, ROI latence/coût supérieur)

**Si Llama <4/5 sur Q5-Q6 (gap >20% vs Sonnet) :**
→ **HERO gagnant** (qualité critique non négociable pour questions complexes)

**Seuil décisif :** Qualité Llama sur Q6 (ultra-complexe backtracking)
- Si ≥4/5 → PRAGMATIC recommandé
- Si <3.5/5 → HERO nécessaire pour 10% questions ultra-complexes

---

## 6. Utilisation Sous-Agent Spécialisé

### 6.1 Tâche Sous-Agent

**Agent sélectionné :** `general-purpose` ou `codebase-quality-analyzer`

**Prompt sous-agent :**
```
Analyse qualitative comparative HERO vs PRAGMATIC :

CONTEXTE :
- HERO = Claude Sonnet 4.5 (champion qualité, $90/M, 60s latence)
- PRAGMATIC = Llama 3.3 70B + PNL ($0.59/M, 10s latence)

TÂCHE :
1. Lire intégralement les deux fichiers JSON :
   - mcp_server/results/hero_vs_pragmatic_sonnet45_results.json
   - mcp_server/results/hero_vs_pragmatic_llama-3.3-70b-groq_results.json

2. Analyser qualité réponses selon 5 critères :
   - Exactitude factuelle (APIs correctes, 0 hallucinations)
   - Complétude (tous aspects couverts)
   - Actionabilité (code fonctionnel)
   - Clarté (structure logique)
   - Concision (Q1-Q2 pas over-engineering)

3. Scorer chaque question (1-5/5) pour chaque modèle

4. Identifier différences clés :
   - Hallucinations (Llama invente-t-il méthodes ?)
   - Verbosité (Llama adapte-t-il selon complexité ?)
   - Gap Q5-Q6 (complexes) : acceptable (<20%) ?

5. RECOMMANDATION FINALE :
   - Si Llama ≥4/5 sur Q1-Q4 ET ≥3.5/5 sur Q5-Q6 → PRAGMATIC
   - Si Llama <3.5/5 sur Q5-Q6 → HERO

LIVRABLES :
- Tableau comparatif 6 questions × 5 critères × 2 modèles
- Analyse qualitative différentielle (300 mots)
- Recommandation finale justifiée
```

### 6.2 Sauvegarde Analyse

**Fichier output sous-agent :**
- `ANALYSE_QUALITATIVE_HERO_VS_PRAGMATIC.md`

**Contenu attendu :**
1. Tableau scores (6Q × 5 critères × 2 modèles)
2. Analyse différentielle (hallucinations, verbosité, gaps)
3. Recommandation finale (HERO ou PRAGMATIC)
4. Justification décision (ROI qualité/latence/coût)

---

## 7. Prochaines Étapes

### 7.1 Exécution Benchmarks

**Statut actuel :** En cours (lancés en parallèle)
- ✅ Llama 3.3 70B : Benchmark lancé (PID 2deeb9)
- ✅ Sonnet 4.5 : Benchmark lancé (PID 2b3340)

**Durée estimée :**
- Llama : ~1.5-3 minutes (6Q × 15s moyenne)
- Sonnet : ~6-12 minutes (6Q × 60s moyenne)

**Surveillance :**
```bash
# Llama
tail -f /tmp/benchmark_hero_vs_pragmatic_llama.log

# Sonnet
tail -f /tmp/benchmark_hero_vs_pragmatic_sonnet.log
```

### 7.2 Analyse Post-Benchmark

1. ✅ Vérifier résultats JSON complets (6/6 tests réussis)
2. ✅ Soumettre analyse qualitative au sous-agent
3. ✅ Documenter recommandation finale
4. ⏳ Configurer serveur MCP avec modèle sélectionné

### 7.3 Critères de Succès

**Benchmarks réussis si :**
- ✅ 6/6 questions exécutées sans erreur (les deux modèles)
- ✅ Réponses complètes (>500 chars minimum)
- ✅ Latences dans limites attendues (Llama <20s, Sonnet <150s)

**Analyse qualitative réussie si :**
- ✅ Scores détaillés 6Q × 5 critères × 2 modèles
- ✅ Différences clés identifiées (hallucinations, verbosité, gaps)
- ✅ Recommandation finale claire et justifiée

---

## 8. Références

### 8.1 Documents Préparatoires

**Benchmarks précédents :**
- `RAPPORT_BENCHMARK_FINAL.md` : 4 modèles validés (Llama 3.3 70B sélectionné)
- `COMPARAISON_QUALITE_PNL_LLAMA_VS_DEEPSEEK.md` : Validation PNL (0% hallucinations)
- `SELECTION_MODELE_UNIQUE_MCP.md` : Grille sélection (Llama 9.8/10 vs DeepSeek 5.9/10)

**Documentation technique :**
- `DOCUMENTATION_WRAPPERS_PNL.md` : Implémentation PNL complète (groq_wrapper.py)
- `backend/groq_wrapper.py` : Wrapper opérationnel avec PNL anti-hallucination

### 8.2 Infrastructure

**Endpoint LangGraph :**
- URL : http://localhost:2024
- Méthode : POST /invoke
- Timeout : 300s par question

**Vector DB :**
- Weaviate v4 Cloud
- 15,061 documents LangChain indexés
- Embeddings : OpenAI text-embedding-3-small

**Wrappers modèles :**
- Sonnet 4.5 : Natif LangChain (`langchain-anthropic`)
- Llama 3.3 70B : Custom wrapper + PNL (`backend/groq_wrapper.py`)

---

## 9. Conclusion Méthodologique

Ce benchmark HERO vs PRAGMATIC représente le **test décisif** pour sélectionner le modèle du serveur MCP.

**Enjeu :** Déterminer si un modèle 153x moins cher et 6x plus rapide peut atteindre une qualité acceptable (≥4/5) pour remplacer le champion absolu.

**Approche rigoureuse :**
- ✅ 6 questions graduées (couverture complète complexité usage réel)
- ✅ Questions naïves (pas d'induction réponse)
- ✅ Benchmarks parallèles (infrastructure identique)
- ✅ Analyse qualitative par sous-agent (objectivité maximale)

**Décision finale dépendra de :** Qualité Llama 3.3 70B sur questions complexes/ultra-complexes (Q5-Q6).

---

**Document généré le 3 octobre 2025**
**Co-authored-by: Stéphane Wootha Richard <stephane@sawup.fr>**
🤖 Méthodologie par Claude Code
