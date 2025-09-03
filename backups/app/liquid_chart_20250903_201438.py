from typing import Optional
from datetime import datetime

from pyecharts.charts import Liquid
from pyecharts import options as opts
from pyecharts.globals import ThemeType

from app.models import MUFData


def get_muf_color(value: float) -> str:
    """
    Détermine la couleur en fonction de la valeur MUF.
    0-4 MHz: bleu
    4-10 MHz: vert
    10-15 MHz: jaune
    15-24 MHz: orange
    24-32 MHz: rouge
    >32 MHz: violet
    """
    if value < 4:
        return "#0066cc"  # bleu
    elif value < 10:
        return "#00cc66"  # vert
    elif value < 15:
        return "#ffcc00"  # jaune
    elif value < 24:
        return "#ff6600"  # orange
    elif value < 32:
        return "#cc0000"  # rouge
    else:
        return "#6600cc"  # violet


def create_muf_liquid_charts(data: MUFData) -> str:
    """
    Crée des graphiques LiquidFill pour afficher les MUF actuels.
    """
    if not data:
        return ""
    
    charts_html = []
    
    # Roquetes
    if data.roquetes is not None:
        roquetes_chart = create_single_liquid_chart(
            value=data.roquetes,
            max_value=50,
            subtitle=f"{data.roquetes:.1f} MHz"
        )
        charts_html.append(f"<div class='col-md-4'>{roquetes_chart.render_embed()}</div>")
    
    # Arenosillo
    if data.arenosillo is not None:
        arenosillo_chart = create_single_liquid_chart(
            value=data.arenosillo,
            max_value=50,
            title="Arenosillo",
            subtitle=f"{data.arenosillo:.1f} MHz"
        )
        charts_html.append(f"<div class='col-md-4'>{arenosillo_chart.render_embed()}</div>")
    
    # Moyenne
    if data.avg is not None:
        avg_chart = create_single_liquid_chart(
            value=data.avg,
            max_value=50,
            title="Moyenne",
            subtitle=f"{data.avg:.1f} MHz"
        )
        charts_html.append(f"<div class='col-md-4'>{avg_chart.render_embed()}</div>")
    
    return "".join(charts_html)


def create_single_liquid_chart(
    value: float,
    max_value: float = 50,
    title: str = "MUF",
    subtitle: str = "",
    color: str = None,
    dark_mode: bool = False
) -> Liquid:
    """
    Crée un graphique LiquidFill individuel.
    
    Args:
        value: Valeur MUF actuelle
        max_value: Valeur maximale pour le calcul du pourcentage
        title: Titre du graphique
        subtitle: Sous-titre avec la valeur
        color: Couleur personnalisée (optionnel)
        dark_mode: True pour le mode sombre, False pour le mode clair
    """
    # Déterminer la couleur automatiquement si non spécifiée
    if color is None:
        color = get_muf_color(value)
    
    # Calculer le pourcentage
    percentage = min(value / max_value, 1.0)
    
    # Couleurs adaptées au thème
    if dark_mode:
        bg_color = "#2c3e50"
        text_color = "#ecf0f1"
        title_color = "#ecf0f1"
        theme = ThemeType.DARK
    else:
        bg_color = "#ffffff"
        text_color = "#2c3e50"
        title_color = "#2c3e50"
        theme = ThemeType.LIGHT
    
    chart = (
        Liquid(init_opts=opts.InitOpts(
            theme=theme,
            width="100%",
            height="300px",
            bg_color=bg_color
        ))
        .add(
            series_name=title,
            data=[percentage],
            color=[color],
            label_opts=opts.LabelOpts(
                font_size=50,
                color=color,
                position="inside",
                formatter=f"{value:.1f}"
            ),
            outline_border_distance=8,
            outline_itemstyle_opts=opts.ItemStyleOpts(
                color="rgba(0, 0, 0, 0.1)",
                border_color=color,
                border_width=2
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                title_textstyle_opts=opts.TextStyleOpts(font_size=18, color=title_color),
                subtitle_textstyle_opts=opts.TextStyleOpts(font_size=14, color=text_color)
            ),
            legend_opts=opts.LegendOpts(is_show=False)
        )
    )
    
    return chart


def create_muf_liquid_dashboard(data: MUFData) -> str:
    """
    Crée un dashboard complet avec les trois graphiques LiquidFill.
    """
    if not data:
        return """
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        Aucune donnée MUF disponible
                    </div>
                </div>
            </div>
        </div>
        """
    
    charts_html = create_muf_liquid_charts(data)
    
    return f"""
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h3 class="text-center mb-4">MUF Actuel - Stations Espagnoles</h3>
            </div>
        </div>
        <div class="row">
            {charts_html}
        </div>
        <div class="row">
            <div class="col-12 text-center">
                <small class="text-muted">
                    Dernière mise à jour: {data.ts.strftime('%d/%m/%Y %H:%M:%S UTC') if data.ts else 'N/A'}
                </small>
            </div>
        </div>
    </div>
    """