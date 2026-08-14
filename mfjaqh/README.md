# Masjid-e-Fathima JAQH, Salem-1 — Income/Expense Tracker

100% free stack: Streamlit (app) + Supabase (database, auth, photo storage) +
GitHub (code) + Streamlit Community Cloud (hosting).

## 1. Create your Supabase project (free)

1. Go to https://supabase.com → Sign up → **New project**.
2. Pick any name/region, set a database password (save it somewhere safe).
3. Wait ~2 minutes for it to provision.

## 2. Set up the database

1. In your Supabase project, go to **SQL Editor > New query**.
2. Paste the entire contents of `schema.sql` from this repo and click **Run**.
3. This creates the `users`, `categories`, and `transactions` tables with the
   correct policies, and pre-fills your income/expense categories.

## 3. Create the photo storage bucket

1. Go to **Storage** in the Supabase sidebar → **New bucket**.
2. Name it exactly `receipts`.
3. Set it to **Public** (so `st.image()` can display photos directly via URL).

## 4. Create your admin user

1. Go to **Authentication > Users > Add user** → enter your email + a password.
   Copy the generated User UID.
2. Go to **Table Editor > users > Insert row**:
   - `id` = the User UID you copied
   - `name` = your name
   - `role` = `admin`
3. Repeat for every other admin. For regular members, do the same but set
   `role` = `member`.

## 5. Get your API keys

Go to **Project Settings > API**. You'll need:
- **Project URL**
- **anon public** key
- **service_role** key (keep this one secret — never put it in frontend code
  or commit it to git; it's fine here because Streamlit apps run server-side)

## 6. Run locally (optional, to test first)

```bash
cd masjid-tracker
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml and paste in your 3 keys from step 5
streamlit run app.py
```

## 7. Deploy for free on Streamlit Community Cloud

1. Push this folder to a new **GitHub repo** (can be private).
   Make sure `.streamlit/secrets.toml` is NOT committed (`.gitignore` already
   excludes it).
2. Go to https://share.streamlit.io → Sign in with GitHub → **New app**.
3. Pick your repo, branch, and set the main file to `app.py`.
4. Under **Advanced settings > Secrets**, paste in the same 3 keys from
   step 5 (same format as `secrets.toml.example`).
5. Click **Deploy**. You'll get a free public URL like
   `https://your-app-name.streamlit.app`.

## How it works

- **Admins**: anything they submit via "Add Transaction" is saved as
  `approved` immediately.
- **Members**: their submissions are saved as `pending` and only show up in
  totals/reports once an admin approves them on the "Pending Approvals" page.
- **Photos**: uploaded to Supabase Storage (`receipts` bucket), and only the
  URL is stored in the database — keeps the database small and fast.
- **Receipt numbers**: free text field for income entries, with a duplicate
  check to flag if the same number is entered twice.

## Free tier limits (should never be an issue for a single masjid)

- Supabase: 500MB database, 1GB file storage, 50,000 monthly active users
- Streamlit Community Cloud: unlimited public apps, generous compute for
  low-traffic apps like this

## Adding/removing admins or members later

Just add/edit rows directly in the Supabase **Table Editor > users** table —
no code changes needed.
