-- Schema for the b-connect Wi-Fi Integration Dashboard.
-- Run this once against your Postgres/Supabase database before starting the app.
-- The application does not run create_all(); this file is the source of truth
-- and app/models.py maps onto it.

-- gen_random_uuid() is built in on Postgres 13+ (and on Supabase); this is
-- a harmless safety net for older installs.
create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- updated_at trigger: keeps updated_at current on every UPDATE so the app
-- doesn't have to set it manually.
-- ---------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- ---------------------------------------------------------------------------
-- venues: a physical location reported by the Wi-Fi controller.
-- ---------------------------------------------------------------------------
create table if not exists venues (
    id          uuid primary key default gen_random_uuid(),
    external_id text not null unique,
    name        text not null,
    address     text,
    city        text,
    country     text,
    timezone    text,
    latitude    double precision,
    longitude   double precision,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create trigger venues_set_updated_at
    before update on venues
    for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- access_points: hardware AP, uniquely identified by its MAC address.
-- ---------------------------------------------------------------------------
create table if not exists access_points (
    id             uuid primary key default gen_random_uuid(),
    external_id    text not null unique,
    venue_id       uuid not null references venues(id) on delete cascade,
    name           text not null,
    mac_address    text not null,
    model          text,
    ip_address     inet,
    firmware       text,
    status         text not null default 'online',
    uptime_seconds bigint default 0,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    constraint uq_access_points_mac unique (mac_address)
);

create index if not exists ix_access_points_venue_id on access_points(venue_id);

create trigger access_points_set_updated_at
    before update on access_points
    for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- sessions: a single client Wi-Fi session attached to an access point.
-- ---------------------------------------------------------------------------
create table if not exists sessions (
    id               uuid primary key default gen_random_uuid(),
    external_id      text not null unique,
    access_point_id  uuid not null references access_points(id) on delete cascade,
    client_mac       text not null,
    username         text,
    device_type      text,
    os               text,
    gender           text,
    age              integer,
    ssid             text,
    ip_assigned      inet,
    start_time       timestamptz not null,
    end_time         timestamptz,
    duration_seconds integer,
    rx_bytes         bigint default 0,
    tx_bytes         bigint default 0,
    signal_dbm       integer,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index if not exists ix_sessions_access_point_id on sessions(access_point_id);

create trigger sessions_set_updated_at
    before update on sessions
    for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- sync_logs: audit record for one ingestion run from the controller.
-- ---------------------------------------------------------------------------
create table if not exists sync_logs (
    id                    uuid primary key default gen_random_uuid(),
    status                text not null,
    source                text,
    started_at            timestamptz not null default now(),
    finished_at           timestamptz,
    venues_synced         integer default 0,
    access_points_synced  integer default 0,
    sessions_synced       integer default 0,
    error_message         text,
    raw_payload           jsonb,
    created_at            timestamptz not null default now(),
    updated_at            timestamptz not null default now(),
    constraint sync_logs_status_check check (status in ('success', 'partial', 'error'))
);

create trigger sync_logs_set_updated_at
    before update on sync_logs
    for each row execute function set_updated_at();
