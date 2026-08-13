"""Support for Hue lights."""

from aiohue.v2.models.feature import Signal
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .bridge import HueConfigEntry
from .const import ATTR_COLOR, ATTR_COLOR2, ATTR_DURATION, ATTR_SIGNAL, SERVICE_SIGNAL
from .v1.light import async_setup_entry as setup_entry_v1
from .v2.group import async_setup_entry as setup_groups_entry_v2
from .v2.light import async_setup_entry as setup_entry_v2

VALID_SIGNAL_VALUES = [x.value for x in Signal if x != Signal.UNKNOWN]
RGB_COLOR_SCHEMA = vol.All(vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HueConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up light entities."""
    bridge = config_entry.runtime_data

    if bridge.api_version == 1:
        await setup_entry_v1(hass, config_entry, async_add_entities)
        return
    # v2 setup logic here
    await setup_entry_v2(hass, config_entry, async_add_entities)
    await setup_groups_entry_v2(hass, config_entry, async_add_entities)

    # register the signaling entity service (V2 only)
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SIGNAL,
        {
            vol.Required(ATTR_SIGNAL): vol.All(
                vol.In(VALID_SIGNAL_VALUES), vol.Coerce(Signal)
            ),
            vol.Optional(ATTR_DURATION): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65534)
            ),
            vol.Optional(ATTR_COLOR): RGB_COLOR_SCHEMA,
            vol.Optional(ATTR_COLOR2): RGB_COLOR_SCHEMA,
        },
        "async_signal",
    )
