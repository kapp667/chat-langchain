#!/bin/bash

# Script pour charger les variables d'environnement depuis env.local ou .env

if [ -f "env.local" ]; then
    export $(cat env.local | grep -v '^#' | xargs)
    echo "✅ Variables d'environnement chargées depuis env.local"
elif [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Variables d'environnement chargées depuis .env"
else
    echo "❌ Aucun fichier env.local ou .env trouvé"
    exit 1
fi

# Variables requises selon le README
echo "Vérification des variables requises:"
echo "- OPENAI_API_KEY: $([ ! -z "$OPENAI_API_KEY" ] && echo '✓' || echo '✗')"
echo "- WEAVIATE_URL: $([ ! -z "$WEAVIATE_URL" ] && echo '✓ (optionnel)' || echo '✗ (optionnel)')"
echo "- WEAVIATE_API_KEY: $([ ! -z "$WEAVIATE_API_KEY" ] && echo '✓ (optionnel)' || echo '✗ (optionnel)')"
echo "- RECORD_MANAGER_DB_URL: $([ ! -z "$RECORD_MANAGER_DB_URL" ] && echo '✓ (optionnel)' || echo '✗ (optionnel)')"

# Pour une config locale minimale, on peut utiliser SQLite
if [ -z "$RECORD_MANAGER_DB_URL" ]; then
    export RECORD_MANAGER_DB_URL="sqlite:///record_manager.db"
    echo "📝 Utilisation de SQLite par défaut pour RECORD_MANAGER_DB_URL"
fi

if [ -z "$WEAVIATE_URL" ]; then
    echo "⚠️  WEAVIATE_URL non défini - vous devrez peut-être configurer un vector store local"
fi

echo ""
echo "Pour lancer le backend: make start"
echo "Pour lancer le frontend: cd frontend && yarn dev"