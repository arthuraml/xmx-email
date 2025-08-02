// Script alternativo usando o cliente Supabase existente
// Este script deve ser executado no contexto do projeto Next.js

const { createClient } = require('@supabase/supabase-js')

// Usar as mesmas configurações do projeto
const supabaseUrl = 'https://gtydmzumlicopgkddabh.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd0eWRtenVtbGljb3Bna2RkYWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxNjg0OTMsImV4cCI6MjA2OTc0NDQ5M30.p8HyAxHjHSgubSzJE9AzrUKzwnGNMY7v42q2VQkXa1Q'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function createAdminUser() {
  console.log('🚀 Criando usuário admin usando signUp...')

  try {
    // Usar signUp que está disponível com anon key
    const { data, error } = await supabase.auth.signUp({
      email: 'admin@xmx.com',
      password: 'xmx123',
      options: {
        data: {
          username: 'admin',
          role: 'admin'
        }
      }
    })

    if (error) {
      console.error('❌ Erro ao criar usuário:', error.message)
      return
    }

    console.log('✅ Usuário criado com sucesso!')
    
    if (data.user) {
      console.log('📧 Email:', data.user.email)
      console.log('🆔 ID:', data.user.id)
      console.log('✉️  Status de confirmação:', data.user.email_confirmed_at ? 'Confirmado' : 'Aguardando confirmação')
    }
    
    console.log('\n🔑 Credenciais de login:')
    console.log('   Email: admin@xmx.com')
    console.log('   Senha: xmx123')
    
    if (!data.user?.email_confirmed_at) {
      console.log('\n⚠️  Nota: O email precisa ser confirmado. Por padrão em desenvolvimento local, a confirmação é automática.')
    }
    
    console.log('\n🎉 Tente fazer login agora!')

  } catch (err) {
    console.error('❌ Erro inesperado:', err)
  }
}

// Executar a criação do usuário
createAdminUser()