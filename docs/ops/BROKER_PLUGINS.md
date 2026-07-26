# Broker plugins — venues externos vía entry points (Fase 24)

QuantLab registra brokers built-in (`a3`, `binance`, `paper`, `generic_csv`, `generic_rest`)
y carga **plugins** del grupo setuptools/hatch:

```text
quantlab.brokers
```

Cada entry point debe ser un **callable**:

```python
def factory(mode: OperatingMode, **opts) -> BrokerPort: ...
```

`opts` opcionales (p. ej. `md_source`, `csv_path`) los pasa el workbench / callers
que usen `BrokerRegistry.create(venue, mode, **opts)`.

## Registrar un venue externo

En el `pyproject.toml` del paquete plugin:

```toml
[project.entry-points."quantlab.brokers"]
my_venue = "my_pkg.brokers:create_my_venue"
```

```python
# my_pkg/brokers.py
from quantlab.brokers.mode import OperatingMode
from quantlab.brokers.port import BrokerPort

def create_my_venue(mode: OperatingMode, **opts) -> BrokerPort:
    return MyMdOnlyBroker(mode=mode)
```

Tras instalar el plugin en el mismo entorno que QuantLab,
`get_default_registry()` lo registra automáticamente.
Fallos de carga → **warning** (structlog), sin tumbar el proceso.

## A3 MD read-only opt-in

| `md_source` | Comportamiento |
|-------------|----------------|
| `fake` (default) | `FakeA3Backend` (CI) |
| `env` | Si `QUANTLAB_A3_MD_READONLY=1` **y** `QUANTLAB_A3_USER\|PASSWORD\|ACCOUNT` → `PyRofexBackend` solo para MD/account/positions. Si no → fallback fake + `md_fallback` en health. |

**Siempre:** `A3BrokerPort.submit` / `cancel` llaman `assert_live_routing_blocked()`  
(PAPER usa `PaperBroker` para fills locales).

Workbench:

```http
POST /api/broker/connect
{"venue":"a3","mode":"paper","md_source":"env"}
```

## Generics (sin SDK)

| Venue | Clase | Notas |
|-------|-------|-------|
| `generic_csv` | `GenericCsvMdBroker` | CSV `symbol,bid,ask,last` o demo in-memory; path vía `csv_path` / `QUANTLAB_GENERIC_CSV_PATH` |
| `generic_rest` | `FakeRestMdBroker` | Skeleton in-memory multi-símbolo; documenta el hueco REST real |

Ambos son MD-only (submit/cancel gated). Un plugin REST real puede copiar el skeleton
y hacer HTTP en `get_snapshot` sin tocar builtins.

## Health / session

`GET /api/health` y `GET /api/session` incluyen:

- `md_provider`, `md_source`, `connected_venue`
- `venues`, `plugin_venues`

## Referencias

- Spec: `docs/FASE_24_VENUE_MD_PLUGINS.md`
- DEC-067, DEC-068 en `learning/decisiones.txt`
- LIVE: `docs/ops/LIVE_FLIP_CHECKLIST.md` (flip **no** ejecutado)
