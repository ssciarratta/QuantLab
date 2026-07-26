# Broker Plugin Contract v1

**API:** `"1"` · **Grupo entry point:** `quantlab.brokers`  
**Alcance:** market data y lectura de cuenta · **ejecución prohibida**

## Publicación

El entry point v1 es una función sin argumentos que retorna un
`BrokerPluginSpec`:

```toml
[project.entry-points."quantlab.brokers"]
my_venue = "my_plugin:broker_plugin"
```

```python
from quantlab.brokers.contracts.v1 import BrokerPluginSpec

def broker_plugin() -> BrokerPluginSpec:
    return BrokerPluginSpec(
        api_version="1",
        venue_id="my_venue",
        capabilities=frozenset({"market_data", "account_read"}),
        factory=create_broker,
    )
```

`venue_id` debe cumplir `^[a-z0-9][a-z0-9_-]{0,63}$`. Las únicas
capabilities v1 son `market_data` y `account_read`; una spec vacía o con
`execution`, `orders`, `submit` u otra capability se rechaza.

La factory recibe `OperatingMode` como primer argumento. Puede declarar opciones
keyword explícitas o `**kwargs`. `BrokerRegistry.create()` inspecciona la firma
antes de invocarla: opciones no soportadas producen `ValidationError`; una
factory válida se invoca exactamente una vez y sus `TypeError` internos no se
ocultan ni reintentan.

## Frontera read-only

Todo plugin externo registrado se entrega como `ReadOnlyBrokerPort`.
`connect`, `close`, `health`, market data y cuenta se delegan. `submit` y
`cancel` terminan en `assert_live_routing_blocked()` y nunca alcanzan al plugin.
Un plugin no puede sombrear un venue built-in o previamente registrado.

`OperatingMode.LIVE` se rechaza antes de ejecutar la factory.
`LIVE_BLOCKED=True` permanece como invariante de producto.

## Test kit cooperativo

```python
from quantlab.brokers.testing import run_broker_contract

report = run_broker_contract(broker_plugin())
assert report.passed, report.issues
```

El kit:

- invoca la factory una vez en `TESTER` por default;
- valida `BrokerPort`, venue, lifecycle, DTOs, `Decimal` finitos y timestamp
  aware del snapshot;
- valida por separado que el registry aplique el wrapper read-only;
- nunca llama `submit`/`cancel` del objeto plugin.

El plugin debe ofrecer fixtures offline y deterministas. Este kit es
**cooperativo, no un sandbox**: no contiene filesystem, red, procesos ni código
malicioso. Sólo instalar y ejecutar plugins confiables.

## Legacy v0

Una factory desnuda `(mode, **opts) -> BrokerPort` sigue aceptada
temporalmente. Emite `LegacyBrokerPluginWarning` y también queda siempre detrás
del wrapper read-only. Migrar a `BrokerPluginSpec`; el formato v0 está deprecado.
