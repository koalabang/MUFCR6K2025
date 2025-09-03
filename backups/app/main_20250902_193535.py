import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.models import MUFData, MUFSeries, DXSpotList
from app.fetcher import get_muf_data
from app.store import muf_store
from app.chart import create_muf_chart
from app.liquid_chart import create_muf_liquid_dashboard
from app.dx_fetcher import get_portuguese_dx_spots
from app.backup import init_backup_system, start_backup_system, stop_backup_system, get_backup_status

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="MUF Monitor",
    description="Surveillance des ionosondes espagnoles Roquetes et Arenosillo",
    version="1.0.0"
)

# Configuration des templates
templates = Jinja2Templates(directory="app/templates")

# Scheduler global
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    """
    Démarrage de l'application et du scheduler.
    """
    logger.info("Démarrage de MUF Monitor...")
    
    # Initialiser et démarrer le système de sauvegarde
    init_backup_system()
    start_backup_system()
    logger.info("Système de sauvegarde automatique démarré")
    
    # Ajouter le job de mise à jour toutes les 5 minutes
    scheduler.add_job(
        update_muf_data,
        trigger=IntervalTrigger(minutes=5),
        id="muf_update",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler démarré - mises à jour toutes les 5 minutes")
    
    # Charger les données initiales
    await update_muf_data()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Arrêt propre de l'application.
    """
    logger.info("Arrêt de MUF Monitor...")
    
    # Arrêter le système de sauvegarde
    stop_backup_system()
    logger.info("Système de sauvegarde arrêté")
    
    scheduler.shutdown()


async def update_muf_data():
    """
    Fonction périodique pour récupérer et stocker les données MUF.
    """
    try:
        logger.info("Récupération des données MUF...")
        roquetes, arenosillo, timestamp = await get_muf_data()
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        muf_store.add_data_point(roquetes, arenosillo, timestamp)
        logger.info(f"Données mises à jour - Roquetes: {roquetes}, Arenosillo: {arenosillo}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des données: {e}")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Page principale avec les bulles et le graphique.
    """
    latest_data = muf_store.get_latest()
    return templates.TemplateResponse("index.html", {"request": request, "data": latest_data})


@app.get("/api/muf/latest")
async def get_latest_muf() -> MUFData:
    """
    Endpoint API pour obtenir les dernières données MUF.
    """
    latest = muf_store.get_latest()
    if latest is None:
        return MUFData(
            roquetes=None,
            arenosillo=None,
            avg=None,
            ts=datetime.now(timezone.utc),
            status="STALE"
        )
    
    # Arrondir les valeurs à un chiffre après la virgule
    if latest.roquetes is not None:
        latest.roquetes = round(latest.roquetes, 1)
    if latest.arenosillo is not None:
        latest.arenosillo = round(latest.arenosillo, 1)
    if latest.avg is not None:
        latest.avg = round(latest.avg, 1)
    
    return latest


@app.get("/api/muf/series")
async def get_muf_series(window: Optional[int] = 60) -> MUFSeries:
    """
    Endpoint API pour obtenir les séries de données MUF.
    
    Args:
        window: Fenêtre de temps en minutes (par défaut 60)
    """
    return muf_store.get_series(window)


@app.get("/chart", response_class=HTMLResponse)
async def get_chart(dark: bool = False):
    """
    Endpoint pour obtenir le graphique Pyecharts.
    
    Args:
        dark: True pour le mode sombre, False pour le mode clair
    """
    series = muf_store.get_series()
    chart = create_muf_chart(series, dark_mode=dark)
    return chart.render_embed()


@app.get("/liquid", response_class=HTMLResponse)
async def get_liquid_dashboard():
    """
    Tableau de bord avec graphiques LiquidFill.
    """
    latest_data = muf_store.get_latest()
    if latest_data is None:
        return "<p>Aucune donnée disponible</p>"
    
    return create_muf_liquid_dashboard(latest_data)


@app.get("/liquid/roquetes", response_class=HTMLResponse)
async def get_roquetes_liquid(dark: bool = False):
    """
    Graphique liquid pour Roquetes.
    
    Args:
        dark: True pour le mode sombre, False pour le mode clair
    """
    from app.liquid_chart import create_single_liquid_chart
    latest_data = muf_store.get_latest()
    if latest_data is None or latest_data.roquetes is None:
        return "<p>Aucune donnée disponible</p>"
    
    chart = create_single_liquid_chart(
        value=latest_data.roquetes,
        max_value=50,
        title="Roquetes",
        subtitle=f"{latest_data.roquetes:.1f} MHz",
        dark_mode=dark
    )
    return chart.render_embed()


@app.get("/liquid/arenosillo", response_class=HTMLResponse)
async def get_arenosillo_liquid(dark: bool = False):
    """
    Graphique liquid pour Arenosillo.
    
    Args:
        dark: True pour le mode sombre, False pour le mode clair
    """
    from app.liquid_chart import create_single_liquid_chart
    latest_data = muf_store.get_latest()
    if latest_data is None or latest_data.arenosillo is None:
        return "<p>Aucune donnée disponible</p>"
    
    chart = create_single_liquid_chart(
        value=latest_data.arenosillo,
        max_value=50,
        title="Arenosillo",
        subtitle=f"{latest_data.arenosillo:.1f} MHz",
        dark_mode=dark
    )
    return chart.render_embed()


@app.get("/liquid/moyenne", response_class=HTMLResponse)
async def get_moyenne_liquid(dark: bool = False):
    """
    Graphique liquid pour la moyenne.
    
    Args:
        dark: True pour le mode sombre, False pour le mode clair
    """
    from app.liquid_chart import create_single_liquid_chart
    latest_data = muf_store.get_latest()
    if latest_data is None or latest_data.avg is None:
        return "<p>Aucune donnée disponible</p>"
    
    chart = create_single_liquid_chart(
        value=latest_data.avg,
        max_value=50,
        title="Moyenne",
        subtitle=f"{latest_data.avg:.1f} MHz",
        dark_mode=dark
    )
    return chart.render_embed()


@app.get("/health")
async def health_check():
    """
    Endpoint de santé pour vérifier que l'application fonctionne.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "data_points": muf_store.get_window_size()
    }

@app.get("/api/backup/status")
async def get_backup_status_api():
    """
    Endpoint pour consulter le statut du système de sauvegarde.
    """
    backup_info = get_backup_status()
    return {
        "status": "active",
        "timestamp": datetime.now(timezone.utc),
        **backup_info
    }

@app.post("/api/muf/refresh")
async def force_refresh():
    """
    Force une mise à jour manuelle des données.
    """
    logger.info("Forçage de la mise à jour des données...")
    await update_muf_data()
    latest = muf_store.get_latest()
    return latest


@app.get("/dxcluster", response_class=HTMLResponse)
async def get_dxcluster_page(request: Request):
    """
    Page d'affichage des spots DX portugais.
    """
    try:
        # Récupérer les spots DX portugais
        spots_data = await get_portuguese_dx_spots()
        
        # Calculer les statistiques
        portuguese_spotters = len(set(spot.spotter for spot in spots_data.spots if spot.country_spotter == 'Portugal'))
        portuguese_dx = len(set(spot.dx_call for spot in spots_data.spots if spot.country_dx == 'Portugal'))
        
        return templates.TemplateResponse(
            "dxcluster.html",
            {
                "request": request,
                "spots": spots_data.spots,
                "portuguese_spotters": portuguese_spotters,
                "portuguese_dx": portuguese_dx,
                "last_update": spots_data.last_update
            }
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des spots DX: {e}")
        return templates.TemplateResponse(
            "dxcluster.html",
            {
                "request": request,
                "spots": [],
                "portuguese_spotters": 0,
                "portuguese_dx": 0,
                "last_update": None
            }
        )


@app.get("/api/dx/spots")
async def get_dx_spots_api() -> DXSpotList:
    """
    API pour récupérer les spots DX portugais.
    """
    try:
        spots_data = await get_portuguese_dx_spots()
        return spots_data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des spots DX via API: {e}")
        return DXSpotList(spots=[], last_update=datetime.now(timezone.utc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)