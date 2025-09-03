import logging
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from app.models import DXSpot, DXSpotList

logger = logging.getLogger(__name__)

# Indicatifs portugais communs
PORTUGUESE_PREFIXES = [
    'CT', 'CR', 'CS', 'CQ', 'CT1', 'CT2', 'CT3', 'CT4', 'CT5', 'CT6', 'CT7', 'CT8', 'CT9',
    'CR1', 'CR2', 'CR3', 'CR4', 'CR5', 'CR6', 'CR7', 'CR8', 'CR9',
    'CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6', 'CS7', 'CS8', 'CS9',
    'CQ1', 'CQ2', 'CQ3', 'CQ4', 'CQ5', 'CQ6', 'CQ7', 'CQ8', 'CQ9'
]


def is_portuguese_callsign(callsign: str) -> bool:
    """
    Vérifie si un indicatif est portugais.
    """
    callsign = callsign.upper().strip()
    
    # Vérifier les préfixes portugais
    for prefix in PORTUGUESE_PREFIXES:
        if callsign.startswith(prefix):
            return True
    
    return False


async def fetch_dx_spots_from_dxsummit() -> List[DXSpot]:
    """
    Récupère les spots DX depuis DXSummit API avec filtres portugais.
    """
    url = "http://www.dxsummit.fi/api/v1/spots?include=3.5MHz,7MHz,14MHz,28MHz,21MHz,1.8MHz&include_modes=PHONE&dx_calls=CT,CS,CQ,CR"
    spots = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # DXSummit retourne directement un tableau de spots
                    if isinstance(data, list):
                        spots_data = data
                    else:
                        spots_data = data.get('spots', [])
                    
                    for spot_data in spots_data:
                        try:
                            # Extraire les données du spot (structure DXSummit)
                            spotter = spot_data.get('de_call', '').strip()
                            dx_call = spot_data.get('dx_call', '').strip()
                            frequency = float(spot_data.get('frequency', 0))
                            comment = spot_data.get('info', '').strip() or ''
                            time_str = spot_data.get('time', '')
                            
                            # Parser le timestamp (format ISO DXSummit)
                            if time_str:
                                # Format attendu: "2025-09-02T11:43:32"
                                time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                                if time_obj.tzinfo is None:
                                    time_obj = time_obj.replace(tzinfo=timezone.utc)
                            else:
                                time_obj = datetime.now(timezone.utc)
                            
                            # Vérifier si c'est un spot portugais
                            if is_portuguese_callsign(spotter) or is_portuguese_callsign(dx_call):
                                spot = DXSpot(
                                    spotter=spotter,
                                    dx_call=dx_call,
                                    frequency=frequency,
                                    comment=comment,
                                    time=time_obj,
                                    country_spotter="Portugal" if is_portuguese_callsign(spotter) else None,
                                    country_dx="Portugal" if is_portuguese_callsign(dx_call) else None
                                )
                                spots.append(spot)
                                
                        except Exception as e:
                            logger.warning(f"Erreur lors du parsing d'un spot: {e}")
                            continue
                            
                else:
                    logger.error(f"Erreur HTTP {response.status} lors de la récupération des spots DX")
                    
    except asyncio.TimeoutError:
        logger.error("Timeout lors de la récupération des spots DX")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des spots DX: {e}")
    
    return spots


async def fetch_dx_spots_from_dxwatch() -> List[DXSpot]:
    """
    Récupère les spots DX depuis DX-Watch (spécifique Portugal).
    """
    # URL pour récupérer les spots portugais spécifiquement
    url = "https://dxwatch.com/dxsd1/dxsd1.php?f=117588"
    spots = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Parser le contenu HTML pour extraire les spots DX
                    import re
                    
                    # Rechercher les patterns de spots DX dans le HTML
                    # Pattern pour capturer: spotter, fréquence, dx_call, commentaire
                    spot_pattern = r'(\w+)\s+(\d+\.\d+)\s+(\w+)\s*(.*)'
                    
                    # Extraire le contenu des lignes de spots depuis le HTML
                    lines = html_content.split('\n')
                    
                    for line in lines:
                        try:
                            # Nettoyer la ligne HTML
                            clean_line = re.sub(r'<[^>]+>', '', line).strip()
                            
                            # Chercher les patterns de spots DX
                            if len(clean_line) > 10 and any(char.isdigit() for char in clean_line):
                                # Essayer de parser la ligne comme un spot
                                parts = clean_line.split()
                                if len(parts) >= 3:
                                    try:
                                        spotter = parts[0]
                                        frequency = float(parts[1])
                                        dx_call = parts[2]
                                        comment = ' '.join(parts[3:]) if len(parts) > 3 else ''
                                        
                                        # Vérifier si c'est un spot portugais
                                        if is_portuguese_callsign(spotter) or is_portuguese_callsign(dx_call):
                                            spot = DXSpot(
                                                spotter=spotter,
                                                dx_call=dx_call,
                                                frequency=frequency,
                                                comment=comment,
                                                time=datetime.now(timezone.utc),
                                                country_spotter="Portugal" if is_portuguese_callsign(spotter) else None,
                                                country_dx="Portugal" if is_portuguese_callsign(dx_call) else None
                                            )
                                            spots.append(spot)
                                    except (ValueError, IndexError) as e:
                                        logger.debug(f"Erreur lors du parsing d'un spot: {e}")
                                        continue
                                            
                        except Exception as e:
                            logger.warning(f"Erreur lors du parsing d'une ligne DX-Watch: {e}")
                            continue
                                
                else:
                    logger.error(f"Erreur HTTP {response.status} lors de la récupération depuis DX-Watch")
                    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération depuis DX-Watch: {e}")
    
    return spots


async def get_portuguese_dx_spots(limit: int = 20) -> DXSpotList:
    """
    Récupère les spots DX portugais depuis plusieurs sources.
    """
    all_spots = []
    
    # Essayer DXSummit en premier
    try:
        spots_dxsummit = await fetch_dx_spots_from_dxsummit()
        all_spots.extend(spots_dxsummit)
        logger.info(f"Récupéré {len(spots_dxsummit)} spots depuis DXSummit")
    except Exception as e:
        logger.error(f"Erreur DXSummit: {e}")
    
    # Si pas assez de spots, essayer DX-Watch
    if len(all_spots) < limit:
        try:
            spots_dxwatch = await fetch_dx_spots_from_dxwatch()
            all_spots.extend(spots_dxwatch)
            logger.info(f"Récupéré {len(spots_dxwatch)} spots depuis DX-Watch")
        except Exception as e:
            logger.error(f"Erreur DX-Watch: {e}")
    
    # Trier par heure (plus récent en premier) et limiter
    all_spots.sort(key=lambda x: x.time, reverse=True)
    limited_spots = all_spots[:limit]
    
    return DXSpotList(
        spots=limited_spots,
        last_update=datetime.now(timezone.utc)
    )


if __name__ == "__main__":
    # Test de la fonction
    async def test():
        spots = await get_portuguese_dx_spots(10)
        print(f"Trouvé {len(spots.spots)} spots portugais:")
        for spot in spots.spots:
            print(f"{spot.time.strftime('%H:%M')} - {spot.spotter} -> {spot.dx_call} @ {spot.frequency} kHz: {spot.comment}")
    
    asyncio.run(test())