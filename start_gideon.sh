#!/bin/bash
# Gideon AI - Script de démarrage optimisé

echo "🚀 Démarrage Gideon AI..."

# Activer environnement virtuel
if [ -d "venv_gideon_production" ]; then
    source venv_gideon_production/bin/activate
    echo "✅ Environnement virtuel activé"
else
    echo "⚠️ Environnement virtuel non trouvé"
fi

# Vérifier variable OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ Variable OPENAI_API_KEY non définie"
    echo "💡 Export recommandé: export OPENAI_API_KEY='your-key-here'"
fi

# Lancer Gideon optimisé
echo "🤖 Lancement Gideon AI Optimisé..."
python3 gideon_main_optimized.py

echo "👋 Gideon AI arrêté"
