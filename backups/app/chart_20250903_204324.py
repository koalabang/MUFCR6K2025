from typing import List, Optional
from datetime import datetime

from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts.globals import ThemeType

from app.models import MUFSeries


def create_muf_chart(series: MUFSeries, dark_mode: bool = False) -> Line:
    """
    Crée un graphique Pyecharts Line avec les 3 séries MUF.
    
    Args:
        series: Données des séries MUF
        dark_mode: True pour le mode sombre, False pour le mode clair
    """
    # Convertir les timestamps en strings ISO courtes
    x_data = [ts.strftime("%H:%M") for ts in series.timestamps]
    
    # Arrondir les valeurs à un chiffre après la virgule
    roquetes_rounded = [round(val, 1) if val is not None else None for val in series.roquetes]
    arenosillo_rounded = [round(val, 1) if val is not None else None for val in series.arenosillo]
    avg_rounded = [round(val, 1) if val is not None else None for val in series.avg]
    
    # Choisir le thème selon le mode
    theme = ThemeType.DARK if dark_mode else ThemeType.LIGHT
    
    # Couleurs adaptées au thème
    if dark_mode:
        bg_color = "#2c3e50"
        text_color = "#ecf0f1"
        grid_color = "#34495e"
        title_color = "#ecf0f1"
    else:
        bg_color = "#ffffff"
        text_color = "#2c3e50"
        grid_color = "#e8e8e8"
        title_color = "#2c3e50"
    
    # Créer le graphique
    chart = (
        Line(init_opts=opts.InitOpts(
            theme=theme,
            width="100%", 
            height="400px",
            js_host="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/",
            bg_color=bg_color
        ))
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="Roquetes",
            y_axis=roquetes_rounded,
            is_symbol_show=False,
            linestyle_opts=opts.LineStyleOpts(width=2),
            itemstyle_opts=opts.ItemStyleOpts(color="#1f77b4"),
            label_opts=opts.LabelOpts(is_show=False),
            areastyle_opts=opts.AreaStyleOpts(
                opacity=0.6,
                color=opts.JsCode("""
                    new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#1f77b4'},
                        {offset: 1, color: 'rgba(31, 119, 180, 0.1)'}
                    ])
                """)
            ),
            stack="stack1",
        )
        .add_yaxis(
            series_name="Arenosillo",
            y_axis=arenosillo_rounded,
            is_symbol_show=False,
            linestyle_opts=opts.LineStyleOpts(width=2),
            itemstyle_opts=opts.ItemStyleOpts(color="#ff7f0e"),
            label_opts=opts.LabelOpts(is_show=False),
            areastyle_opts=opts.AreaStyleOpts(
                opacity=0.6,
                color=opts.JsCode("""
                    new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#ff7f0e'},
                        {offset: 1, color: 'rgba(255, 127, 14, 0.1)'}
                    ])
                """)
            ),
            stack="stack1",
        )
        .add_yaxis(
            series_name="Moyenne",
            y_axis=avg_rounded,
            is_symbol_show=False,
            linestyle_opts=opts.LineStyleOpts(width=3),
            itemstyle_opts=opts.ItemStyleOpts(color="#2ca02c"),
            label_opts=opts.LabelOpts(is_show=False),
            areastyle_opts=opts.AreaStyleOpts(
                opacity=0.6,
                color=opts.JsCode("""
                    new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#2ca02c'},
                        {offset: 1, color: 'rgba(44, 160, 44, 0.1)'}
                    ])
                """)
            ),
            stack="stack1",
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="MUF (3000 km) - Stations Espagnoles",
                subtitle=f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S UTC')}",
                title_textstyle_opts=opts.TextStyleOpts(color=title_color),
                subtitle_textstyle_opts=opts.TextStyleOpts(color=text_color)
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                formatter="{b}<br/>{a}: {c} MHz"
            ),
            legend_opts=opts.LegendOpts(
                pos_top="5%",
                selected_mode="multiple",
                textstyle_opts=opts.TextStyleOpts(color=text_color)
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=False,
                axislabel_opts=opts.LabelOpts(rotate=45, color=text_color),
                name="Heure (UTC)",
                name_textstyle_opts=opts.TextStyleOpts(color=text_color),
                axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color=grid_color))
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                name="MUF (MHz)",
                min_=0,
                splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(color=grid_color)),
                axislabel_opts=opts.LabelOpts(color=text_color),
                name_textstyle_opts=opts.TextStyleOpts(color=text_color),
                axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color=grid_color))
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    type_="slider",
                    range_start=0,
                    range_end=100,
                    pos_bottom="0%"
                ),
                opts.DataZoomOpts(
                    type_="inside",
                    range_start=0,
                    range_end=100
                )
            ],
        )
        .set_series_opts(
            markline_opts=opts.MarkLineOpts(
                data=[
                    opts.MarkLineItem(y=1.8, name="1.8 MHz", linestyle_opts=opts.LineStyleOpts(color="#ff0000", width=1, type_="dashed")),
                    opts.MarkLineItem(y=3.5, name="3.5 MHz", linestyle_opts=opts.LineStyleOpts(color="#ff0000", width=1, type_="dashed")),
                    opts.MarkLineItem(y=7.0, name="7 MHz", linestyle_opts=opts.LineStyleOpts(color="#ff0000", width=1, type_="dashed")),
                    opts.MarkLineItem(y=14.0, name="14 MHz", linestyle_opts=opts.LineStyleOpts(color="#ff0000", width=1, type_="dashed")),
                    opts.MarkLineItem(y=21.0, name="21 MHz", linestyle_opts=opts.LineStyleOpts(color="#ff0000", width=1, type_="dashed")),
                    opts.MarkLineItem(y=28.0, name="28 MHz", linestyle_opts=opts.LineStyleOpts(color="#ff0000", width=1, type_="dashed")),
                ],
                label_opts=opts.LabelOpts(
                    position="start",
                    formatter="{b}",
                    color="#ff0000",
                    font_size=10
                ),
                symbol=["none", "none"],
            )
        )
    )
    
    return chart


def get_color_for_muf(muf_value: Optional[float]) -> str:
    """
    Retourne la couleur correspondante selon la valeur MUF.
    """
    if muf_value is None:
        return "#6c757d"  # Gris pour données manquantes
    
    if muf_value < 10:
        return "#dc3545"  # Rouge
    elif muf_value < 20:
        return "#fd7e14"  # Orange
    elif muf_value < 30:
        return "#ffc107"  # Jaune
    else:
        return "#28a745"  # Vert


def get_badge_class_for_muf(muf_value: Optional[float]) -> str:
    """
    Retourne la classe Bootstrap pour le badge selon la valeur MUF.
    """
    if muf_value is None:
        return "secondary"
    
    if muf_value < 10:
        return "danger"
    elif muf_value < 20:
        return "warning"
    elif muf_value < 30:
        return "info"
    else:
        return "success"