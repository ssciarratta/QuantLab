# A3 Security

## Secretos
- Solo vía env: `QUANTLAB_A3_USER|PASSWORD|ACCOUNT|TOKEN`
- Nunca en YAML, logs, excepciones ni Review Package

## Gates de producción
Todos obligatorios:
1. `environment == production`
2. `execution.enabled == true`
3. `execution.allow_live_orders == true`
4. `QUANTLAB_ENABLE_LIVE_TRADING == I_UNDERSTAND_THIS_SENDS_REAL_ORDERS`
5. account allowlist
6. symbol allowlist
7. risk gate
8. kill switch no bloqueante

CI debe fijar `QUANTLAB_ENABLE_LIVE_TRADING=DISABLED`.

## Incidentes
1. Activar kill switch `block_all_orders`
2. Rotar credenciales
3. Revisar raw executions sanitizados
