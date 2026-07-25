# A3 Simulation Testing

## Offline (CI)
```bash
uv run pytest tests/unit/data -q
```

## Simulation reMarkets (opt-in)
```bash
set QUANTLAB_RUN_A3_SIMULATION_TESTS=1
# + credenciales QUANTLAB_A3_*
```
Suite dedicada pendiente de credenciales del equipo; el adaptador real es `PyRofexBackend`.

## Prohibido
Órdenes LIVE en CI o sin aprobación del Director.
