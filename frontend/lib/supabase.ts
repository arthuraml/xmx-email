import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://gtydmzumlicopgkddabh.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd0eWRtenVtbGljb3Bna2RkYWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxNjg0OTMsImV4cCI6MjA2OTc0NDQ5M30.p8HyAxHjHSgubSzJE9AzrUKzwnGNMY7v42q2VQkXa1Q'

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  }
})