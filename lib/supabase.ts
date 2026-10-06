import { env } from "cloudflare:workers";
import { createClient } from "@supabase/supabase-js";

export function getSupabase() {
  return createClient(env.SUPABASE_URL, env.SUPABASE_KEY, {
    auth: { persistSession: false },
  });
}
