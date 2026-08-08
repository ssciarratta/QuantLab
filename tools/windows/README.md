# Scripts Windows — Binance Spot Testnet

Ejecutar con **doble clic** desde el Explorador o desde CMD. Todos asumen raíz del repo QuantLab.

| Script | Función |
|--------|---------|
| `_common.bat` | Helper interno (paths, .env, runner uv/python) |
| `01_setup_testnet_environment.bat` | `uv sync`, verifica CLI `quantlab-testnet` |
| `02_configure_testnet_credentials.bat` | Crea/actualiza `.env` (secret oculto al tipear) |
| `03_test_binance_testnet_connection.bat` | Ping + auth + balances (log en `logs/`) |
| `04_show_testnet_balances.bat` | Muestra balances testnet |
| `05_install_or_setup_hummingbot.bat` | Guía instalación HB (Docker/WSL) |
| `06_verify_hummingbot_testnet.bat` | Verifica configs HB vs producción |
| `07_full_testnet_diagnostic.bat` | Diagnóstico `TESTNET READY` completo |
| `08_start_quantlab_testnet.bat` | Valida y arranca Workbench |

## Orden recomendado

1. `01_setup_testnet_environment.bat`
2. `02_configure_testnet_credentials.bat` (requiere keys de testnet.binance.vision)
3. `03_test_binance_testnet_connection.bat`
4. `04_show_testnet_balances.bat` (opcional)
5. `07_full_testnet_diagnostic.bat`
6. `05` / `06` si usa Hummingbot externo
7. `08_start_quantlab_testnet.bat`

## Logs

`tools/windows/logs/*.log` — generados por scripts 03 y 07.

## Seguridad

- No imprimen `BINANCE_DEMO_API_SECRET`.
- No crean órdenes.
- No modifican Binance producción.
- `.env` debe permanecer en `.gitignore`.
