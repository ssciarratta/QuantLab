# Fase 20 — Workbench (1-click, ventanas tipo Windows)

**Estado:** DISEÑO → implementar tras F19  
**Prerrequisito:** F19 Operating Modes + BrokerPort  
**Pedido dueño:** entrar con 1 click; ventanas tipo Windows; mouse; todas las funcionalidades.

## Stack (DEC-061)

`stdlib http.server` + SPA estática con window-manager (sin deps UI nuevas).

```text
src/quantlab/workbench/
├── server.py / api.py / launch.py
└── static/ (index.html, css, js/wm.js, panes)
```

Bind default: `127.0.0.1`. Entry: `quantlab-workbench`.

## Paneles F20 (shell)

1. Health / Mode  
2. Market Data  
3. Paper Blotter  

## Fuera de alcance F20

Chat completo (F22), paneles de todas las features (F21), Electron, LIVE UI arming.
