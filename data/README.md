# Semiconductor logistics data

This folder holds the source CSV and instructions for the three Supabase datasets defined in `semiconductor_research/chatgpt_project_suggestions.md`.

## Supabase tables (already created)

| Table | Dataset | Description |
|-------|---------|-------------|
| **shipments** | Dataset 1 | One row per shipment. Schema matches the CSV columns. |
| **shipment_event_log** | Dataset 2 | One row per event update (live tracking). Links to `shipments` via `shipment_id`. |
| **warehouse_operations** | Dataset 3 | One row per warehouse per time period (fulfillment metrics). |

## Loading the CSV into `shipments`

**Option A: Supabase Dashboard**

1. Open your project at [supabase.com/dashboard](https://supabase.com/dashboard).
2. Go to **Table Editor** → **shipments**.
3. Click **Import data** (or **Insert** → **Import from CSV**).
4. Upload `semiconductor_shipments_500(1).csv`.
5. Map columns (names match the table); ensure date columns are parsed as timestamps.

**Option B: Script (requires Supabase URL + key)**

From the project root:

```bash
cd data
npm install  # or ensure @supabase/supabase-js and csv-parse are available
SUPABASE_URL=https://your-project.supabase.co SUPABASE_SERVICE_ROLE_KEY=your_key node load_shipments_to_supabase.mjs
```

Use the script in `data/load_shipments_to_supabase.mjs` if you prefer automated loading.

## Dataset 2 and 3

- **shipment_event_log:** Populate from app logic (e.g. one event per shipment using `edi_last_event_code`, `departure_time`/`actual_arrival_time`, `temp_c_recorded`, `humidity_pct_recorded`, `shock_g_max_recorded`) or from a separate events export.
- **warehouse_operations:** Populate from warehouse metrics (e.g. by aggregating shipments by `destination_site` and time, or from synthetic hourly/daily data).

The CSV only contains **Dataset 1 (shipments)**. Event and warehouse data can be derived or generated per the project suggestions doc.
