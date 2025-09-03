import httpx
import re
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from app.models import StationData

logger = logging.getLogger(__name__)

# Configuration
API_URL = "https://prop.kc2g.com/api/stations.json"
TIMEOUT = 5  # seconds
MAX_RETRIES = 3
RETRY_DELAYS = [0.5, 1, 2]  # seconds

# Regex pour matcher les noms de stations espagnoles
STATION_PATTERN = re.compile(r"roquetes|el arenosillo|arenosillo|ebre", re.IGNORECASE)

# Limites géographiques pour l'Espagne
SPAIN_LAT_MIN, SPAIN_LAT_MAX = 36, 44
SPAIN_LON_MIN, SPAIN_LON_MAX = -9.5, 4.5


async def fetch_stations_data() -> Optional[list]:
    """
    Récupère les données depuis l'API KC2G avec retry et timeout.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.get(API_URL)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning(f"Tentative {attempt + 1} échouée: {e}, retry dans {delay}s")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error("Échec de récupération des données après toutes les tentatives")
                    return None


def is_spanish_station(station_data: dict) -> bool:
    """
    Vérifie si une station est en Espagne selon les critères géographiques.
    """
    try:
        station_info = station_data.get("station", {})
        lat = float(station_info.get("latitude", 0))
        lon = float(station_info.get("longitude", 0))
        return (SPAIN_LAT_MIN <= lat <= SPAIN_LAT_MAX and 
                SPAIN_LON_MIN <= lon <= SPAIN_LON_MAX)
    except (ValueError, TypeError):
        return False


def filter_spanish_stations(stations_data: list) -> Dict[str, StationData]:
    """
    Filtre les stations espagnoles et extrait les données pertinentes.
    """
    spanish_stations = {}
    logger.info(f"Nombre total de stations reçues: {len(stations_data) if stations_data else 0}")
    
    for station in stations_data:
        if not isinstance(station, dict):
            continue
            
        station_info = station.get("station", {})
        code = station_info.get("code", "")
        name = station_info.get("name", "")
        mufd = station.get("mufd")
        
        logger.info(f"Station trouvée - Code: {code}, Nom: {name}, MUFd: {mufd}")
        
        # Identifier les stations par nom ou coordonnées
        normalized_name = None
        
        # Recherche par nom
        name_lower = name.lower()
        if "roquetes" in name_lower or "ebre" in name_lower:
            normalized_name = "roquetes"
        elif "arenosillo" in name_lower:
            normalized_name = "arenosillo"
        
        # Recherche par coordonnées approximatives
        if not normalized_name:
            lat = float(station_info.get("latitude", 0))
            lon = float(station_info.get("longitude", 0))
            
            # Roquetes: ~40.8°N, 0.5°E
            if abs(lat - 40.8) < 0.5 and abs(lon - 0.5) < 0.5:
                normalized_name = "roquetes"
            # Arenosillo: ~37.1°N, -6.7°W  
            elif abs(lat - 37.1) < 0.5 and abs(lon - (-6.7)) < 0.5:
                normalized_name = "arenosillo"
        
        if not normalized_name:
            continue
            
        if normalized_name:
            # Toujours utiliser le timestamp actuel pour éviter les problèmes de stale data
            timestamp = datetime.now(timezone.utc)
                
            spanish_stations[normalized_name] = StationData(
                name=name,
                latitude=float(station_info.get("latitude", 0)),
                longitude=float(station_info.get("longitude", 0)),
                mufd=mufd,
                timestamp=timestamp
            )
            logger.info(f"Station {normalized_name} ajoutée avec MUFd: {mufd}")
    
    logger.info(f"Stations espagnoles filtrées: {list(spanish_stations.keys())}")
    return spanish_stations


async def get_muf_data() -> Tuple[Optional[float], Optional[float], Optional[datetime]]:
    """
    Récupère les données MUF pour Roquetes et Arenosillo.
    Retourne: (roquetes_muf, arenosillo_muf, timestamp)
    """
    stations_data = await fetch_stations_data()
    if not stations_data:
        logger.error("Aucune donnée reçue depuis l'API")
        return None, None, None
        
    spanish_stations = filter_spanish_stations(stations_data)
    logger.info(f"Stations espagnoles trouvées: {list(spanish_stations.keys())}")
    
    roquetes_muf = spanish_stations.get("roquetes", {}).mufd if "roquetes" in spanish_stations else None
    arenosillo_muf = spanish_stations.get("arenosillo", {}).mufd if "arenosillo" in spanish_stations else None
    
    logger.info(f"Valeurs MUF - Roquetes: {roquetes_muf}, Arenosillo: {arenosillo_muf}")
    
    # Utiliser le timestamp le plus récent
    latest_timestamp = None
    for station in spanish_stations.values():
        if station.timestamp and (latest_timestamp is None or station.timestamp > latest_timestamp):
            latest_timestamp = station.timestamp
    
    if latest_timestamp is None:
        latest_timestamp = datetime.now(timezone.utc)
    
    return roquetes_muf, arenosillo_muf, latest_timestamp