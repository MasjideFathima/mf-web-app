-- ============================================================
-- Masjid-e-Fathima JAQH, Salem-1  |  Income/Expense Tracker
-- Run this ONCE in Supabase SQL Editor (Project > SQL Editor > New query)
-- ============================================================

-- 1. Users table (linked to Supabase Auth users)
create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    name text not null,
    phone text,
    role text not null default 'member' check (role in ('admin', 'member')),
    created_at timestamptz default now()
);

-- 2. Categories (kept as a table, not hardcoded, so you can add new
--    hadiya/sponsorship types later without touching code)
create table if not exists public.categories (
    id serial primary key,
    name text not null unique,
    type text not null check (type in ('income', 'expense'))
);

insert into public.categories (name, type) values
    ('Monthly Chandha/Subscription', 'income'),
    ('Donation for Masjid', 'income'),
    ('Donation for Building', 'income'),
    ('Jummah Collection', 'income'),
    ('Sponsorship - Computer/Printer/Fan/Light etc.', 'income'),
    ('Hadiya - Imam', 'expense'),
    ('Hadiya - Moulvi', 'expense'),
    ('Hadiya - Aalima', 'expense'),
    ('Hadiya - Jummah Dhayee', 'expense')
on conflict (name) do nothing;

-- 3. Transactions table (income + expense, pending + approved, all in one)
create table if not exists public.transactions (
    id uuid primary key default gen_random_uuid(),
    type text not null check (type in ('income', 'expense')),
    category_id int references public.categories(id),
    amount numeric(12,2) not null check (amount > 0),
    txn_date date not null,
    receipt_number text,          -- only meaningful for income, free text
    donor_name text,               -- name of person donating (for income entries)
    donor_phone text,              -- WhatsApp/mobile number to notify on approval
    payment_method text not null default 'cash' check (payment_method in ('cash', 'bank')),
    description text,
    photo_url text,                -- link into Supabase Storage, not a blob
    status text not null default 'pending' check (status in ('pending','approved','rejected')),
    submitted_by uuid references public.users(id),
    approved_by uuid references public.users(id),
    approved_at timestamptz,
    created_at timestamptz default now()
);

create index if not exists idx_transactions_status on public.transactions(status);
create index if not exists idx_transactions_date on public.transactions(txn_date);
create index if not exists idx_transactions_receipt on public.transactions(receipt_number);

-- ============================================================
-- Row Level Security
-- ============================================================
alter table public.users enable row level security;
alter table public.transactions enable row level security;
alter table public.categories enable row level security;

-- Everyone logged in can read categories
create policy "categories readable by all logged in users"
    on public.categories for select
    using (auth.role() = 'authenticated');

-- Users can see their own profile row; admins can see all
create policy "users can view own profile"
    on public.users for select
    using (auth.uid() = id);

-- Transactions: members can see/insert their own; admins can see/do everything.
-- (Simplify by doing role checks in the app layer via the service key for admin
--  actions, and anon key + these policies for regular member actions.)
create policy "members can insert their own transactions"
    on public.transactions for insert
    with check (auth.uid() = submitted_by);

create policy "members can view their own transactions"
    on public.transactions for select
    using (auth.uid() = submitted_by);

-- Note: Admin pages in the app use the Supabase service_role key (server-side
-- only, never exposed to the browser) which bypasses RLS entirely, so admins
-- can see/approve/reject everything regardless of these member-scoped policies.

-- ============================================================
-- If you already ran the schema.sql before adding WhatsApp support,
-- run just this block to add the new columns without recreating tables:
-- ============================================================
-- alter table public.transactions add column if not exists donor_name text;
-- alter table public.transactions add column if not exists donor_phone text;

-- ============================================================
-- If you already ran schema.sql before adding Cash/Bank tracking, run this:
-- ============================================================
-- alter table public.transactions add column if not exists payment_method text
--     not null default 'cash' check (payment_method in ('cash', 'bank'));

-- ============================================================
-- Storage monitoring: exposes current database size in bytes so the app
-- can warn before hitting Supabase's free tier 500MB database cap.
-- Run this once (safe to re-run - "or replace" overwrites cleanly):
-- ============================================================
create or replace function public.get_database_size_bytes()
returns bigint
language sql
security definer
as $$
  select pg_database_size(current_database());
$$;

grant execute on function public.get_database_size_bytes() to anon, authenticated, service_role;

-- ============================================================
-- Allow deleting a user even if they've submitted/approved transactions.
-- Historical records are kept (financial history isn't erased) but their
-- submitted_by/approved_by becomes NULL, shown as "Unknown" in the app.
-- Run this once before using the delete-user feature:
-- ============================================================
alter table public.transactions drop constraint if exists transactions_submitted_by_fkey;
alter table public.transactions add constraint transactions_submitted_by_fkey
    foreign key (submitted_by) references public.users(id) on delete set null;

alter table public.transactions drop constraint if exists transactions_approved_by_fkey;
alter table public.transactions add constraint transactions_approved_by_fkey
    foreign key (approved_by) references public.users(id) on delete set null;
