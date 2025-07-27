#!/usr/bin/env python3
"""
FICHIER OBSOLÈTE - MIGRATION VERS OLLAMA TERMINÉE

Ce fichier utilisait l'ancienne API OpenAI et a été remplacé par:
- core/assistant_core_production.py (Assistant principal avec Ollama)
- main.py (Point d'entrée simplifié avec Ollama)
- gideon_main_optimized.py (Version complète avec Ollama)

Pour utiliser l'assistant IA personnel avec Ollama:

1. Démarrer Ollama:
   ollama serve

2. Installer les modèles:
   ollama pull mistral:7b
   ollama pull llama3:8b

3. Lancer l'assistant:
   python3 main.py --cli              # Version simple
   python3 gideon_main_optimized.py   # Version complète

MIGRATION COMPLÈTE VERS OLLAMA:
- ✅ Aucune dépendance OpenAI
- ✅ Fonctionne 100% en local
- ✅ Reconnaissance vocale préservée
- ✅ Text-to-Speech préservé
- ✅ Interface graphique disponible
- ✅ Toutes les optimisations maintenues

Ce fichier peut être supprimé en toute sécurité.
"""

import sys

def main():
    print("""
🚀 ASSISTANT IA PERSONNEL - MIGRATION OLLAMA TERMINÉE!

❌ Ce fichier est obsolète et utilisait OpenAI
✅ Nouvelle version 100% locale avec Ollama disponible

NOUVEAUX POINTS D'ENTRÉE:
📁 main.py                     - Version simple et rapide
📁 gideon_main_optimized.py    - Version complète optimisée

COMMANDES DE LANCEMENT:
🔧 python3 main.py --cli
🔧 python3 gideon_main_optimized.py

AVANTAGES DE LA MIGRATION:
🚀 Plus rapide (pas de latence réseau)
🔒 Complètement privé (aucune donnée envoyée)
💾 Fonctionne hors ligne
🆓 Aucun quota ou limite d'API
🧠 Modèles multiples disponibles

Pour continuer, utilisez les nouveaux fichiers!
    """)
    return 0

if __name__ == "__main__":
    sys.exit(main())
