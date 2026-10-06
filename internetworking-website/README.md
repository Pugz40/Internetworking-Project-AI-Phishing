# Phishing email quiz (vinext + Supabase)

Shows a random email from Supabase `human_emails`; clicking **Fake** / **Real** records the answer
in `quiz_sessions` and `user_results`.

## Setup

1. Copy `.dev.vars.example` to `.dev.vars` and fill in:
   - `SUPABASE_URL` — project base URL, e.g. `https://xxxx.supabase.co` (no `/rest/v1/`)
   - `SUPABASE_KEY` — the publishable (anon) key
2. Run this once in the Supabase SQL editor (draft-level RLS policies for the anon role):

   ```sql
   alter table human_emails  enable row level security;
   alter table quiz_sessions enable row level security;
   alter table user_results  enable row level security;

   create policy "anon read emails"     on human_emails  for select to anon using (true);
   create policy "anon read sessions"   on quiz_sessions for select to anon using (true);
   create policy "anon insert sessions" on quiz_sessions for insert to anon with check (true);
   create policy "anon insert results"  on user_results  for insert to anon with check (true);
   ```
3. For Cloudflare, add `SUPABASE_URL` and `SUPABASE_KEY` under the Worker's
   Settings → Variables and Secrets (or `npx wrangler secret put SUPABASE_KEY`).

## Scripts

- `npm run dev` starts the vinext dev server.
- `npm run build` builds the Cloudflare Worker output.
- `npm run start` starts the built Worker locally with Wrangler.
- `npm run deploy` deploys the Cloudflare Worker.
- `npm run cf-typegen` regenerates `worker-configuration.d.ts` after changing vars/bindings.
