-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/bukyxdybwxwtpzywdlhu/sql

create table tournaments (
  id bigint generated always as identity primary key,
  name text not null,
  players text[] not null,
  schedule jsonb not null,
  results jsonb not null default '[]',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

-- Allow public read/write (no auth needed for this app)
alter table tournaments enable row level security;

create policy "Anyone can read tournaments"
  on tournaments for select
  using (true);

create policy "Anyone can insert tournaments"
  on tournaments for insert
  with check (true);

create policy "Anyone can delete tournaments"
  on tournaments for delete
  using (true);

-- Feedback table
create table feedback (
  id bigint generated always as identity primary key,
  message text not null,
  created_at timestamptz not null default now()
);

alter table feedback enable row level security;

create policy "Anyone can insert feedback"
  on feedback for insert
  with check (true);

create policy "Anyone can read feedback"
  on feedback for select
  using (true);
