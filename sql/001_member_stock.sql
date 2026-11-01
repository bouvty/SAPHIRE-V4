create table if not exists public.stock_members (
    id integer primary key default 1 check (id = 1),
    offline_members bigint not null default 0 check (offline_members >= 0),
    online_members bigint not null default 0 check (online_members >= 0),
    updated_at timestamptz,
    created_at timestamptz not null default now()
);
alter table public.stock_members enable row level security;
revoke all on public.stock_members from anon, authenticated;
insert into public.stock_members(id) values(1) on conflict(id) do nothing;
