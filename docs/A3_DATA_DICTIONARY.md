# A3 Data Dictionary (mínimo)

## Raw record
provider, endpoint_or_message_type, environment, symbol, event_timestamp,
received_timestamp, request_id, schema_version, payload, checksum, ingestion_run_id

## Instrument (dominio)
instrument_id=`a3:{symbol}`, symbol, base/quote, venue_id=`a3`, tick/lot/min_notional,
metadata.provider/description/market/segment/cfi/maturity/fields_inferred

## Trade
instrument_id, price, quantity, side, timestamp (aware), trade_id

## Bar
OHLCV + timeframe + timestamps aware; construida desde trades (schema_version barras `1.0`)
