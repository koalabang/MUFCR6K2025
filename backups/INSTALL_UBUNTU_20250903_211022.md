# Installation sur Ubuntu 21.10 x64

⚠️ **ATTENTION : Ubuntu 21.10 (Impish) est en fin de vie depuis juillet 2022**

Ce guide détaille l'installation du projet MUF Monitor sur un système Ubuntu 21.10 x64.

**Si vous rencontrez des erreurs 404 lors des mises à jour APT, consultez immédiatement la section "Problème spécifique Ubuntu 21.10" ci-dessous.**

## Prérequis système

### 1. Mise à jour du système
```bash
sudo apt update
sudo apt upgrade -y

# Vérifier les dépôts activés
sudo apt list --upgradable

# Si des paquets sont manquants, activer les dépôts universe
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
```

### ⚠️ Problème spécifique Ubuntu 21.10 (Impish)

**Ubuntu 21.10 est en fin de vie depuis juillet 2022**. Les dépôts officiels ne sont plus disponibles, ce qui cause les erreurs 404 observées.

**Solutions recommandées :**

1. **Mise à niveau vers une version supportée (recommandé)**
   ```bash
   # Vérifier la version actuelle
   lsb_release -a
   
   # Mettre à niveau vers Ubuntu 22.04 LTS
   sudo do-release-upgrade
   ```

2. **Utiliser les archives historiques (temporaire)**
   ```bash
   # Sauvegarder la configuration actuelle
   sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
   
   # Remplacer les dépôts par les archives
   sudo sed -i 's/archive.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
   sudo sed -i 's/security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
   
   # Nettoyer les dépôts Docker en double
   sudo rm -f /etc/apt/sources.list.d/archive_uri-https_download_docker_com_linux_ubuntu-impish.list
   
   # Mettre à jour
   sudo apt update
   ```

3. **Corriger les clés GPG manquantes**
   ```bash
   # Ajouter la clé Docker manquante
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   
   # Reconfigurer le dépôt Docker
   echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu impish stable" | sudo tee /etc/apt/sources.list.d/docker.list
   
   sudo apt update
   ```

### 2. Installation de Python 3.9+ et pip
```bash
# Ubuntu 21.10 inclut Python 3.9 par défaut
sudo apt install -y python3 python3-pip python3-dev

# Si python3-venv n'est pas disponible, utiliser cette alternative :
sudo apt install -y python3-virtualenv
# OU installer venv via pip :
python3 -m pip install --user virtualenv

# Vérifier la version Python
python3 --version
```

### 3. Dépendances système pour la compilation
```bash
sudo apt install -y build-essential curl git
```

### 4. Dépendances optionnelles (recommandées)
```bash
# Installation minimale (paquets de base uniquement)
sudo apt install -y gcc g++ make

# Si vous voulez installer les dépendances de développement :
# Chercher d'abord les paquets disponibles :
apt search libssl | grep dev
apt search libffi | grep dev

# Puis installer selon les résultats trouvés, par exemple :
# sudo apt install -y libssl-dev libffi-dev  # si disponibles
# sudo apt install -y libssl3-dev libffi8-dev  # variantes possibles

# Note : Ces dépendances sont optionnelles pour le fonctionnement de base
```

## Installation du projet

### 1. Cloner le projet
```bash
git clone <url-du-projet>
cd MUFCR6K2025
```

### 2. Créer un environnement virtuel
```bash
# Méthode 1 : avec venv (si disponible)
python3 -m venv venv

# Méthode 2 : avec virtualenv (si venv non disponible)
python3 -m virtualenv venv

# Activer l'environnement virtuel
source venv/bin/activate
```

### 3. Mettre à jour pip
```bash
# Ubuntu 21.10 peut nécessiter une mise à jour de pip
python3 -m pip install --upgrade pip setuptools wheel

# Vérifier la version de pip
pip --version
```

### 4. Installer les dépendances
```bash
# Installation des dépendances Python
pip install -r requirements.txt

# Si des erreurs de compilation apparaissent, installer d'abord :
# sudo apt install -y gcc python3-dev
# puis réessayer l'installation
```

## Configuration pour la production

### 1. Créer un utilisateur système
```bash
sudo useradd -r -s /bin/false mufmonitor
sudo mkdir -p /opt/mufmonitor
sudo chown mufmonitor:mufmonitor /opt/mufmonitor
```

### 2. Copier les fichiers
```bash
sudo cp -r . /opt/mufmonitor/
sudo chown -R mufmonitor:mufmonitor /opt/mufmonitor
```

### 3. Service systemd
Créer le fichier `/etc/systemd/system/mufmonitor.service` :

```ini
[Unit]
Description=MUF Monitor Service
After=network.target

[Service]
Type=simple
User=mufmonitor
Group=mufmonitor
WorkingDirectory=/opt/mufmonitor
Environment=PATH=/opt/mufmonitor/venv/bin
ExecStart=/opt/mufmonitor/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 4. Activer et démarrer le service
```bash
sudo systemctl daemon-reload
sudo systemctl enable mufmonitor
sudo systemctl start mufmonitor
```

### 5. Vérifier le statut
```bash
sudo systemctl status mufmonitor
```

## Configuration du pare-feu

```bash
# UFW (Ubuntu)
sudo ufw allow 8080/tcp

# iptables (si UFW n'est pas utilisé)
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

## Proxy inverse avec Nginx (optionnel)

### 1. Installer Nginx
```bash
sudo apt install -y nginx
```

### 2. Configuration Nginx
Créer `/etc/nginx/sites-available/mufmonitor` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Activer la configuration
```bash
sudo ln -s /etc/nginx/sites-available/mufmonitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Surveillance et logs

### Consulter les logs
```bash
# Logs du service
sudo journalctl -u mufmonitor -f

# Logs Nginx (si utilisé)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitoring des ressources
```bash
# Utilisation CPU/RAM
top -p $(pgrep -f mufmonitor)

# Connexions réseau
sudo netstat -tlnp | grep :8080
```

## Dépannage

### Problèmes spécifiques à Ubuntu 21.10

**⚠️ IMPORTANT :** Si vous rencontrez des erreurs 404 lors de `sudo apt update` ou `sudo add-apt-repository universe`, consultez la section "Problème spécifique Ubuntu 21.10 (Impish)" au début de ce guide.

1. **Package python3-venv non disponible**
   ```bash
   # Solution 1 : Utiliser python3-virtualenv
   sudo apt install -y python3-virtualenv
   python3 -m virtualenv venv
   
   # Solution 2 : Installer via pip
   python3 -m pip install --user virtualenv
   python3 -m virtualenv venv
   ```

2. **Erreur de compilation des dépendances**
   ```bash
   # Installer les outils de développement manquants
   sudo apt install -y build-essential python3-dev
   
   # Essayer ces variantes de noms de paquets :
   sudo apt install -y libffi8-dev libssl3-dev
   sudo apt install -y pkgconf
   
   # Si les paquets ne sont pas trouvés, chercher les alternatives :
   apt search libssl | grep dev
   apt search libffi | grep dev
   apt search cairo | grep dev
   ```

### Problèmes courants

3. **Port déjà utilisé**
   ```bash
   sudo lsof -i :8080
   sudo systemctl stop mufmonitor
   ```

4. **Permissions insuffisantes**
   ```bash
   sudo chown -R mufmonitor:mufmonitor /opt/mufmonitor
   sudo chmod +x /opt/mufmonitor/venv/bin/uvicorn
   ```

5. **Dépendances manquantes**
   ```bash
   source /opt/mufmonitor/venv/bin/activate
   pip install --upgrade -r requirements.txt
   ```

### Test de l'installation
```bash
# Test local
curl http://localhost:8080/health

# Test API
curl http://localhost:8080/api/muf/latest
```

## Mise à jour

```bash
# Arrêter le service
sudo systemctl stop mufmonitor

# Mettre à jour le code
cd /opt/mufmonitor
sudo -u mufmonitor git pull

# Mettre à jour les dépendances
sudo -u mufmonitor /opt/mufmonitor/venv/bin/pip install --upgrade -r requirements.txt

# Redémarrer le service
sudo systemctl start mufmonitor
```

## Sécurité

### Recommandations
- Utiliser HTTPS en production (Let's Encrypt + Nginx)
- Configurer un pare-feu restrictif
- Mettre à jour régulièrement le système
- Surveiller les logs d'accès
- Limiter l'accès SSH

### Sauvegarde
```bash
# Sauvegarder la configuration
sudo tar -czf mufmonitor-backup-$(date +%Y%m%d).tar.gz /opt/mufmonitor
```