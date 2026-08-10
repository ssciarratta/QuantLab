# Vendor Kronos (shiyu-coder/Kronos)

No se versiona el código de terceros aquí (carpeta gitignored).

## Bootstrap

```bash
git clone --depth 1 https://github.com/shiyu-coder/Kronos.git third_party/kronos
uv sync --extra kronos --extra dev
```

Modelo por defecto: `NeoQuasar/Kronos-small` + `NeoQuasar/Kronos-Tokenizer-base`.

QuantLab arranca **sin** este vendor: el Scanner cae a ranking tradicional con `kronos.status=unavailable`.
