from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.models.schemas import DomainManifest, SignalSnapshot, SystemProfile
from app.services.domain_ids import safe_child_file, safe_domain_dir


class DomainService:
    def __init__(self, domains_root: Path) -> None:
        self.domains_root = domains_root

    def list_domains(self) -> list[DomainManifest]:
        manifests = []
        for path in sorted(self.domains_root.glob("*/manifest.yaml")):
            manifests.append(self._load_manifest(path.parent))
        return manifests

    def get_domain(self, domain_id: str) -> DomainManifest:
        domain_dir = self._domain_dir(domain_id)
        return self._load_manifest(domain_dir)

    def get_system(self, domain_id: str, system_id: str) -> SystemProfile:
        domain = self.get_domain(domain_id)
        for system in domain.systems:
            if system.id == system_id:
                return system
        raise KeyError(f"Unknown system_id {system_id!r} for domain {domain_id!r}")

    def get_signals(self, domain_id: str, system_id: str) -> SignalSnapshot:
        path = safe_child_file(self._domain_dir(domain_id) / "signals", system_id, ".json")
        if not path.exists():
            raise KeyError(f"Missing signals for {domain_id}/{system_id}")
        return SignalSnapshot.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def _domain_dir(self, domain_id: str) -> Path:
        return safe_domain_dir(self.domains_root, domain_id)

    def _load_manifest(self, domain_dir: Path) -> DomainManifest:
        data = yaml.safe_load((domain_dir / "manifest.yaml").read_text(encoding="utf-8"))
        return DomainManifest.model_validate(data)
