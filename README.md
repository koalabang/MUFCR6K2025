# MUF Monitor - Surveillance des Ionosondes Espagnoles

Application de surveillance en temps réel des données MUF (Maximum Usable Frequency) provenant des stations d'ionosondes espagnoles Roquetes et Arenosillo.

## 🎯 Fonctionnalités

- **Surveillance temps réel** : Récupération automatique des données MUF toutes les 5 minutes
- **Interface web moderne** : Affichage sous forme de bulles colorées avec indicateurs de statut
- **Graphiques interactifs** : Visualisation historique des données avec Pyecharts
- **API REST** : Endpoints pour accéder aux données en JSON
- **Fenêtre glissante** : Conservation des données des 60 dernières minutes
- **Gestion des données obsolètes** : Marquage automatique des données "STALE" après 10 minutes

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation rapide

1. **Cloner le projet** :
```bash
git clone <repository-url>
cd MUFCR6K2025
```

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

3. **Lancer l'application** :
```bash
python -m app.main
```

L'application sera accessible à l'adresse : http://localhost:8080

## 📊 Utilisation

### Interface Web

L'interface principale affiche :
- **Bulles colorées** pour Roquetes et Arenosillo avec les valeurs MUF actuelles
- **Bulle moyenne** avec la moyenne des deux stations
- **Indicateurs de statut** : vert (OK), orange (STALE), rouge (N/A)
- **Graphique historique** montrant l'évolution des 60 dernières minutes

### API REST

#### Dernières données
```bash
curl http://localhost:8080/api/muf/latest
```

#### Série temporelle
```bash
curl http://localhost:8080/api/muf/series
```

#### Mise à jour forcée
```bash
curl -X POST http://localhost:8080/api/muf/refresh
```

#### Santé de l'application
```bash
curl http://localhost:8080/health
```

### Endpoints disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Interface web principale |
| `/chart` | GET | Graphique Pyecharts |
| `/api/muf/latest` | GET | Dernières données MUF |
| `/api/muf/series` | GET | Série temporelle (60 min par défaut) |
| `/api/muf/refresh` | POST | Forcer une mise à jour |
| `/health` | GET | Vérifier l'état de l'application |

## 🏗️ Architecture

### Structure du projet
```
MUFCR6K2025/
├── app/
│   ├── __init__.py
│   ├── main.py          # Application FastAPI avec scheduler
│   ├── fetcher.py       # Récupération des données depuis l'API KC2G
│   ├── store.py         # Stockage en mémoire avec fenêtre glissante
│   ├── models.py        # Modèles de données Pydantic
│   ├── chart.py         # Génération des graphiques Pyecharts
│   └── templates/
│       └── index.html   # Interface web
├── requirements.txt     # Dépendances Python
└── README.md           # Ce fichier
```

### Sources de données

Les données sont récupérées depuis l'API publique de KC2G :
- **Roquetes, Spain** (code : EB040)
- **El Arenosillo, Spain** (code : EA036)

## ⚙️ Configuration

### Variables d'environnement

Aucune variable d'environnement requise. L'application utilise les paramètres par défaut :
- Port : 8080
- Mise à jour : toutes les 5 minutes
- Fenêtre de données : 60 minutes
- Seuil STALE : 10 minutes

### Personnalisation

Pour modifier les paramètres, éditer les fichiers suivants :
- **Fréquence de mise à jour** : `app/main.py` (ligne 45)
- **Fenêtre de données** : `app/store.py` (ligne 11)
- **Seuil STALE** : `app/store.py` (ligne 12)

## 🔧 Développement

### Installation en mode développement

```bash
# Installation avec rechargement automatique
uvicorn app.main:app --reload --port 8080

# Ou avec Python directement
python -m app.main
```

### Tests

```bash
# Vérifier la récupération des données
python debug_stations.py

# Tester l'API
curl http://localhost:8080/api/muf/latest | jq .
```

## 📈 Monitoring

### Logs

L'application génère des logs détaillés incluant :
- Récupération des données
- Mises à jour du store
- État de santé
- Erreurs éventuelles

### Indicateurs de santé

- **Healthy** : L'application fonctionne correctement
- **Data points** : Nombre de points de données stockés
- **STALE** : Données obsolètes (plus de 10 minutes)

## 🐛 Dépannage

### Problèmes courants

1. **ModuleNotFoundError** : Installer les dépendances avec `pip install -r requirements.txt`
2. **Port déjà utilisé** : Changer le port avec `--port 8081`
3. **Données N/A** : Vérifier la connexion internet et l'accessibilité de l'API KC2G

### Vérification rapide

```bash
# Vérifier l'installation
python -c "import app.main; print('Installation OK')"

# Tester l'API externe
curl -s https://prop.kc2g.com/api/stations.json | jq '.[] | select(.name | contains("Spain"))'
```

## 📄 Licence

Projet open-source - disponible sous licence MIT.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## 📞 Support

Pour toute question ou problème, ouvrez une issue sur le dépôt GitHub ou contactez l'équipe de développement.