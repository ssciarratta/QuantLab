"""Registry de modelo ML activo (fail-closed si ausente)."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.model import MlRankingModel


class MlModelRegistry:
    """``active_model_id`` o None → inferencia desactivada."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._state_path = self.root / "active.json"

    def list_model_ids(self) -> tuple[str, ...]:
        ids: list[str] = []
        for p in sorted(self.root.iterdir()):
            if p.is_dir() and (p / "manifest.json").is_file():
                ids.append(p.name)
        return tuple(ids)

    def read_state(self) -> dict[str, object]:
        if not self._state_path.is_file():
            return {}
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
            return dict(raw) if isinstance(raw, dict) else {}
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

    def write_state(self, payload: dict[str, object]) -> None:
        self._state_path.write_text(
            json.dumps(payload, sort_keys=True), encoding="utf-8"
        )

    def get_active_id(self) -> str | None:
        mid = self.read_state().get("active_model_id")
        return str(mid) if mid else None

    def set_active(self, model_id: str | None) -> None:
        if model_id is not None and model_id not in self.list_model_ids():
            raise ValidationError(f"model_id desconocido: {model_id}")
        st = self.read_state()
        st["active_model_id"] = model_id
        self.write_state(st)

    def load_active(self) -> MlRankingModel | None:
        mid = self.get_active_id()
        if not mid:
            return None
        return MlRankingModel(self.root / mid)


_DEFAULT: MlModelRegistry | None = None


def get_default_registry(root: Path | None = None) -> MlModelRegistry:
    global _DEFAULT
    if root is not None:
        return MlModelRegistry(root)
    if _DEFAULT is None:
        _DEFAULT = MlModelRegistry(Path("experiments") / "alpha_ml")
    return _DEFAULT


__all__ = ["MlModelRegistry", "get_default_registry"]
