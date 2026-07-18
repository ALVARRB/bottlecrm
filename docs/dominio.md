# Domínio Customizado — Guia de Configuração

## Subdomínio
**crm.allshoptotal.com** → apontar para o Render

## Passo a Passo

### 1. No seu provedor de domínio (registro.br, GoDaddy, etc.)
Criar um registro CNAME:

| Tipo | Nome | Valor |
|------|------|-------|
| CNAME | `crm` | `bottlecrm-frontend.onrender.com` |

### 2. No Render Dashboard
- Acessar: https://dashboard.render.com
- Ir em: **bottlecrm-frontend** → **Settings** → **Custom Domain**
- Adicionar: `crm.allshoptotal.com`
- Render vai gerar um valor de verificação DNS
- Voltar ao provedor de domínio e adicionar o registro TXT de verificação
- Após verificação, Render emite SSL grátis (Let's Encrypt)

### 3. Backend (API)
Repetir o processo para o backend se quiser:

| Tipo | Nome | Valor |
|------|------|-------|
| CNAME | `api` | `bottlecrm.onrender.com` |

Render: **bottlecrm** → **Settings** → **Custom Domain** → `api.allshoptotal.com`

### 4. Atualizar variáveis de ambiente no Render
Após o domínio estar ativo:
- `bottlecrm` (backend): `ALLOWED_HOSTS` → adicionar `crm.allshoptotal.com,api.allshoptotal.com`
- `bottlecrm` (backend): `DOMAIN_NAME` → `https://crm.allshoptotal.com`
- `bottlecrm` (backend): `PUBLIC_DJANGO_API_URL` → `https://api.allshoptotal.com` (ou `https://crm.allshoptotal.com` se for same-origin)
- `bottlecrm-frontend`: `PUBLIC_DJANGO_API_URL` → `https://api.allshoptotal.com`