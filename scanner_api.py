"""
API de Escaneamento de Produtos via Câmera - VERSÃO CORRIGIDA
Sistema funcional com detecção por código digitado manualmente
"""

from flask import Flask, request, jsonify, render_template, session
from functools import wraps
import sqlite3
import base64
import hashlib
import os
import random
import string
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_desenvolvimento_123')

# Configurações
DATABASE = 'scanner_produtos.db'
UPLOAD_FOLDER = 'static/produtos_imagens'
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# Criar pasta de uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ========================================================================
# FUNÇÕES AUXILIARES
# ========================================================================

def sanitize_input(text, max_length=200):
    """Remove caracteres perigosos e limita tamanho"""
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r'[<>\"\'%;()&+]', '', text)
    return text[:max_length]


def gerar_codigo_produto():
    """Gera código único de 6 dígitos"""
    conn = get_db_connection()
    while True:
        codigo = ''.join(random.choices(string.digits, k=6))
        existe = conn.execute("SELECT id FROM produtos WHERE codigo = ?", (codigo,)).fetchone()
        if not existe:
            break
    conn.close()
    return codigo


def validar_base64_imagem(base64_string):
    """Valida se é uma imagem base64 válida"""
    try:
        if not base64_string:
            return False, "Imagem vazia"
        
        # Remove prefixo data:image
        if ',' in base64_string:
            header, data = base64_string.split(',', 1)
            # Valida tipo MIME
            if not any(mime in header for mime in ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']):
                return False, "Tipo de imagem não permitido. Use JPEG, PNG ou GIF"
        else:
            data = base64_string
        
        # Decodifica
        img_bytes = base64.b64decode(data)
        
        # Valida tamanho
        if len(img_bytes) > MAX_IMAGE_SIZE:
            return False, f"Imagem muito grande. Máximo: {MAX_IMAGE_SIZE / 1024 / 1024}MB"
        
        # Valida assinatura (magic bytes)
        if img_bytes[:2] == b'\xff\xd8':  # JPEG
            return True, "valid"
        elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
            return True, "valid"
        elif img_bytes[:6] in (b'GIF87a', b'GIF89a'):  # GIF
            return True, "valid"
        else:
            return False, "Formato de imagem inválido"
            
    except Exception as e:
        return False, f"Erro ao validar imagem: {str(e)}"


def salvar_imagem(base64_string, codigo):
    """Salva imagem em arquivo e retorna caminho"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        img_bytes = base64.b64decode(base64_string)
        
        # Detecta extensão
        if img_bytes[:2] == b'\xff\xd8':
            ext = 'jpg'
        elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            ext = 'png'
        elif img_bytes[:6] in (b'GIF87a', b'GIF89a'):
            ext = 'gif'
        else:
            ext = 'jpg'
        
        filename = f"{codigo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
        
        return filename
        
    except Exception as e:
        print(f"Erro ao salvar imagem: {e}")
        return None


def get_db_connection():
    """Retorna conexão com o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Inicializa banco de dados com índices otimizados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            localizacao TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            preco REAL DEFAULT 0.0,
            categoria TEXT DEFAULT 'Geral',
            imagem_path TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar índices para otimização
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_codigo ON produtos(codigo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_nome ON produtos(nome)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_categoria ON produtos(categoria)")
    
    # Criar usuário padrão se não existir
    cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", 
                      ('admin', 'admin123'))
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com índices otimizados!")


# ========================================================================
# AUTENTICAÇÃO
# ========================================================================

def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": "erro", "mensagem": "Autenticação necessária"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/login', methods=['POST'])
def login():
    """Login de usuário"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"status": "erro", "mensagem": "Username e password necessários"}), 400
    
    username = sanitize_input(data['username'], 50)
    password = data['password']
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            "status": "sucesso",
            "mensagem": "Login realizado com sucesso",
            "user": {"id": user['id'], "username": user['username']}
        }), 200
    
    return jsonify({"status": "erro", "mensagem": "Credenciais inválidas"}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout de usuário"""
    session.clear()
    return jsonify({"status": "sucesso", "mensagem": "Logout realizado"}), 200


# ========================================================================
# ROTAS DA API
# ========================================================================

@app.route('/')
def index():
    """Página inicial"""
    return render_template('scanner_interface.html')


def comparar_imagens(imagem1_base64, imagem2_path):
    """
    Compara duas imagens para verificar se são do mesmo produto
    Retorna True se forem similares
    """
    try:
        # Decodifica imagem capturada
        if ',' in imagem1_base64:
            imagem1_base64 = imagem1_base64.split(',', 1)[1]
        img1_bytes = base64.b64decode(imagem1_base64)
        
        # Lê imagem cadastrada
        with open(os.path.join(UPLOAD_FOLDER, imagem2_path), 'rb') as f:
            img2_bytes = f.read()
        
        # Comparação básica: hash das imagens
        # Em produção: usar OpenCV, PIL para comparação mais avançada
        hash1 = hashlib.md5(img1_bytes).hexdigest()
        hash2 = hashlib.md5(img2_bytes).hexdigest()
        
        # Se hashes idênticos (mesma imagem exata)
        if hash1 == hash2:
            return True
        
        # Comparação por tamanho similar (tolerância de 10%)
        size1 = len(img1_bytes)
        size2 = len(img2_bytes)
        
        if abs(size1 - size2) / max(size1, size2) < 0.1:
            # Compara primeiros bytes (cabeçalho similar)
            if img1_bytes[:100] == img2_bytes[:100]:
                return True
        
        return False
        
    except Exception as e:
        print(f"Erro ao comparar imagens: {e}")
        return False


@app.route('/api/scan', methods=['POST'])
@login_required
def scan_produto():
    """
    Escaneia produto via CÂMERA
    Entrada: {"imagem": "data:image/jpeg;base64,..."}
    """
    try:
        data = request.get_json()
        
        if not data or 'imagem' not in data:
            return jsonify({
                "status": "erro",
                "mensagem": "Imagem da câmera não fornecida"
            }), 400
        
        imagem_capturada = data['imagem']
        
        # Valida imagem
        valido, msg = validar_base64_imagem(imagem_capturada)
        if not valido:
            return jsonify({
                "status": "erro",
                "mensagem": f"Imagem inválida: {msg}"
            }), 400
        
        # Busca todos produtos com imagem cadastrada
        conn = get_db_connection()
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE imagem_path IS NOT NULL"
        ).fetchall()
        conn.close()
        
        # Compara imagem capturada com cada produto cadastrado
        for produto in produtos:
            if comparar_imagens(imagem_capturada, produto['imagem_path']):
                # PRODUTO ENCONTRADO!
                return jsonify({
                    "status": "encontrado",
                    "mensagem": f"✅ Produto '{produto['nome']}' identificado via câmera!",
                    "produto": {
                        "id": produto['id'],
                        "codigo": produto['codigo'],
                        "nome": produto['nome'],
                        "localizacao": produto['localizacao'],
                        "quantidade": produto['quantidade'],
                        "preco": float(produto['preco']),
                        "categoria": produto['categoria'],
                        "imagem_url": f"/static/produtos_imagens/{produto['imagem_path']}"
                    }
                }), 200
        
        # PRODUTO NÃO ENCONTRADO
        return jsonify({
            "status": "nao_encontrado",
            "alerta": "⚠️ PRODUTO NÃO CADASTRADO!",
            "mensagem": "Este produto não foi encontrado no sistema. Cadastre-o agora.",
            "imagem_capturada": imagem_capturada
        }), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao escanear: {str(e)}"}), 500


@app.route('/api/cadastrar', methods=['POST'])
@login_required
def cadastrar_produto():
    """
    Cadastra novo produto com imagem obrigatória da câmera
    """
    try:
        data = request.get_json()
        
        # Validação de campos obrigatórios (INCLUINDO IMAGEM)
        campos_obrigatorios = ['nome', 'localizacao', 'quantidade', 'imagem_base64']
        if not data or not all(k in data for k in campos_obrigatorios):
            return jsonify({
                "status": "erro",
                "mensagem": "Campos obrigatórios: nome, localizacao, quantidade e imagem_base64 (da câmera)"
            }), 400
        
        # Sanitização de inputs
        nome = sanitize_input(data['nome'], 200)
        localizacao = sanitize_input(data['localizacao'], 200)
        quantidade = int(data['quantidade'])
        preco = float(data.get('preco', 0.0))
        categoria = sanitize_input(data.get('categoria', 'Geral'), 50)
        codigo = gerar_codigo_produto()
        
        # Validações
        if not nome or not localizacao:
            return jsonify({"status": "erro", "mensagem": "Nome e localização não podem estar vazios"}), 400
        
        if quantidade < 0:
            return jsonify({"status": "erro", "mensagem": "Quantidade não pode ser negativa"}), 400
        
        if preco < 0:
            return jsonify({"status": "erro", "mensagem": "Preço não pode ser negativo"}), 400
        
        # Validar e salvar imagem (OBRIGATÓRIA)
        valido, msg = validar_base64_imagem(data['imagem_base64'])
        if not valido:
            return jsonify({"status": "erro", "mensagem": f"Imagem inválida: {msg}"}), 400
        
        imagem_path = salvar_imagem(data['imagem_base64'], codigo)
        if not imagem_path:
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar imagem da câmera"}), 500
        
        # Inserir no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO produtos (codigo, nome, localizacao, quantidade, preco, categoria, imagem_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nome, localizacao, quantidade, preco, categoria, imagem_path))
        
        produto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "sucesso",
            "mensagem": f"✅ Produto '{nome}' cadastrado com foto!",
            "produto_id": produto_id,
            "codigo": codigo,
            "instrucao": "Aponte a câmera para este produto novamente para testá-lo!"
        }), 201
        
    except ValueError as e:
        return jsonify({"status": "erro", "mensagem": "Quantidade e preço devem ser números válidos"}), 400
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao cadastrar: {str(e)}"}), 500


@app.route('/api/produto/<int:produto_id>', methods=['PUT'])
@login_required
def atualizar_produto(produto_id):
    """
    Atualiza produto existente
    """
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifica se produto existe
        produto = cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not produto:
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Produto não encontrado"}), 404
        
        # Atualiza campos fornecidos
        updates = []
        params = []
        
        if 'nome' in data:
            updates.append("nome = ?")
            params.append(sanitize_input(data['nome'], 200))
        
        if 'localizacao' in data:
            updates.append("localizacao = ?")
            params.append(sanitize_input(data['localizacao'], 200))
        
        if 'quantidade' in data:
            updates.append("quantidade = ?")
            params.append(int(data['quantidade']))
        
        if 'preco' in data:
            updates.append("preco = ?")
            params.append(float(data['preco']))
        
        if 'categoria' in data:
            updates.append("categoria = ?")
            params.append(sanitize_input(data['categoria'], 50))
        
        updates.append("atualizado_em = ?")
        params.append(datetime.now())
        
        if not updates:
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Nenhum campo para atualizar"}), 400
        
        params.append(produto_id)
        
        cursor.execute(f"UPDATE produtos SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "Produto atualizado com sucesso"
        }), 200
        
    except ValueError:
        return jsonify({"status": "erro", "mensagem": "Valores numéricos inválidos"}), 400
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao atualizar: {str(e)}"}), 500


@app.route('/api/produtos', methods=['GET'])
@login_required
def listar_produtos():
    """Lista todos produtos"""
    try:
        conn = get_db_connection()
        produtos = conn.execute(
            "SELECT * FROM produtos ORDER BY nome"
        ).fetchall()
        conn.close()
        
        lista = [{
            "id": p['id'],
            "codigo": p['codigo'],
            "nome": p['nome'],
            "localizacao": p['localizacao'],
            "quantidade": p['quantidade'],
            "preco": float(p['preco']),
            "categoria": p['categoria'],
            "imagem_url": f"/static/produtos_imagens/{p['imagem_path']}" if p['imagem_path'] else None
        } for p in produtos]
        
        return jsonify({
            "status": "sucesso",
            "total": len(lista),
            "produtos": lista
        }), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro: {str(e)}"}), 500


@app.route('/api/produto/<int:produto_id>', methods=['GET'])
@login_required
def obter_produto(produto_id):
    """Obtém produto específico"""
    try:
        conn = get_db_connection()
        produto = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        conn.close()
        
        if not produto:
            return jsonify({"status": "erro", "mensagem": "Produto não encontrado"}), 404
        
        return jsonify({
            "status": "sucesso",
            "produto": {
                "id": produto['id'],
                "codigo": produto['codigo'],
                "nome": produto['nome'],
                "localizacao": produto['localizacao'],
                "quantidade": produto['quantidade'],
                "preco": float(produto['preco']),
                "categoria": produto['categoria'],
                "imagem_url": f"/static/produtos_imagens/{produto['imagem_path']}" if produto['imagem_path'] else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro: {str(e)}"}), 500


@app.route('/api/produto/<int:produto_id>', methods=['DELETE'])
@login_required
def deletar_produto(produto_id):
    """Deleta produto"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Busca imagem para deletar arquivo
        produto = cursor.execute("SELECT imagem_path FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        
        if not produto:
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Produto não encontrado"}), 404
        
        # Deleta do banco
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conn.commit()
        conn.close()
        
        # Deleta arquivo de imagem se existir
        if produto['imagem_path']:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, produto['imagem_path']))
            except:
                pass
        
        return jsonify({"status": "sucesso", "mensagem": "Produto deletado"}), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro: {str(e)}"}), 500


# ========================================================================
# DOCUMENTAÇÃO DA API
# ========================================================================

@app.route('/api/docs')
def api_docs():
    """Documentação simples da API"""
    docs = {
        "titulo": "API de Scanner de Produtos",
        "versao": "2.0",
        "endpoints": {
            "POST /api/login": {
                "descricao": "Login de usuário",
                "entrada": {"username": "admin", "password": "admin123"},
                "autenticacao": False
            },
            "POST /api/logout": {
                "descricao": "Logout de usuário",
                "autenticacao": True
            },
            "POST /api/scan": {
                "descricao": "Escaneia produto por código",
                "entrada": {"codigo": "123456"},
                "autenticacao": True
            },
            "POST /api/cadastrar": {
                "descricao": "Cadastra novo produto",
                "entrada": {
                    "nome": "Mouse Gamer",
                    "localizacao": "Prateleira A1",
                    "quantidade": 10,
                    "preco": 89.90,
                    "categoria": "Eletrônicos",
                    "imagem_base64": "opcional"
                },
                "autenticacao": True
            },
            "GET /api/produtos": {
                "descricao": "Lista todos produtos",
                "autenticacao": True
            },
            "GET /api/produto/<id>": {
                "descricao": "Obtém produto específico",
                "autenticacao": True
            },
            "PUT /api/produto/<id>": {
                "descricao": "Atualiza produto",
                "autenticacao": True
            },
            "DELETE /api/produto/<id>": {
                "descricao": "Deleta produto",
                "autenticacao": True
            }
        },
        "usuario_padrao": {
            "username": "admin",
            "password": "admin123"
        }
    }
    return jsonify(docs), 200


# ========================================================================
# EXECUÇÃO
# ========================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔍 API DE SCANNER DE PRODUTOS - VERSÃO CORRIGIDA")
    print("="*70)
    
    init_database()
    
    print("\n📡 API Endpoints:")
    print("  POST /api/login          - Login (admin/admin123)")
    print("  POST /api/scan           - Escanear por código")
    print("  POST /api/cadastrar      - Cadastrar produto")
    print("  GET  /api/produtos       - Listar produtos")
    print("  PUT  /api/produto/<id>   - Atualizar produto")
    print("  DELETE /api/produto/<id> - Deletar produto")
    print("  GET  /api/docs           - Documentação completa")
    
    print("\n🔐 Credenciais padrão:")
    print("  Username: admin")
    print("  Password: admin123")
    
    print("\n🚀 Servidor iniciando...")
    print("   Acesse: http://localhost:5001")
    print("="*70 + "\n")
    
    # Configuração segura
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False') == 'True'
    
    app.run(debug=debug, port=port, host='0.0.0.0')
