# 📡 API de Escaneamento de Produtos - Documentação

## Visão Geral

API REST para escaneamento e identificação de produtos em tempo real através de imagens capturadas por câmera. O sistema identifica produtos cadastrados e alerta quando produtos não cadastrados são detectados.

---

## 🔑 Autenticação

A maioria dos endpoints requer autenticação via sessão do Flask. O usuário deve estar logado no sistema.

---

## 📍 Endpoints da API

### 1️⃣ Escanear Produto

**POST** `/api/escanear`

Escaneia uma imagem para identificar um produto. Retorna informações completas se o produto estiver cadastrado, ou um alerta caso contrário.

#### Request Body:
```json
{
  "imagem": "data:image/jpeg;base64,/9j/4AAQSkZJRg..." // Imagem em base64
}
```

#### Response - Produto Encontrado (200):
```json
{
  "sucesso": true,
  "encontrado": true,
  "produto": {
    "id": 1,
    "nome": "notebook dell",
    "quantidade": 15,
    "localizacao": "Coluna 3, Linha 2, Centro",
    "preco": 3500.00,
    "coluna": 3,
    "nivel": 2,
    "posicao": "Centro",
    "imagem": "base64_encoded_image..."
  },
  "mensagem": "Produto 'notebook dell' identificado com sucesso!"
}
```

#### Response - Produto NÃO Encontrado (200):
```json
{
  "sucesso": true,
  "encontrado": false,
  "alerta": "⚠️ PRODUTO NÃO CADASTRADO",
  "mensagem": "Este produto não está registrado no sistema. Por favor, realize o cadastro.",
  "acao_requerida": "cadastro"
}
```

#### Response - Erro (400/500):
```json
{
  "sucesso": false,
  "erro": "Nenhuma imagem recebida"
}
```

---

### 2️⃣ Cadastrar Produto Escaneado

**POST** `/api/cadastrar_produto_escaneado`

Cadastra rapidamente um produto que foi escaneado mas não foi encontrado no sistema.

**Requer autenticação!**

#### Request Body:
```json
{
  "nome": "mouse logitech",
  "quantidade": 50,
  "preco": 89.90,
  "coluna": 2,
  "linha": 1,
  "posicao": "Esquerda",
  "imagem": "data:image/jpeg;base64,..." // Opcional
}
```

#### Response - Sucesso (201):
```json
{
  "sucesso": true,
  "mensagem": "Produto 'mouse logitech' cadastrado com sucesso!",
  "produto_id": 15
}
```

#### Response - Erro (400/401):
```json
{
  "erro": "Campos obrigatórios faltando"
}
```

---

### 3️⃣ Listar Todos os Produtos

**GET** `/api/produtos`

Retorna lista completa de todos os produtos cadastrados no sistema.

#### Response (200):
```json
{
  "sucesso": true,
  "total": 25,
  "produtos": [
    {
      "id": 1,
      "nome": "notebook dell",
      "quantidade": 15,
      "preco": 3500.00,
      "localizacao": "Coluna 3, Linha 2, Centro",
      "coluna": 3,
      "nivel": 2,
      "posicao": "Centro",
      "imagem": "base64_encoded_image..."
    },
    {
      "id": 2,
      "nome": "mouse logitech",
      "quantidade": 50,
      "preco": 89.90,
      "localizacao": "Coluna 2, Linha 1, Esquerda",
      "coluna": 2,
      "nivel": 1,
      "posicao": "Esquerda",
      "imagem": ""
    }
  ]
}
```

---

### 4️⃣ Obter Produto Específico

**GET** `/api/produto/<produto_id>`

Retorna informações detalhadas de um produto específico por ID.

#### Response - Sucesso (200):
```json
{
  "sucesso": true,
  "produto": {
    "id": 1,
    "nome": "notebook dell",
    "quantidade": 15,
    "preco": 3500.00,
    "localizacao": "Coluna 3, Linha 2, Centro",
    "coluna": 3,
    "nivel": 2,
    "posicao": "Centro",
    "imagem": "base64_encoded_image..."
  }
}
```

#### Response - Não Encontrado (404):
```json
{
  "erro": "Produto não encontrado"
}
```

---

## 🌐 Páginas Web

### Scanner em Tempo Real

**GET** `/scanner`

Interface web interativa para escanear produtos usando a câmera em tempo real.

**Requer autenticação!**

Funcionalidades:
- ✅ Ativação de câmera
- ✅ Captura de imagem em tempo real
- ✅ Identificação automática de produtos
- ✅ Exibição de informações do produto
- ✅ Formulário de cadastro rápido para produtos não encontrados

---

## 🔧 Como Usar

### Exemplo 1: Escanear produto com JavaScript

```javascript
// Capturar imagem da câmera
const canvas = document.getElementById('canvas');
const video = document.getElementById('video');
canvas.getContext('2d').drawImage(video, 0, 0);
const imagemBase64 = canvas.toDataURL('image/jpeg');

// Enviar para API
const response = await fetch('/api/escanear', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ imagem: imagemBase64 })
});

const resultado = await response.json();

if (resultado.encontrado) {
  console.log('Produto encontrado:', resultado.produto);
} else {
  console.log('Alerta:', resultado.alerta);
  // Mostrar formulário de cadastro
}
```

### Exemplo 2: Cadastrar produto após escaneamento

```javascript
const dadosProduto = {
  nome: 'Teclado Mecânico',
  quantidade: 10,
  preco: 299.90,
  coluna: 1,
  linha: 3,
  posicao: 'Direita',
  imagem: imagemBase64 // Imagem capturada anteriormente
};

const response = await fetch('/api/cadastrar_produto_escaneado', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(dadosProduto)
});

const resultado = await response.json();
console.log(resultado.mensagem);
```

### Exemplo 3: Listar todos os produtos

```javascript
const response = await fetch('/api/produtos');
const data = await response.json();

console.log(`Total de produtos: ${data.total}`);
data.produtos.forEach(produto => {
  console.log(`${produto.nome} - R$ ${produto.preco}`);
});
```

---

## 🚀 Executar o Sistema

```bash
python main.py
```

Acesse: `http://localhost:5000/scanner`

---

## 📝 Notas Importantes

1. **Identificação de Imagem**: Atualmente usa hash MD5 para comparação de imagens. Em produção, deve ser substituído por modelo de IA (YOLO, TensorFlow, etc.)

2. **Segurança**: Endpoints de cadastro requerem autenticação. Certifique-se de estar logado.

3. **Formato de Imagem**: As imagens devem ser enviadas em base64. O sistema aceita o prefixo `data:image/...;base64,` que será removido automaticamente.

4. **Câmera**: A página `/scanner` solicita permissão para acessar a câmera do dispositivo. Funciona melhor com câmera traseira em dispositivos móveis.

---

## 🎯 Fluxo de Trabalho

```
1. Usuário aponta câmera para produto
   ↓
2. Sistema captura imagem
   ↓
3. API /escanear processa imagem
   ↓
4. Produto encontrado? 
   ├─ SIM → Exibe informações (nome, quantidade, localização, preço)
   └─ NÃO → Exibe alerta + formulário de cadastro
              ↓
              API /cadastrar_produto_escaneado
              ↓
              Produto cadastrado no sistema
```

---

## 🛠️ Tecnologias

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **API**: REST (JSON)
- **Processamento de Imagem**: PIL, Base64, Hashlib

---

## 📞 Suporte

Para dúvidas ou problemas, consulte o código fonte em [main.py](main.py).
