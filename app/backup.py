import os
import shutil
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupHandler(FileSystemEventHandler):
    """Gestionnaire d'événements pour la sauvegarde automatique des fichiers."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Extensions de fichiers à surveiller
        self.watched_extensions = {'.py', '.html', '.css', '.js', '.json', '.txt', '.md'}
        
        # Dossiers à ignorer
        self.ignored_dirs = {'__pycache__', '.git', 'node_modules', 'backups'}
    
    def should_backup(self, file_path: str) -> bool:
        """Détermine si un fichier doit être sauvegardé."""
        path = Path(file_path)
        
        # Ignorer les dossiers spécifiques
        if any(ignored in path.parts for ignored in self.ignored_dirs):
            return False
        
        # Vérifier l'extension
        return path.suffix.lower() in self.watched_extensions
    
    def create_backup(self, file_path: str):
        """Crée une sauvegarde du fichier modifié."""
        try:
            source_path = Path(file_path)
            if not source_path.exists() or not self.should_backup(file_path):
                return
            
            # Créer le nom de fichier de sauvegarde avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
            # Créer la structure de dossiers dans le répertoire de sauvegarde
            relative_path = source_path.relative_to(Path.cwd())
            backup_subdir = self.backup_dir / relative_path.parent
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            # Chemin complet de la sauvegarde
            backup_path = backup_subdir / backup_name
            
            # Copier le fichier
            shutil.copy2(source_path, backup_path)
            logger.info(f"Sauvegarde créée: {backup_path}")
            
            # Nettoyer les anciennes sauvegardes (garder les 10 dernières)
            self.cleanup_old_backups(backup_subdir, source_path.name)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {file_path}: {e}")
    
    def cleanup_old_backups(self, backup_dir: Path, original_filename: str):
        """Supprime les anciennes sauvegardes, garde les 10 plus récentes."""
        try:
            # Trouver tous les fichiers de sauvegarde pour ce fichier
            base_name = Path(original_filename).stem
            pattern = f"{base_name}_*{Path(original_filename).suffix}"
            
            backup_files = list(backup_dir.glob(pattern))
            
            # Trier par date de modification (plus récent en premier)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Supprimer les fichiers au-delà des 10 plus récents
            for old_backup in backup_files[10:]:
                old_backup.unlink()
                logger.info(f"Ancienne sauvegarde supprimée: {old_backup}")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des sauvegardes: {e}")
    
    def on_modified(self, event):
        """Appelé quand un fichier est modifié."""
        if not event.is_directory:
            self.create_backup(event.src_path)
    
    def on_created(self, event):
        """Appelé quand un fichier est créé."""
        if not event.is_directory:
            self.create_backup(event.src_path)

class BackupManager:
    """Gestionnaire principal du système de sauvegarde."""
    
    def __init__(self, watch_path: str = ".", backup_dir: str = "backups"):
        self.watch_path = Path(watch_path)
        self.backup_dir = backup_dir
        self.observer = Observer()
        self.handler = BackupHandler(backup_dir)
    
    def start(self):
        """Démarre la surveillance des fichiers."""
        try:
            self.observer.schedule(self.handler, str(self.watch_path), recursive=True)
            self.observer.start()
            logger.info(f"Système de sauvegarde démarré - Surveillance: {self.watch_path}")
            logger.info(f"Répertoire de sauvegarde: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du système de sauvegarde: {e}")
    
    def stop(self):
        """Arrête la surveillance des fichiers."""
        try:
            self.observer.stop()
            self.observer.join()
            logger.info("Système de sauvegarde arrêté")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du système de sauvegarde: {e}")
    
    def create_manual_backup(self, file_path: str):
        """Crée une sauvegarde manuelle d'un fichier spécifique."""
        self.handler.create_backup(file_path)
    
    def get_backup_info(self) -> dict:
        """Retourne des informations sur les sauvegardes."""
        backup_path = Path(self.backup_dir)
        if not backup_path.exists():
            return {"total_backups": 0, "backup_size": 0}
        
        total_files = sum(1 for _ in backup_path.rglob("*") if _.is_file())
        total_size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
        
        return {
            "total_backups": total_files,
            "backup_size": total_size,
            "backup_size_mb": round(total_size / (1024 * 1024), 2)
        }

# Instance globale du gestionnaire de sauvegarde
backup_manager = None

def init_backup_system(watch_path: str = ".", backup_dir: str = "backups"):
    """Initialise le système de sauvegarde."""
    global backup_manager
    backup_manager = BackupManager(watch_path, backup_dir)
    return backup_manager

def start_backup_system():
    """Démarre le système de sauvegarde."""
    global backup_manager
    if backup_manager:
        backup_manager.start()

def stop_backup_system():
    """Arrête le système de sauvegarde."""
    global backup_manager
    if backup_manager:
        backup_manager.stop()

def get_backup_status() -> dict:
    """Retourne le statut du système de sauvegarde."""
    global backup_manager
    if backup_manager:
        return backup_manager.get_backup_info()
    return {"error": "Système de sauvegarde non initialisé"}