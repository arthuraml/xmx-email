const { createClient } = require('@supabase/supabase-js')

// Configurações do Supabase
const supabaseUrl = 'https://gtydmzumlicopgkddabh.supabase.co'
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseServiceKey) {
  console.error('❌ Erro: SUPABASE_SERVICE_ROLE_KEY não está definida')
  console.log('Por favor, defina a variável de ambiente:')
  console.log('export SUPABASE_SERVICE_ROLE_KEY="sua-service-role-key"')
  process.exit(1)
}

// Criar cliente Supabase com service role key (bypass RLS)
const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

async function createAdminUser() {
  console.log('🚀 Criando usuário admin...')

  try {
    // Criar usuário usando a API Admin
    const { data, error } = await supabase.auth.admin.createUser({
      email: 'admin@xmx.com',
      password: 'xmx123',
      email_confirm: true,
      user_metadata: {
        username: 'admin',
        role: 'admin'
      }
    })

    if (error) {
      console.error('❌ Erro ao criar usuário:', error.message)
      return
    }

    console.log('✅ Usuário admin criado com sucesso!')
    console.log('📧 Email:', data.user.email)
    console.log('🆔 ID:', data.user.id)
    console.log('🔑 Senha: xmx123')
    console.log('\n🎉 Você pode fazer login com essas credenciais!')

  } catch (err) {
    console.error('❌ Erro inesperado:', err)
  }
}

// Executar a criação do usuário
createAdminUser()