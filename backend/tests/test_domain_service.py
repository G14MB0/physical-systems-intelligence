from pathlib import Path

from app.services.domain_service import DomainService


def test_loads_drone_domain_pack_with_system_and_signals() -> None:
    service = DomainService(Path("app/domains"))

    domain = service.get_domain("drone_inspection")
    system = service.get_system("drone_inspection", "DRN-INSPECT-01")
    signals = service.get_signals("drone_inspection", "DRN-INSPECT-01")

    assert domain.id == "drone_inspection"
    assert system.name == "Inspection Drone 01"
    assert signals.system_id == "DRN-INSPECT-01"
    assert signals.current["battery_health_pct"] == 71
    assert signals.events[-1].code == "ESC-TEMP-WARN"
