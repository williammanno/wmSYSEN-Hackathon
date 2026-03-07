#!/usr/bin/env node
/**
 * Load data/semiconductor_shipments_500(1).csv into Supabase table public.shipments.
 * Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (or ANON key with insert rights)
 * Run from repo root: node data/load_shipments_to_supabase.mjs
 */

import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'fs';
import { parse } from 'csv-parse/sync';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const csvPath = join(__dirname, 'semiconductor_shipments_500(1).csv');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY)');
  process.exit(1);
}

const raw = readFileSync(csvPath, 'utf-8');
const rows = parse(raw, { columns: true, skip_empty_lines: true, trim: true });

function toNum(v) {
  if (v === '' || v == null) return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}
function toInt(v) {
  const n = toNum(v);
  return n == null ? null : Math.round(n);
}
function toTs(v) {
  if (v === '' || v == null) return null;
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}
function str(v) {
  if (v === '' || v == null) return null;
  return String(v).trim();
}

const records = rows.map((r) => ({
  shipment_id: str(r.shipment_id),
  company: str(r.company),
  part_type: str(r.part_type),
  product_family: str(r.product_family),
  priority_level: str(r.priority_level),
  origin_site: str(r.origin_site),
  origin_type: str(r.origin_type),
  origin_city: str(r.origin_city),
  origin_country: str(r.origin_country),
  destination_site: str(r.destination_site),
  destination_type: str(r.destination_type),
  destination_city: str(r.destination_city),
  destination_state: str(r.destination_state),
  carrier: str(r.carrier),
  transport_mode: str(r.transport_mode),
  route_type: str(r.route_type),
  departure_time: toTs(r.departure_time),
  planned_arrival_time: toTs(r.planned_arrival_time),
  actual_arrival_time: toTs(r.actual_arrival_time),
  current_status: str(r.current_status),
  edi_last_event_code: str(r.edi_last_event_code),
  distance_km: toNum(r.distance_km),
  freight_cost_usd_per_kg: toNum(r.freight_cost_usd_per_kg),
  customs_required: toInt(r.customs_required),
  customs_hold_hours: toNum(r.customs_hold_hours),
  c_tpat_enrolled: toInt(r.c_tpat_enrolled),
  tariff_flag_hts8542: toInt(r.tariff_flag_hts8542),
  temperature_sensitive: toInt(r.temperature_sensitive),
  shock_sensitive: toInt(r.shock_sensitive),
  humidity_sensitive: toInt(r.humidity_sensitive),
  temp_c_recorded: toNum(r.temp_c_recorded),
  humidity_pct_recorded: toNum(r.humidity_pct_recorded),
  shock_g_max_recorded: toNum(r.shock_g_max_recorded),
  shock_exception_flag: toInt(r.shock_exception_flag),
  chokepoint_exposure: toInt(r.chokepoint_exposure),
  sla_hours: toNum(r.sla_hours),
  delay_hours: toNum(r.delay_hours),
  missed_delivery_window: toInt(r.missed_delivery_window),
  warehouse_stop_count: toInt(r.warehouse_stop_count),
  current_location: str(r.current_location),
  weather_event: str(r.weather_event),
  geopolitical_event: str(r.geopolitical_event),
  weather_risk_score: toNum(r.weather_risk_score),
  geopolitical_risk_score: toNum(r.geopolitical_risk_score),
  port_congestion_score: toNum(r.port_congestion_score),
  labor_risk_score: toNum(r.labor_risk_score),
  composite_risk_score: toNum(r.composite_risk_score),
}));

const supabase = createClient(supabaseUrl, supabaseKey);

async function main() {
  const batchSize = 100;
  let inserted = 0;
  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);
    const { data, error } = await supabase.from('shipments').upsert(batch, {
      onConflict: 'shipment_id',
      ignoreDuplicates: false,
    });
    if (error) {
      console.error('Insert error:', error);
      process.exit(1);
    }
    inserted += batch.length;
    console.log(`Upserted ${inserted}/${records.length} rows`);
  }
  console.log('Done. Total rows in shipments:', inserted);
}

main();
