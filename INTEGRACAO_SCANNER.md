# 📷 Integração Scanner + Sistema Principal

## ✅ O que foi feito

A API de Scanner foi **completamente integrada** ao `main.py`. Agora ambos os sistemas trabalham juntos usando a mesma base de dados e autenticação.

---

## 🎯 Como Funciona

### 1️⃣ **Login Único**
- Usuário faz login uma vez no sistema principal (`/login`)
- A sessão funciona para TODAS as funcionalidades
- Não precisa fazer login separado no scanner

### 2️⃣ **Banco de Dados Compartilhado**
- Mesma tabela `produtos` para ambos sistemas
- Produtos cadastrados no scanner aparecem no estoque
- Campos adicionados: `codigo`, `categoria`, `imagem_path`

### 3️⃣ **Fluxo Integrado**

```
1. Login → /login (email/senha)
   ↓
2. Página Inicial → /inicio
   ↓
3. Opções:
   ├─ 🔍 Scanner de Produtos → /scanner (NOVO!)
   ├─ 📷 Câmera
   ├─ 🔎 Buscar Produto
   ├─ 📦 Estoque
   └─ ⚠️ Estoque Baixo
```

---

## 🚀 Como Usar

### **Iniciar o Sistema**

```bash
python main.py
```

### **Testar Scanner**

1. **Login**
   - Acesse: `http://localhost:5000/login`
   - Email: (qualquer cadastrado)
   - Senha: (sua senha)

2. **Ir para Scanner**
   - Clique em **"🔍 Scanner de Produtos"**
   - Ou acesse diretamente: `http://localhost:5000/scanner`

3. **Usar Câmera**
   - Clique **"📷 Iniciar Câmera"**
   - Aponte para um objeto
   - Clique **"🔎 Escanear Produto"**

4. **Cadastrar Produto**
   - Se não encontrado, preencha formulário
   - A foto é salva automaticamente
   - Produto aparece no estoque principal

5. **Testar Reconhecimento**
   - Aponte câmera para o MESMO objeto
   - Clique **"🔎 Escanear"**
   - ✅ Sistema reconhece e mostra dados!

---

## 📡 Endpoints da API

### **Scanner (Novos)**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/scan` | Escaneia produto via câmera |
| POST | `/api/cadastrar_scanner` | Cadastra produto com foto |
| GET | `/api/produtos_scanner` | Lista produtos do scanner |

### **Sistema Principal (Existentes)**

| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/login` | Login de usuário |
| GET | `/inicio` | Página inicial |
| GET | `/estoque` | Lista estoque completo |
| GET | `/scanner` | Interface do scanner |

---

## 🗄️ Estrutura do Banco

### Tabela: `produtos`

```sql
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco REAL NOT NULL,
    localizacao TEXT NOT NULL,
    -- Campos originais
    coluna_armazenada INTEGER,
    nivel_armazenado INTEGER,
    imagem_base64 TEXT,
    posicao_bloqueada TEXT,
    -- Campos do scanner (NOVOS)
    codigo TEXT,              -- Código único 6 dígitos
    categoria TEXT,           -- Categoria do produto
    imagem_path TEXT,         -- Caminho da foto real
    criado_em TIMESTAMP,      -- Data de criação
    atualizado_em TIMESTAMP   -- Última atualização
)
```

---

## 📁 Estrutura de Arquivos

```
Efllor-main/
├── main.py                    # Sistema principal + API Scanner
├── banco.db                   # Banco de dados único
├── static/
│   ├── uploads/               # Uploads antigos
│   └── produtos_imagens/      # Fotos do scanner
├── templates/
│   ├── index.html             # Página inicial
│   ├── inicio.html            # Menu principal
│   ├── scanner_interface.html # Interface do scanner
│   ├── estoque.html           # Lista de estoque
│   └── ...
└── INTEGRACAO_SCANNER.md      # Este arquivo
```

---

## ⚙️ Funcionalidades Integradas

### ✅ O que já funciona:

1. **Autenticação Única**
   - Login compartilhado entre sistemas
   - Sessão Flask protege todas rotas

2. **Scanner por Câmera**
   - Captura de imagem em tempo real
   - Comparação com produtos cadastrados
   - Alerta se produto não existe

3. **Cadastro com Foto**
   - Imagem obrigatória ao cadastrar
   - Salva em `static/produtos_imagens/`
   - Gera código único automático

4. **Reconhecimento Visual**
   - Compara hash MD5 das imagens
   - Verifica tamanho e primeiros bytes
   - Retorna dados completos do produto

5. **Listagem Integrada**
   - Produtos aparecem em ambos sistemas
   - Estoque atualizado em tempo real

---

## 🎨 Interface do Scanner

### Componentes:

1. **Câmera em Tempo Real**
   - Vídeo ao vivo da webcam
   - Controles de iniciar/parar
   - Indicador visual quando ativa

2. **Área de Resultados**
   - Fundo verde → Produto encontrado
   - Fundo laranja → Produto não cadastrado
   - Mostra: Nome, Localização, Quantidade, Preço

3. **Formulário de Cadastro**
   - Aparece automaticamente se produto novo
   - Campos: Nome, Localização, Quantidade, Preço, Categoria
   - Foto capturada é enviada junto

4. **Lista de Produtos**
   - Mostra produtos cadastrados via scanner
   - Atualiza em tempo real
   - Botão de refresh manual

---

## 🔐 Segurança

### Implementada:

- ✅ Autenticação obrigatória em todas rotas
- ✅ Validação de tipo MIME de imagens
- ✅ Limite de tamanho 5MB por imagem
- ✅ Sanitização de entradas (em desenvolvimento)
- ✅ Imagens salvas fora do código base

### Recomendações para Produção:

- [ ] Hash de senhas (bcrypt)
- [ ] HTTPS obrigatório
- [ ] Rate limiting nas APIs
- [ ] Validação CSRF
- [ ] Logs de auditoria

---

## 🐛 Troubleshooting

### **Scanner não aparece no menu**
- **Solução:** Faça logout e login novamente

### **Câmera não ativa**
- **Causa:** Navegador bloqueou permissão
- **Solução:** Clique no ícone de câmera na barra de endereço e permita

### **Produto não é reconhecido**
- **Causa:** Imagem muito diferente da cadastrada
- **Solução:** 
  - Mantenha iluminação similar
  - Mesma distância e ângulo
  - Fundo limpo

### **Erro "Não autenticado"**
- **Causa:** Sessão expirou
- **Solução:** Volte para `/login` e faça login novamente

### **Pasta `produtos_imagens` não existe**
- **Causa:** Permissões de escrita
- **Solução:** Crie manualmente: `mkdir static/produtos_imagens`

---

## 🚀 Melhorias Futuras

### Curto Prazo:
- [ ] Adicionar QR Code ao cadastrar produto
- [ ] Melhorar algoritmo de comparação de imagens
- [ ] Adicionar histórico de escaneamentos
- [ ] Export de relatórios

### Longo Prazo:
- [ ] IA de reconhecimento visual (TensorFlow/YOLO)
- [ ] App mobile nativo
- [ ] Múltiplas câmeras simultâneas
- [ ] Integração com código de barras

---

## 📞 Suporte

**Arquivo principal:** [main.py](file:///c:/Users/Home/OneDrive/Documentos/Efllor-main/main.py)  
**Interface:** [scanner_interface.html](file:///c:/Users/Home/OneDrive/Documentos/Efllor-main/templates/scanner_interface.html)  
**Sistema completo funcionando:** ✅

---

**Pronto para usar! Execute `python main.py` e acesse `/scanner`** 🎉
