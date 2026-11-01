create table if not exists public.member_stock(
 id integer primary key default 1 check(id=1),
 offline_members bigint not null default 0 check(offline_members>=0),
 online_members bigint not null default 0 check(online_members>=0),
 updated_at timestamptz,
 created_at timestamptz not null default now()
);
alter table public.member_stock enable row level security;
revoke all on public.member_stock from anon,authenticated;
insert into public.member_stock(id) values(1) on conflict(id) do nothing;
