import os

from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.recorder.history import get_significant_states

from imagespec import render, RenderContext, RenderError
from .drivers.coolled.colors import default_background, get_palette


def map_weather_icon(icon: str) -> str:
    if icon.startswith("weather-"):
        weather_mapping = {
            "clear-night": "night",
            "partlycloudy": "partly-cloudy",
            "exceptional": "sunny-off"
        }
        clean_icon = icon.removeprefix("weather-")
        mapped = weather_mapping.get(clean_icon, clean_icon)
        return f"weather-{mapped}"
    else:
        return icon


def _make_context(hass, *, default_font, palette):
    def font_resolver(name):
        base_name = os.path.basename(name)
        
        # 1. Check local components fonts/ directory
        local_font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        local_path = os.path.join(local_font_dir, base_name)
        if os.path.exists(local_path):
            return local_path
        
        # Also check inside fonts/galmuri/
        galmuri_path = os.path.join(local_font_dir, "galmuri", base_name)
        if os.path.exists(galmuri_path):
            return galmuri_path

        # 2. Check Home Assistant www/fonts
        www_fonts_dir = hass.config.path("www/fonts")
        www_path = os.path.join(www_fonts_dir, base_name)
        if os.path.exists(www_path):
            return www_path

        return None

    def history_provider(entity_ids, start, end):
        return get_significant_states(
            hass,
            start_time=start,
            entity_ids=list(entity_ids),
            significant_changes_only=False,
            minimal_response=True,
            no_attributes=False,
        )

    return RenderContext(
        font_resolver=font_resolver,
        history_provider=history_provider,
        default_font=default_font,
        palette=palette,
    )


def render_image(entity_id, device, service, hass):
    color_type = device.color_type
    
    # Deduplicate palette colors while preserving order
    palette = []
    for val in get_palette(color_type).values():
        if val not in palette:
            palette.append(val)

    bg_name = service.data.get("background", "black")
    payload = service.data.get("payload", "")
    
    # Preprocess icon values to support weather icon mapping
    if isinstance(payload, list):
        for element in payload:
            if isinstance(element, dict) and element.get("type") == "icon" and "value" in element:
                element["value"] = map_weather_icon(str(element["value"]))

    try:
        return render(
            payload=payload,
            width=device.width,
            height=device.height,
            rotate=int(service.data.get("rotate", 0)),
            rotate_mode="canvas",   # fixed resolution LED sign panel
            background=bg_name,
            context=_make_context(hass, default_font="Galmuri14.ttf", palette=palette),
        )
    except RenderError as err:
        raise HomeAssistantError(str(err)) from err