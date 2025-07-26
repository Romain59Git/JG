# 🤖 Gideon AI Assistant - Version Optimisée

Un assistant IA personnel futuriste inspiré de Gideon de la série Flash, avec reconnaissance vocale, faciale et interface overlay transparente.

## ✨ Fonctionnalités

### 🎤 Audio Intelligent
- **Reconnaissance vocale** optimisée avec timeouts intelligents
- **Text-to-Speech** naturel
- **Écoute continue** avec pauses automatiques
- **Détection microphone** automatique (macOS optimisé)

### 🔍 Vision Artificielle
- **Authentification faciale** avec MTCNN + TensorFlow
- **Détection visage** temps réel
- **Interface camera** non intrusive

### 🧠 Intelligence Artificielle
- **OpenAI GPT-3.5 Turbo** intégré
- **Réponses contextuelles** rapides
- **Fallbacks intelligents** si API indisponible

### 💾 Performance Optimisée
- **Monitoring mémoire** temps réel (< 300MB cible)
- **Garbage collection** agressif
- **Timeouts intelligents** (3s max écoute)
- **Sample rate optimisé** (16kHz au lieu de 44kHz)

### 🖥️ Interface Moderne
- **Debug Panel PyQt6** avec contrôles temps réel
- **Overlay transparent** (mode futur)
- **System tray** intégré
- **Indicateurs visuels** status système

## 🚀 Installation Rapide

### Prérequis
- **macOS** (optimisé pour macOS, compatible Linux/Windows)
- **Python 3.9+**
- **Homebrew** (pour macOS)

### Installation Automatique
```bash
# 1. Cloner le repository
git clone https://github.com/Romain59Git/JG.git
cd JG

# 2. Rendre exécutable et lancer l'installation
chmod +x install_system_production.sh
./install_system_production.sh

# 3. Activer l'environnement virtuel
source venv_gideon_production/bin/activate

# 4. Tester le système audio
python test_audio_system.py

# 5. Lancer Gideon AI Optimisé
python gideon_main_optimized.py
```

## 🎛️ Interface de Contrôle

Gideon AI inclut un **Debug Panel** en temps réel avec :

- 🎤 **Audio Status** : ON/OFF + Test Microphone
- 💾 **Memory Monitor** : Usage temps réel avec barre de progression
- 🔗 **OpenAI Status** : État connexion API
- 📊 **Performance Stats** : Statistiques d'écoute et succès
- 🔧 **Debug Mode** : Logs détaillés
- 🧹 **Clean RAM** : Nettoyage mémoire manuel

## 📊 Tests et Validation

### Suite de Tests Automatique
```bash
python test_audio_system.py
```

**Résultats attendus :**
- ✅ Speech Recognition Available
- ✅ Microphone Available  
- ✅ TTS Engine Available
- ✅ Continuous Listening
- ✅ Performance Metrics
- **Score global : 87.5%+ = système prêt**

### Tests Manuels
1. **Test Microphone** : Bouton dans Debug Panel
2. **Test Reconnaissance** : Dire "Hello Gideon"
3. **Test TTS** : Réponse vocale automatique
4. **Test Mémoire** : Surveillance < 300MB

## ⚙️ Configuration

### Variables d'Environnement
```bash
# Clé API OpenAI (optionnel si dans config.py)
export OPENAI_API_KEY="your-api-key-here"

# Mode debug (optionnel)
export GIDEON_DEBUG="true"
```

### Fichier config.py
Les paramètres sont configurables dans `config.py` :
- **API OpenAI** : Clé et modèle
- **Audio** : Sample rate, timeouts, langue
- **Mémoire** : Seuils d'alerte et nettoyage
- **Interface** : Couleurs et animations

## 🔧 Architecture

```
Gideon AI/
├── core/
│   ├── audio_manager_optimized.py    # Gestionnaire audio intelligent
│   ├── memory_monitor.py             # Surveillance mémoire
│   ├── assistant_core_production.py  # Logique IA principale
│   ├── event_system.py               # Système d'événements
│   └── logger.py                     # Logs structurés
├── ui/
│   ├── overlay.py                    # Interface overlay
│   └── widgets.py                    # Composants UI
├── gideon_main_optimized.py          # Application principale optimisée
├── test_audio_system.py              # Tests automatiques
├── config.py                         # Configuration centralisée
└── requirements_production.txt       # Dépendances verrouillées
```

## 📈 Performance

### Métriques Optimisées
- **Mémoire au repos** : ~50MB
- **Mémoire avec ML** : ~500MB (MTCNN + TensorFlow)
- **Temps de réponse audio** : < 3 secondes
- **Latence TTS** : < 1 seconde
- **CPU idle** : < 5%

### Optimisations Implémentées
- Sample rate réduit : 44100Hz → 16000Hz (-65% mémoire audio)
- Garbage collection agressif : (700, 10, 10)
- Timeouts intelligents et progressifs
- Monitoring continu avec alertes automatiques
- Fallbacks gracieux pour tous composants

## 🐛 Troubleshooting

### Erreurs Communes

**Speech Recognition non fonctionnel :**
```bash
# Installer PyAudio manuellement
pip install pyaudio
```

**Mémoire élevée :**
- Utiliser le bouton "Clean RAM" du Debug Panel
- Désactiver face detection si non nécessaire

**OpenAI API errors :**
- Vérifier la clé API dans `config.py`
- Tester la connectivité internet

**Microphone non détecté :**
- Vérifier permissions macOS (Sécurité > Microphone)
- Utiliser "Test Mic" pour diagnostic

### Logs de Debug
```bash
# Activer mode debug via interface ou :
export GIDEON_DEBUG="true"
python gideon_main_optimized.py
```

## 🚀 Modes d'Utilisation

### Mode Production (Recommandé)
```bash
python gideon_main_optimized.py
```
- Interface debug intégrée
- Monitoring temps réel
- Performance optimisée

### Mode Console (Fallback)
Si PyQt6 indisponible, Gideon bascule automatiquement en mode console avec toutes les fonctionnalités audio.

### Mode Léger (< 150MB)
Pour utilisation avec mémoire limitée, désactiver face detection dans `config.py`.

## 🤝 Contribution

Ce projet utilise :
- **OpenAI GPT-3.5** pour l'intelligence artificielle
- **MTCNN + TensorFlow** pour la détection faciale  
- **SpeechRecognition + PyTTSx3** pour l'audio
- **PyQt6** pour l'interface graphique
- **sounddevice** pour l'audio optimisé

## 📄 Licence

MIT License - Voir fichier LICENSE pour détails.

## 🔗 Liens Utiles

- [Documentation OpenAI](https://platform.openai.com/docs)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)
- [MTCNN Face Detection](https://github.com/ipazc/mtcnn)

---

**🎉 Gideon AI Assistant - L'IA personnelle du futur, disponible aujourd'hui !** 