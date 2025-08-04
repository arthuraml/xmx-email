# Configuração do Supabase MCP - Passo a Passo

## 1. Project Reference ✅
Seu project reference está correto:
```
SUPABASE_PROJECT_REF=gtydmzumlicopgkddabh
```

## 2. Personal Access Token - Como obter:

1. **Clique no seu avatar** no canto superior direito do Supabase Dashboard
2. Selecione **"Account Settings"** ou **"User Settings"**
3. No menu lateral, procure por **"Access Tokens"**
4. Clique em **"Generate New Token"**
5. Dê um nome ao token (ex: "claude-code-mcp")
6. Copie o token gerado - **IMPORTANTE: Ele só será mostrado uma vez!**

## 3. Configure seu arquivo .env:

```env
SUPABASE_PROJECT_REF=gtydmzumlicopgkddabh
SUPABASE_ACCESS_TOKEN=sbp_[seu_token_aqui]
```

## Nota Importante:
- O Personal Access Token começa com `sbp_`
- As API Keys que você vê no projeto (publishable e secret) são para uso direto nas aplicações
- O MCP precisa de um Personal Access Token vinculado à sua conta de usuário

## Para testar após configurar:
```bash
# No Claude Code
/mcp
```

Se aparecer "supabase" na lista, a configuração está correta!