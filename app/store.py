import logging
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.models import MUFData, MUFSeries

logger = logging.getLogger(__name__)

# Fenêtre de 60 minutes
WINDOW_MINUTES = 60
STALE_THRESHOLD_SECONDS = 600  # 10 minutes


class MUFStore:
    """
    Stockage en mémoire pour les données MUF avec fenêtre glissante.
    """
    
    def __init__(self):
        self._buffer = deque()
        self._lock = None  # Pour thread-safety si nécessaire
    
    def add_data_point(self, roquetes: Optional[float], arenosillo: Optional[float], 
                      timestamp: datetime) -> None:
        """
        Ajoute un nouveau point de données avec calcul de la moyenne.
        """
        # Calculer la moyenne uniquement si les deux valeurs existent
        avg = None
        if roquetes is not None and arenosillo is not None:
            avg = (roquetes + arenosillo) / 2
        
        # Vérifier si les données sont stale (>10 min)
        now = datetime.now(timezone.utc)
        time_diff = (now - timestamp).total_seconds()
        status = "OK" if time_diff <= STALE_THRESHOLD_SECONDS else "STALE"
        
        data_point = MUFData(
            roquetes=roquetes,
            arenosillo=arenosillo,
            avg=avg,
            ts=timestamp,
            status=status
        )
        
        self._buffer.append(data_point)
        self._cleanup_old_data()
        
        logger.info(f"Données ajoutées: Roquetes={roquetes}, Arenosillo={arenosillo}, Avg={avg}")
        logger.info(f"Taille du buffer après ajout: {len(self._buffer)}")
        logger.info(f"Dernier point: {self._buffer[-1] if self._buffer else 'Aucun'}")
    
    def _cleanup_old_data(self) -> None:
        """
        Supprime les données plus anciennes que la fenêtre.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
        
        while self._buffer and self._buffer[0].ts < cutoff_time:
            self._buffer.popleft()
    
    def get_latest(self) -> Optional[MUFData]:
        """
        Retourne la dernière donnée disponible.
        """
        if not self._buffer:
            logger.info("Buffer vide - retour None")
            return None
            
        latest = self._buffer[-1]
        logger.info(f"Dernière donnée dans le buffer: {latest}")
        
        # Vérifier si les données sont stale
        now = datetime.now(timezone.utc)
        time_diff = (now - latest.ts).total_seconds()
        
        if time_diff > STALE_THRESHOLD_SECONDS:
            latest.status = "STALE"
            logger.info(f"Données marquées comme STALE, délai: {time_diff}s")
        
        return latest
    
    def get_series(self, window_minutes: int = WINDOW_MINUTES) -> MUFSeries:
        """
        Retourne les séries de données pour la fenêtre spécifiée.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        # Filtrer les données dans la fenêtre
        filtered_data = [point for point in self._buffer if point.ts >= cutoff_time]
        
        # Séparer en séries
        timestamps = [point.ts for point in filtered_data]
        roquetes = [point.roquetes for point in filtered_data]
        arenosillo = [point.arenosillo for point in filtered_data]
        avg = [point.avg for point in filtered_data]
        
        return MUFSeries(
            timestamps=timestamps,
            roquetes=roquetes,
            arenosillo=arenosillo,
            avg=avg
        )
    
    def get_window_size(self) -> int:
        """
        Retourne le nombre de points dans la fenêtre actuelle.
        """
        return len(self._buffer)
    
    def clear(self) -> None:
        """
        Vide le buffer (pour tests).
        """
        self._buffer.clear()


# Instance globale du store
muf_store = MUFStore()