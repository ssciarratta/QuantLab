"""Schedule de comisiones Binance Spot (research / lab).

Fuente: tarifa publicada VIP 0 (Regular) en el fee schedule de Binance Spot.
No hay endpoint público sin auth que devuelva la VIP del usuario; por eso el lab
usa el schedule retail documentado (no inventa 0%).

VIP 0 Spot (sin pagar en BNB): maker 0.10% · taker 0.10%  (= 10 bps).
Con pago de fees en BNB (−25%): 0.075% (= 7.5 bps).

Referencia: https://www.binance.com/en/fee/schedule
Actualizado en código: 2026-07-27. Revisar si Binance cambia VIP 0.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from quantlab.execution.fees import MakerTakerFeeModel

# VIP 0 / Regular — Spot (sin descuento BNB)
SPOT_VIP0_MAKER_BPS = Decimal("10")  # 0.10%
SPOT_VIP0_TAKER_BPS = Decimal("10")  # 0.10%

# Mismo tier con BNB fee discount (−25%)
SPOT_VIP0_BNB_MAKER_BPS = Decimal("7.5")  # 0.075%
SPOT_VIP0_BNB_TAKER_BPS = Decimal("7.5")  # 0.075%

FEE_SCHEDULE_ID = "binance_spot_vip0"
FEE_SCHEDULE_URL = "https://www.binance.com/en/fee/schedule"
FEE_SCHEDULE_AS_OF = "2026-07-27"


@dataclass(frozen=True, slots=True)
class BinanceSpotFeeSchedule:
    """Snapshot del schedule retail usado en lab/backtest."""

    schedule_id: str
    as_of: str
    source_url: str
    maker_bps: Decimal
    taker_bps: Decimal
    use_bnb_discount: bool
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "as_of": self.as_of,
            "source_url": self.source_url,
            "maker_bps": str(self.maker_bps),
            "taker_bps": str(self.taker_bps),
            "maker_pct": str(self.maker_bps / Decimal("100")),
            "taker_pct": str(self.taker_bps / Decimal("100")),
            "use_bnb_discount": self.use_bnb_discount,
            "note": self.note,
        }


def _env_bnb_discount(default: bool = False) -> bool:
    raw = os.environ.get("QUANTLAB_BINANCE_FEE_BNB_DISCOUNT", "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def resolve_binance_spot_fee_schedule(
    *,
    use_bnb_discount: bool | None = None,
) -> BinanceSpotFeeSchedule:
    """Resuelve VIP0 Spot (o VIP0+BNB). Default: sin BNB (conservador)."""
    bnb = _env_bnb_discount(False) if use_bnb_discount is None else use_bnb_discount
    if bnb:
        return BinanceSpotFeeSchedule(
            schedule_id=FEE_SCHEDULE_ID,
            as_of=FEE_SCHEDULE_AS_OF,
            source_url=FEE_SCHEDULE_URL,
            maker_bps=SPOT_VIP0_BNB_MAKER_BPS,
            taker_bps=SPOT_VIP0_BNB_TAKER_BPS,
            use_bnb_discount=True,
            note="VIP0 Spot con descuento BNB (−25%). No es la VIP de tu cuenta vía API.",
        )
    return BinanceSpotFeeSchedule(
        schedule_id=FEE_SCHEDULE_ID,
        as_of=FEE_SCHEDULE_AS_OF,
        source_url=FEE_SCHEDULE_URL,
        maker_bps=SPOT_VIP0_MAKER_BPS,
        taker_bps=SPOT_VIP0_TAKER_BPS,
        use_bnb_discount=False,
        note="VIP0 Spot retail 0.10%/0.10%. Sin asumir pago en BNB.",
    )


def binance_spot_fee_model(
    *,
    use_bnb_discount: bool | None = None,
) -> MakerTakerFeeModel:
    """FeeModel listo para BarBacktester / BarSimulationEngine."""
    sched = resolve_binance_spot_fee_schedule(use_bnb_discount=use_bnb_discount)
    return MakerTakerFeeModel(
        maker_bps=sched.maker_bps,
        taker_bps=sched.taker_bps,
        model_id=f"fee.binance_spot_vip0{'_bnb' if sched.use_bnb_discount else ''}.v1",
    )
