"""Overview sensor: which entities are linked to the portal."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CRITICAL_FIELD_KEYS, DOMAIN, INTEGRATION_VERSION
from .coordinator import LifelineCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([LifelineWatchedSensor(entry.runtime_data, entry)])


class LifelineWatchedSensor(CoordinatorEntity[LifelineCoordinator], SensorEntity):
    """State = number of linked sensors; attributes list them per category."""

    _attr_has_entity_name = True
    _attr_translation_key = "watched"
    _attr_icon = "mdi:shield-link-variant"
    _attr_native_unit_of_measurement = "sensors"

    def __init__(self, coordinator: LifelineCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_watched"
        self.entity_id = "sensor.digital_lifeline_watched_sensors"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="DigiLifeline",
            manufacturer="DigiLifeline",
            sw_version=INTEGRATION_VERSION,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.watched:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, list(self.coordinator.watched), self._handle_watched_change
                )
            )

    @callback
    def _handle_watched_change(self, _event) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> int:
        return len(self.coordinator.watched)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {key: [] for key in CRITICAL_FIELD_KEYS}
        for entity_id, field_key in self.coordinator.watched.items():
            state = self.hass.states.get(entity_id)
            attrs.setdefault(field_key, []).append(
                {
                    "entity_id": entity_id,
                    "name": state.attributes.get("friendly_name") if state else None,
                    "state": state.state if state else "missing",
                }
            )
        return attrs
