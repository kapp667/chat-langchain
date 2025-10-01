#!/bin/bash
# Script de mise à jour des prompts depuis LangSmith Hub
# Usage: ./update_prompts.sh
# Nécessite: LANGCHAIN_API_KEY dans l'environnement ou .env

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Vérifier que l'API key est disponible
if [ -z "$LANGCHAIN_API_KEY" ]; then
  # Essayer de charger depuis .env du projet
  if [ -f "../../.env" ]; then
    export $(grep LANGCHAIN_API_KEY ../../.env | xargs)
  fi
fi

if [ -z "$LANGCHAIN_API_KEY" ]; then
  echo "❌ Erreur: LANGCHAIN_API_KEY non définie"
  echo "   Exporter la variable ou l'ajouter au fichier .env"
  exit 1
fi

echo "🔄 Mise à jour des prompts depuis LangSmith Hub..."
echo ""

# Liste des prompts à récupérer
PROMPTS=(
  "router"
  "generate-queries"
  "more-info"
  "research-plan"
  "general"
  "response"
)

for prompt in "${PROMPTS[@]}"; do
  echo "📥 Récupération: chat-langchain-${prompt}-prompt"

  # Récupérer le prompt via API
  response=$(curl -s -H "x-api-key: ${LANGCHAIN_API_KEY}" \
    "https://api.smith.langchain.com/commits/langchain-ai/chat-langchain-${prompt}-prompt/latest")

  # Extraire le template
  template=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['manifest']['kwargs']['messages'][0]['kwargs']['prompt']['kwargs']['template'])")

  # Nom du fichier (remplacer - par _)
  filename="${prompt//-/_}.txt"

  # Sauvegarder
  echo "$template" > "$filename"

  echo "   ✓ Sauvegardé: $filename ($(wc -c < "$filename" | xargs) octets)"
  echo ""
done

echo "✅ Tous les prompts ont été mis à jour avec succès"
echo ""
echo "📝 N'oubliez pas de:"
echo "   1. Vérifier les modifications: git diff backend/prompts_static/"
echo "   2. Créer un commit: git add backend/prompts_static/ && git commit -m 'chore: update prompts from LangSmith Hub'"
