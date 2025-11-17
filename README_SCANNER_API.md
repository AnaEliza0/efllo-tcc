# 🔍 API de Escaneamento de Produtos

## 📋 Descrição

API completa para escaneamento e identificação de produtos através de câmera em tempo real. O sistema identifica produtos cadastrados mostrando suas informações, e envia alerta quando produtos não cadastrados são detectados.

---

## 🚀 Como Executar

### 1️⃣ Instalar Dependências

```bash
pip install flask pillow
```

### 2️⃣ Executar a API

```bash
python scanner_api.py
```

### 3️⃣ Acessar Interface

Abra seu navegador em: **http://localhost:5001**

---

## 📡 Endpoints da API

### **POST /api/scan**
Escaneia uma imagem para identificar produto

**Request:**
```json
{
  "imagem": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response - Produto Encontrado:**
```json
{
  "status": "encontrado",
  "mensagem": "✅ Produto 'Mouse Logitech' identificado com sucesso!",
  "produto": {
    "id": 1,
    "nome": "Mouse Logitech",
    "localizacao": "Prateleira A1",
    "quantidade": 50,
    "preco": 89.90,
    "categoria": "Eletrônicos"
  }
}
```

**Response - Produto NÃO Encontrado:**
```json
{
  "status": "nao_encontrado",
  "alerta": "⚠️ PRODUTO NÃO CADASTRADO!",
  "mensagem": "Este produto não foi encontrado no sistema. Por favor, cadastre-o.",
  "imagem_hash": "a1b2c3d4e5f6"
}
```

---

### **POST /api/cadastrar**
Cadastra novo produto no sistema

**Request:**
```json
{
  "nome": "Mouse Logitech",
  "localizacao": "Prateleira A1",
  "quantidade": 50,
  "preco": 89.90,
  "categoria": "Eletrônicos",
  "imagem_base64": "...",
  "imagem_hash": "..."
}
```

**Response:**
```json
{
  "status": "sucesso",
  "mensagem": "✅ Produto 'Mouse Logitech' cadastrado com sucesso!",
  "produto_id": 1
}
```

---

### **GET /api/produtos**
Lista todos produtos cadastrados

**Response:**
```json
{
  "status": "sucesso",
  "total": 5,
  "produtos": [
    {
      "id": 1,
      "nome": "Mouse Logitech",
      "localizacao": "Prateleira A1",
      "quantidade": 50,
      "preco": 89.90,
      "categoria": "Eletrônicos"
    }
  ]
}
```

---

### **GET /api/produto/<id>**
Obtém detalhes de produto específico

**Response:**
```json
{
  "status": "sucesso",
  "produto": {
    "id": 1,
    "nome": "Mouse Logitech",
    "localizacao": "Prateleira A1",
    "quantidade": 50,
    "preco": 89.90,
    "categoria": "Eletrônicos",
    "imagem": "base64_string..."
  }
}
```

---

### **DELETE /api/produto/<id>**
Deleta um produto

**Response:**
```json
{
  "status": "sucesso",
  "mensagem": "Produto deletado com sucesso"
}
```

---

## 🎯 Fluxo de Funcionamento

```
┌─────────────────────────────────────────┐
│  1. Usuário aponta câmera para produto  │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  2. Sistema captura imagem (JPEG)       │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  3. Gera hash SHA-256 da imagem         │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  4. Busca produto no banco por hash     │
└──────────────┬──────────────────────────┘
               ▼
        ┌──────┴───────┐
        ▼              ▼
┌──────────────┐  ┌──────────────────┐
│  ENCONTRADO  │  │  NÃO ENCONTRADO  │
└──────┬───────┘  └────────┬─────────┘
       ▼                   ▼
┌──────────────┐  ┌──────────────────┐
│ Exibe:       │  │ Exibe:           │
│ • Nome       │  │ • Alerta         │
│ • Localização│  │ • Form cadastro  │
│ • Quantidade │  └────────┬─────────┘
│ • Preço      │           ▼
└──────────────┘  ┌──────────────────┐
                  │ Usuário cadastra │
                  │ novo produto     │
                  └──────────────────┘
```

---

## 🎨 Interface Web

A interface possui duas colunas:

### **Coluna Esquerda - Scanner**
- 📷 Visualização da câmera em tempo real
- 🔘 Botões de controle (Iniciar, Escanear, Parar)
- 📊 Área de resultados do escaneamento
- 📝 Formulário de cadastro (quando produto não encontrado)

### **Coluna Direita - Lista de Produtos**
- 📦 Lista de todos produtos cadastrados
- 🔄 Botão de atualizar lista
- 📋 Informações resumidas de cada produto

---

## 🔐 Segurança

- ✅ Identificação por hash SHA-256 da imagem
- ✅ Validação de campos obrigatórios
- ✅ Proteção contra duplicatas
- ✅ Tratamento de erros robusto

---

## 💾 Banco de Dados

**Tabela: produtos**
```sql
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    localizacao TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco REAL,
    categoria TEXT,
    imagem_hash TEXT UNIQUE,
    imagem_base64 TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Flask (Python)
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, JavaScript Vanilla
- **API:** REST (JSON)
- **Câmera:** MediaDevices API
- **Processamento:** Base64, SHA-256 Hash

---

## 📝 Exemplo de Uso com JavaScript

```javascript
// Capturar imagem da câmera
const canvas = document.getElementById('canvas');
const video = document.getElementById('video');
canvas.getContext('2d').drawImage(video, 0, 0);
const imagemBase64 = canvas.toDataURL('image/jpeg');

// Escanear produto
const response = await fetch('/api/scan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ imagem: imagemBase64 })
});

const resultado = await response.json();

if (resultado.status === 'encontrado') {
  console.log('Produto:', resultado.produto.nome);
  console.log('Localização:', resultado.produto.localizacao);
  console.log('Quantidade:', resultado.produto.quantidade);
} else {
  console.log('Alerta:', resultado.alerta);
  // Mostrar formulário de cadastro
}
```

---

## ⚙️ Configurações

**Porta do servidor:** 5001 (pode ser alterada em `scanner_api.py`)

**Banco de dados:** `scanner_produtos.db` (criado automaticamente)

---

## 📞 Comandos Úteis

```bash
# Executar em modo debug
python scanner_api.py

# Acessar de outro dispositivo na mesma rede
# Use o IP da máquina:
http://192.168.x.x:5001
```

---

## 🎓 Notas Importantes

1. **Identificação de Imagem:** Sistema usa hash SHA-256 para comparação. Em produção, considere usar modelos de IA (YOLO, TensorFlow, etc.)

2. **Permissões:** Browser solicitará permissão para usar câmera

3. **HTTPS:** Para produção, use HTTPS (obrigatório para câmera em alguns browsers)

4. **Performance:** Imagens são comprimidas em JPEG (qualidade 80%) para otimizar transferência

---

## ✅ Pronto para Usar!

Execute `python scanner_api.py` e acesse `http://localhost:5001`
