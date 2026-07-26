# Broker plugins — venues externos vía entry points (Fases 24/87)

QuantLab registra brokers built-in (`a3`, `binance`, `paper`, `generic_csv`, `generic_rest`)
y carga **plugins** del grupo setuptools/hatch:

```text
quantlab.brokers
```

Desde F87, cada entry point debe ser un provider sin argumentos:

```python
def broker_plugin() -> BrokerPluginSpec: ...
```

La spec API `"1"` declara `venue_id`, capabilities read-only y factory.
Ver el contrato completo en `docs/ops/BROKER_PLUGIN_CONTRACT_V1.md`.
Factories desnudas v0 se aceptan temporalmente con warning.

## Registrar un venue externo

En el `pyproject.toml` del paquete plugin:

```toml
[project.entry-points."quantlab.brokers"]
my_venue = "my_pkg.brokers:broker_plugin"
```

```python
# my_pkg/brokers.py
from quantlab.brokers.contracts.v1 import BrokerPluginSpec

def create_my_venue(mode, **opts):
    return MyMdOnlyBroker(mode=mode)

def broker_plugin() -> BrokerPluginSpec:
    return BrokerPluginSpec(
        api_version="1",
        venue_id="my_venue",
        capabilities=frozenset({"market_data", "account_read"}),
        factory=create_my_venue,
    )
```

Tras instalar el plugin en el mismo entorno que QuantLab,
`get_default_registry()` lo registra automáticamente.
Fallos de carga → **warning** (structlog), sin tumbar el proceso.
**No shadow:** un entry point cuyo nombre coincida con un venue ya registrado
(builtins u otro plugin) se **rechaza** (warning `broker_plugin_shadow_refused`);
no reemplaza la factory existente.

Todo plugin externo se retorna detrás de `ReadOnlyBrokerPort`; `submit` y
`cancel` nunca se delegan. LIVE se rechaza antes de invocar su factory.

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
- Contract v1: `docs/ops/BROKER_PLUGIN_CONTRACT_V1.md`
- DEC-067, DEC-068 en `learning/decisiones.txt`
- DEC-131 en `learning/decisiones.txt`
- LIVE: `docs/ops/LIVE_FLIP_CHECKLIST.md` (flip **no** ejecutado)
