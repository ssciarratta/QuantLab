# Scripts Windows — Binance Spot Testnet

Ejecutar con **doble clic** desde el Explorador o desde CMD. Todos asumen raíz del repo QuantLab.

| Script | Función |
|--------|---------|
| `_common.bat` | Helper interno (paths, .env, `.venv` python, stamp logs) |
| `01_setup_testnet_environment.bat` | `uv sync`, verifica CLI `quantlab-testnet` |
| `02_configure_testnet_credentials.bat` | `.env` Spot Testnet (secret oculto) |
| `02b_configure_futures_testnet_credentials.bat` | `.env` Futures Testnet (XOR Spot) |
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

`tools/windows/logs/*.log` — generados por scripts 03 y 07 (nombre con stamp `yyyyMMdd_HHmmss`, independiente del locale de Windows).

## Notas PC local (ES-AR)

- `_common.bat` **no** usa `setlocal` sticky: exporta `QL_*` al script llamador.
- Preferencia de runner: `.venv\Scripts\python.exe` → evita que `uv run` intente reescribir `quantlab-workbench.exe` mientras el Workbench está abierto.
- Locale `DATE=dom dd/mm/yyyy` rompe substrings `%DATE:~…%`; no usarlas en scripts nuevos.

## Seguridad

- No imprimen `BINANCE_DEMO_API_SECRET`.
- No crean órdenes.
- No modifican Binance producción.
- `.env` debe permanecer en `.gitignore`.
