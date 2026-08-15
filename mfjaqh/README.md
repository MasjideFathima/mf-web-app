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

## WhatsApp Notifications (donor confirmation on approval)

When an admin approves an income entry, the donor gets an automatic WhatsApp
message using Meta's official Cloud API. No paid BSP needed - Meta charges
only a tiny per-message fee (~₹0.12 in India), no monthly platform cost.

### One-time setup

1. Go to https://developers.facebook.com → create a free developer account.
2. **My Apps > Create App** → type = **Business**.
3. Inside the app, add the **WhatsApp** product.
4. On the API Setup page, note down:
   - **Phone Number ID**
   - The **temporary access token** (only valid 24h, for testing only)
5. Click **Add phone number** and register a real phone number you own as
   your WhatsApp Business number (must not already be an active WhatsApp
   number - if it is, remove it from WhatsApp first). This lets you message
   *any* number dynamically, not just Meta's 5 test recipients.
6. Create a message template (Meta App Dashboard > WhatsApp > Message
   Templates > Create Template):
   - Name: `donation_receipt` (or update `WHATSAPP_TEMPLATE_NAME` in secrets
     to match whatever you name it)
   - Category: **Utility**
   - Body example:
     ```
     Dear {{1}}, your {{2}} of ₹{{3}} (Receipt #{{4}}) has been recorded.
     Jazakallah Khair - Masjid-e-Fathima JAQH, Salem-1
     ```
   - Submit for approval (usually minutes to a few hours)
7. Generate a **permanent token**: Meta Business Settings > Users > System
   Users > create a system user > generate token with `whatsapp_business_messaging`
   permission. Use this (not the 24h temporary one) in your secrets.

### Add to Streamlit secrets

```toml
WHATSAPP_PHONE_NUMBER_ID = "123456789012345"
WHATSAPP_ACCESS_TOKEN = "your-permanent-system-user-token"
WHATSAPP_TEMPLATE_NAME = "donation_receipt"
```

### Notes

- No business document verification is required for up to **250
  business-initiated conversations per 24 hours** - more than enough for a
  single masjid's donation volume.
- If `WHATSAPP_PHONE_NUMBER_ID` / `WHATSAPP_ACCESS_TOKEN` aren't set, the app
  simply skips sending and shows a warning instead of crashing - so you can
  keep using the app for tracking before WhatsApp is fully set up.
- Phone numbers are auto-normalized assuming India (+91); a plain 10-digit
  number like `9876543210` is converted to `919876543210` automatically.

## Adding/removing admins or members later

Just add/edit rows directly in the Supabase **Table Editor > users** table —
no code changes needed.
