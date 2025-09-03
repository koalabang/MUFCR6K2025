#!/usr/bin/env python3
"""
Script de débogage pour vérifier les stations disponibles dans l'API KC2G
"""
import httpx
import json
import re

async def debug_stations():
    url = "https://prop.kc2g.com/api/stations.json"
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            print(f"Total stations: {len(data)}")
            print("\nStations espagnoles détectées:")
            
            # Regex pour stations espagnoles
            pattern = re.compile(r"(arenosillo|roquetes|ebre|spain|españa)", re.IGNORECASE)
            
            spanish_stations = []
            for station in data:
                name = station.get("name", "")
                lat = float(station.get("latitude", 0))
                lon = float(station.get("longitude", 0))
                
                # Critères géographiques Espagne
                is_spain_geo = (36 <= lat <= 44) and (-9.5 <= lon <= 4.5)
                is_spain_name = pattern.search(name)
                
                if is_spain_geo or is_spain_name:
                    spanish_stations.append({
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "mufd": station.get("mufd"),
                        "timestamp": station.get("timestamp")
                    })
            
            print(f"Stations trouvées: {len(spanish_stations)}")
            for station in spanish_stations:
                print(f"  {station['name']}: lat={station['lat']}, lon={station['lon']}, mufd={station['mufd']}")
            
            # Vérifier spécifiquement Roquetes et Arenosillo
            print("\nRecherche spécifique:")
            for station in data:
                name = station.get("name", "").lower()
                if "roquetes" in name or "ebre" in name:
                    print(f"Roquetes/Ebre trouvé: {station}")
                if "arenosillo" in name:
                    print(f"Arenosillo trouvé: {station}")
            
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_stations())