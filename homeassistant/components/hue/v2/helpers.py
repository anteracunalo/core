"""Helper functions for Philips Hue v2."""

from aiohue.v2.models.feature import (
    ColorFeaturePut,
    ColorPoint,
    Signal,
    SignalingFeaturePut,
)
from aiohue.v2.models.grouped_light import GroupedLight
from aiohue.v2.models.light import Light

from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import color as color_util

from ..const import DOMAIN


def normalize_hue_brightness(brightness: float | None) -> float | None:
    """Return calculated brightness values."""
    if brightness is not None:
        # Hue uses a range of [0, 100] to control brightness.
        brightness = float((brightness / 255) * 100)

    return brightness


def normalize_hue_transition(transition: float | None) -> float | None:
    """Return rounded transition values."""
    if transition is not None:
        # hue transition duration is in milliseconds and round them to 100ms
        transition = int(round(transition, 1) * 1000)

    return transition


def normalize_hue_colortemp(
    colortemp_k: int | None, min_mireds: int, max_mireds: int
) -> int | None:
    """Return color temperature within Hue's ranges."""
    if colortemp_k is None:
        return None
    colortemp_mireds = color_util.color_temperature_kelvin_to_mired(colortemp_k)
    # Hue only accepts a range between min_mireds..max_mireds
    return min(max(colortemp_mireds, min_mireds), max_mireds)


def build_signaling(
    resource: Light | GroupedLight,
    signal: Signal,
    duration: int | None = None,
    color: tuple[int, int, int] | None = None,
    color2: tuple[int, int, int] | None = None,
) -> SignalingFeaturePut:
    """Build aiohue SignalingFeaturePut from (validated) service call data."""
    if resource.signaling is None or signal not in resource.signaling.signal_values:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="signal_not_supported",
            translation_placeholders={"signal": signal.value},
        )
    colors: list[ColorFeaturePut] | None = None
    if signal in (Signal.ON_OFF_COLOR, Signal.ALTERNATING):
        rgb_colors = [color, color2] if signal == Signal.ALTERNATING else [color]
        if None in rgb_colors:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="signal_missing_color",
                translation_placeholders={
                    "signal": signal.value,
                    "required": str(len(rgb_colors)),
                },
            )
        colors = [
            ColorFeaturePut(xy=ColorPoint(*color_util.color_RGB_to_xy(*rgb)))
            for rgb in rgb_colors
        ]
    return SignalingFeaturePut(
        signal=signal,
        # bridge expects milliseconds with a step size of 1 second
        duration=duration * 1000 if duration is not None else None,
        colors=colors,
    )
