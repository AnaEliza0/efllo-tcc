from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import sqlite3
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image
import hashlib
import random
import string
import re
from datetime import datetime
import qrcode

app = Flask(__name__)
app.secret_key = 'troque_esse_seguro_para_uma_chave_real'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SCANNER_FOLDER'] = 'static/produtos_imagens'
app.config['QRCODE_FOLDER'] = 'static/qrcodes'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SCANNER_FOLDER'], exist_ok=True)
os.makedirs(app.config['QRCODE_FOLDER'], exist_ok=True)

# Configurações da API Scanner
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


# -----------------------------------------------------------
# BANCO DE DADOS
# -----------------------------------------------------------

def get_db():
    conn = sqlite3.connect('banco.db')
    conn.row_factory = sqlite3.Row
    return conn


def ensure_columns(cursor):
    cursor.execute("PRAGMA table_info(produtos)")
    existing = [row[1] for row in cursor.fetchall()]

    campos = {
        "coluna_armazenada": "INTEGER",
        "nivel_armazenado": "INTEGER",
        "imagem_base64": "TEXT",
        "posicao_bloqueada": "TEXT",
        "codigo": "TEXT",
        "categoria": "TEXT",
        "imagem_path": "TEXT",
        "criado_em": "TIMESTAMP",
        "atualizado_em": "TIMESTAMP"
    }

    for coluna, tipo in campos.items():
        if coluna not in existing:
            cursor.execute(f"ALTER TABLE produtos ADD COLUMN {coluna} {tipo}")
    
    # Criar índices se não existirem
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_codigo ON produtos(codigo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_nome ON produtos(nome)")
    except:
        pass


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco REAL NOT NULL,
            localizacao TEXT NOT NULL
        )
    """)

    ensure_columns(cursor)
    conn.commit()
    conn.close()


init_db()


# -----------------------------------------------------------
# FUNÇÕES AUXILIARES DA API SCANNER
# -----------------------------------------------------------

def gerar_codigo_produto():
    """Gera código único de 6 dígitos"""
    conn = get_db()
    while True:
        codigo = ''.join(random.choices(string.digits, k=6))
        existe = conn.execute("SELECT id FROM produtos WHERE codigo = ?", (codigo,)).fetchone()
        if not existe:
            break
    conn.close()
    return codigo


def gerar_qrcode(codigo, nome_produto):
    """Gera QR Code para o produto"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(codigo)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_filename = f"{codigo}.png"
        qr_path = os.path.join(app.config['QRCODE_FOLDER'], qr_filename)
        img.save(qr_path)
        
        print(f"✅ QR Code gerado: {qr_path}")
        return qr_filename
        
    except Exception as e:
        print(f"❌ Erro ao gerar QR Code: {e}")
        return None


def validar_base64_imagem(base64_string):
    """Valida se é uma imagem base64 válida"""
    try:
        if not base64_string:
            return False, "Imagem vazia"
        
        if ',' in base64_string:
            header, data = base64_string.split(',', 1)
            if not any(mime in header for mime in ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']):
                return False, "Tipo de imagem não permitido"
        else:
            data = base64_string
        
        img_bytes = base64.b64decode(data)
        
        if len(img_bytes) > MAX_IMAGE_SIZE:
            return False, f"Imagem muito grande. Máximo: 5MB"
        
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


def salvar_imagem_scanner(base64_string, codigo):
    """Salva imagem em arquivo para o scanner"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        img_bytes = base64.b64decode(base64_string)
        
        if img_bytes[:2] == b'\xff\xd8':
            ext = 'jpg'
        elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            ext = 'png'
        elif img_bytes[:6] in (b'GIF87a', b'GIF89a'):
            ext = 'gif'
        else:
            ext = 'jpg'
        
        filename = f"{codigo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        filepath = os.path.join(app.config['SCANNER_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
        
        return filename
        
    except Exception as e:
        print(f"Erro ao salvar imagem: {e}")
        return None


def comparar_imagens(imagem1_base64, imagem2_path):
    """
    Compara duas imagens para verificar se são do mesmo produto.
    
    IMPORTANTE: Este é um sistema de demonstração que compara características básicas.
    Para produção real, use:
    - OpenCV com feature matching (ORB, SIFT)
    - Deep Learning (TensorFlow, YOLO)
    - QR Code / Código de Barras
    """
    try:
        if ',' in imagem1_base64:
            imagem1_base64 = imagem1_base64.split(',', 1)[1]
        img1_bytes = base64.b64decode(imagem1_base64)
        
        with open(os.path.join(app.config['SCANNER_FOLDER'], imagem2_path), 'rb') as f:
            img2_bytes = f.read()
        
        # Método 1: Hash exato (funciona se for a mesma imagem)
        hash1 = hashlib.md5(img1_bytes).hexdigest()
        hash2 = hashlib.md5(img2_bytes).hexdigest()
        
        if hash1 == hash2:
            print(f"✅ Match exato por hash: {hash1}")
            return True
        
        # Método 2: Comparação por tamanho similar (tolerância 15%)
        size1 = len(img1_bytes)
        size2 = len(img2_bytes)
        diferenca_tamanho = abs(size1 - size2) / max(size1, size2)
        
        print(f"📊 Tamanho img1: {size1} bytes, img2: {size2} bytes, diferença: {diferenca_tamanho:.2%}")
        
        if diferenca_tamanho < 0.15:  # 15% de tolerância
            # Compara assinatura (primeiros e últimos bytes)
            inicio_match = img1_bytes[:200] == img2_bytes[:200]
            fim_match = img1_bytes[-200:] == img2_bytes[-200:]
            
            if inicio_match and fim_match:
                print(f"✅ Match por assinatura (início e fim)")
                return True
            
            # Verifica se pelo menos um dos dois bate
            if inicio_match or fim_match:
                print(f"⚠️ Match parcial (início: {inicio_match}, fim: {fim_match})")
                # Aceita match parcial se tamanho for muito similar
                if diferenca_tamanho < 0.05:  # 5% de tolerância
                    print(f"✅ Match aceito por similaridade de tamanho")
                    return True
        
        print(f"❌ Sem match - diferença de tamanho: {diferenca_tamanho:.2%}")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao comparar imagens: {e}")
        return False


# -----------------------------------------------------------
# ROTAS DO SISTEMA
# -----------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = email
            return redirect(url_for('inicio'))
        else:
            flash("Email ou senha inválidos")
            return redirect(url_for('login'))

    return render_template('pagina2.html')


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email'].lower()
    password = request.form['password']

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        flash("Email já cadastrado")
        conn.close()
        return redirect(url_for('login'))

    conn.close()
    flash("Cadastro realizado com sucesso!")
    return redirect(url_for('login'))


@app.route('/inicio')
def inicio():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('inicio.html')


# -----------------------------------------------------------
# API DE ESCANEAMENTO POR CÂMERA
# -----------------------------------------------------------

@app.route('/api/scan', methods=['POST'])
def api_scan_produto():
    """
    Escaneia produto via CÂMERA usando QR Code
    Aceita: {"codigo": "123456"} OU {"imagem": "base64..."} (fallback)
    """
    if 'user' not in session:
        return jsonify({"status": "erro", "mensagem": "Não autenticado"}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "erro",
                "mensagem": "Dados não fornecidos"
            }), 400
        
        codigo_detectado = None
        
        # Método 1: QR Code já foi lido no frontend (JavaScript)
        if 'codigo' in data and data['codigo']:
            codigo_detectado = data['codigo'].strip()
            print(f"📱 Código QR detectado: {codigo_detectado}")
        
        # Método 2: Fallback - comparação de imagem (baixa taxa de sucesso)
        elif 'imagem' in data:
            imagem_capturada = data['imagem']
            
            # Valida imagem
            valido, msg = validar_base64_imagem(imagem_capturada)
            if not valido:
                return jsonify({
                    "status": "erro",
                    "mensagem": f"Imagem inválida: {msg}"
                }), 400
            
            # Busca produtos com imagem
            conn = get_db()
            produtos = conn.execute(
                "SELECT * FROM produtos WHERE imagem_path IS NOT NULL"
            ).fetchall()
            conn.close()
            
            # Compara imagens
            for produto in produtos:
                if comparar_imagens(imagem_capturada, produto['imagem_path']):
                    codigo_detectado = produto['codigo']
                    print(f"🖼️ Produto encontrado por comparação de imagem: {codigo_detectado}")
                    break
        
        # Se não detectou código de nenhuma forma
        if not codigo_detectado:
            return jsonify({
                "status": "nao_encontrado",
                "alerta": "⚠️ PRODUTO NÃO CADASTRADO!",
                "mensagem": "Nenhum QR Code detectado ou produto não encontrado. Cadastre-o agora.",
                "dica": "Aponte a câmera para o QR Code do produto"
            }), 200
        
        # Busca produto pelo código
        conn = get_db()
        produto = conn.execute(
            "SELECT * FROM produtos WHERE codigo = ?",
            (codigo_detectado,)
        ).fetchone()
        conn.close()
        
        if produto:
            # PRODUTO ENCONTRADO!
            return jsonify({
                "status": "encontrado",
                "mensagem": f"✅ Produto '{produto['nome']}' identificado via QR Code!",
                "produto": {
                    "id": produto['id'],
                    "codigo": produto['codigo'],
                    "nome": produto['nome'],
                    "localizacao": produto['localizacao'],
                    "quantidade": produto['quantidade'],
                    "preco": float(produto['preco']),
                    "categoria": produto['categoria'] or 'Geral',
                    "qrcode_url": f"/static/qrcodes/{produto['codigo']}.png"
                }
            }), 200
        
        # Código detectado mas produto não existe
        return jsonify({
            "status": "nao_encontrado",
            "alerta": "⚠️ PRODUTO NÃO CADASTRADO!",
            "mensagem": f"QR Code '{codigo_detectado}' detectado mas produto não existe no sistema.",
            "codigo_detectado": codigo_detectado
        }), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao escanear: {str(e)}"}), 500


@app.route('/api/cadastrar_scanner', methods=['POST'])
def api_cadastrar_scanner():
    """Cadastra novo produto via scanner com imagem obrigatória"""
    if 'user' not in session:
        return jsonify({"status": "erro", "mensagem": "Não autenticado"}), 401
    
    try:
        data = request.get_json()
        
        # Validação de campos obrigatórios (INCLUINDO IMAGEM)
        campos_obrigatorios = ['nome', 'localizacao', 'quantidade', 'imagem_base64']
        if not data or not all(k in data for k in campos_obrigatorios):
            return jsonify({
                "status": "erro",
                "mensagem": "Campos obrigatórios: nome, localizacao, quantidade e imagem_base64"
            }), 400
        
        nome = data['nome'].strip()
        localizacao = data['localizacao'].strip()
        quantidade = int(data['quantidade'])
        preco = float(data.get('preco', 0.0))
        categoria = data.get('categoria', 'Geral').strip()
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
        
        imagem_path = salvar_imagem_scanner(data['imagem_base64'], codigo)
        if not imagem_path:
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar imagem da câmera"}), 500
        
        # Gerar QR Code
        qr_filename = gerar_qrcode(codigo, nome)
        
        # Inserir no banco
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE produtos SET 
            codigo = ?, categoria = ?, imagem_path = ?, criado_em = ?, atualizado_em = ?
            WHERE id = (SELECT MAX(id) FROM produtos WHERE codigo IS NULL LIMIT 1)
        """, (codigo, categoria, imagem_path, datetime.now(), datetime.now()))
        
        if cursor.rowcount == 0:
            # Se não atualizou, insere novo
            cursor.execute("""
                INSERT INTO produtos (nome, quantidade, preco, localizacao, codigo, categoria, imagem_path, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, quantidade, preco, localizacao, codigo, categoria, imagem_path, datetime.now(), datetime.now()))
        
        produto_id = cursor.lastrowid if cursor.lastrowid > 0 else cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "sucesso",
            "mensagem": f"✅ Produto '{nome}' cadastrado com QR Code!",
            "produto_id": produto_id,
            "codigo": codigo,
            "qrcode_url": f"/static/qrcodes/{qr_filename}",
            "instrucao": "Baixe o QR Code, imprima e cole no produto. Depois aponte a câmera para o QR Code!"
        }), 201
        
    except ValueError as e:
        return jsonify({"status": "erro", "mensagem": "Quantidade e preço devem ser números válidos"}), 400
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao cadastrar: {str(e)}"}), 500


@app.route('/api/produtos_scanner', methods=['GET'])
def api_listar_produtos_scanner():
    """Lista todos produtos do scanner"""
    if 'user' not in session:
        return jsonify({"status": "erro", "mensagem": "Não autenticado"}), 401
    
    try:
        conn = get_db()
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE codigo IS NOT NULL ORDER BY nome"
        ).fetchall()
        conn.close()
        
        lista = [{
            "id": p['id'],
            "codigo": p['codigo'],
            "nome": p['nome'],
            "localizacao": p['localizacao'],
            "quantidade": p['quantidade'],
            "preco": float(p['preco']),
            "categoria": p['categoria'] or 'Geral',
            "imagem_url": f"/static/produtos_imagens/{p['imagem_path']}" if p['imagem_path'] else None
        } for p in produtos]
        
        return jsonify({
            "status": "sucesso",
            "total": len(lista),
            "produtos": lista
        }), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro: {str(e)}"}), 500


# -----------------------------------------------------------
# UPLOAD MANUAL
# -----------------------------------------------------------

@app.route('/camera', methods=['GET', 'POST'])
def camera():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash("Nenhuma imagem enviada")
            return redirect(url_for('camera'))

        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        nome = os.path.splitext(filename)[0].lower().strip()

        conn = get_db()
        produto = conn.execute(
            "SELECT * FROM produtos WHERE TRIM(LOWER(nome)) = ?",
            (nome,)
        ).fetchone()
        conn.close()

        if produto:
            return render_template('scan_result.html', produto=produto)

        flash(f'Produto "{nome}" não cadastrado.')
        return redirect(url_for('estoque'))

    return render_template('atual.html')


# API antiga comentada - agora usa /api/scan integrada acima


@app.route('/api/cadastrar_produto_escaneado', methods=['POST'])
def cadastrar_produto_escaneado():
    """
    API para cadastrar rapidamente um produto que foi escaneado mas não encontrado.
    """
    if 'user' not in session:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    data = request.get_json()
    
    campos_obrigatorios = ["nome", "quantidade", "preco", "coluna", "linha", "posicao"]
    if not all(campo in data for campo in campos_obrigatorios):
        return jsonify({"erro": "Campos obrigatórios faltando"}), 400

    try:
        nome = data["nome"].strip().lower()
        quantidade = int(data["quantidade"])
        preco = float(data["preco"])
        coluna = int(data["coluna"])
        linha = int(data["linha"])
        posicao = data["posicao"]
        
        imagem_base64 = data.get("imagem", "")
        if imagem_base64 and "," in imagem_base64:
            imagem_base64 = imagem_base64.split(",", 1)[1]

        localizacao = f"Coluna {coluna}, Linha {linha}, {posicao}"

        conn = get_db()
        cursor = conn.cursor()
        
        produto_existente = cursor.execute(
            "SELECT * FROM produtos WHERE TRIM(LOWER(nome)) = ?",
            (nome,)
        ).fetchone()
        
        if produto_existente:
            conn.close()
            return jsonify({"erro": "Produto já cadastrado com este nome"}), 400

        cursor.execute("""
            INSERT INTO produtos
            (nome, quantidade, preco, localizacao,
             coluna_armazenada, nivel_armazenado,
             imagem_base64, posicao_bloqueada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, quantidade, preco, localizacao,
              coluna, linha, imagem_base64, posicao))
        
        produto_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "sucesso": True,
            "mensagem": f"Produto '{nome}' cadastrado com sucesso!",
            "produto_id": produto_id
        }), 201

    except Exception as e:
        return jsonify({"erro": f"Erro ao cadastrar produto: {str(e)}"}), 500


@app.route('/api/produtos', methods=['GET'])
def listar_produtos():
    """
    API para listar todos os produtos cadastrados.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, quantidade, preco, localizacao,
                   coluna_armazenada, nivel_armazenado,
                   imagem_base64, posicao_bloqueada
            FROM produtos
            ORDER BY nome
        """)
        
        produtos = [{
            "id": row["id"],
            "nome": row["nome"],
            "quantidade": row["quantidade"],
            "preco": float(row["preco"]),
            "localizacao": row["localizacao"],
            "coluna": row["coluna_armazenada"],
            "nivel": row["nivel_armazenado"],
            "posicao": row["posicao_bloqueada"],
            "imagem": row["imagem_base64"]
        } for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "sucesso": True,
            "total": len(produtos),
            "produtos": produtos
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao listar produtos: {str(e)}"}), 500


@app.route('/api/produto/<int:produto_id>', methods=['GET'])
def obter_produto(produto_id):
    """
    API para obter informações de um produto específico por ID.
    """
    try:
        conn = get_db()
        produto = conn.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (produto_id,)
        ).fetchone()
        conn.close()

        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        return jsonify({
            "sucesso": True,
            "produto": {
                "id": produto["id"],
                "nome": produto["nome"],
                "quantidade": produto["quantidade"],
                "preco": float(produto["preco"]),
                "localizacao": produto["localizacao"],
                "coluna": produto["coluna_armazenada"],
                "nivel": produto["nivel_armazenado"],
                "posicao": produto["posicao_bloqueada"],
                "imagem": produto["imagem_base64"]
            }
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar produto: {str(e)}"}), 500


# -----------------------------------------------------------
# CONSULTAS DE ESTOQUE
# -----------------------------------------------------------

@app.route('/buscar_produto', methods=['GET', 'POST'])
def buscar_produto():
    if 'user' not in session:
        return redirect(url_for('login'))

    produto = None
    busca_realizada = False

    if request.method == 'POST':
        nome = request.form['busca'].strip().lower()

        conn = get_db()
        produto = conn.execute(
            "SELECT * FROM produtos WHERE TRIM(LOWER(nome)) = ?",
            (nome,)
        ).fetchone()
        conn.close()

        busca_realizada = True

    return render_template('buscar_produto.html',
                           produto=produto,
                           busca_realizada=busca_realizada)


@app.route('/estoque')
def estoque():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, quantidade, preco, localizacao,
               coluna_armazenada, nivel_armazenado,
               imagem_base64, posicao_bloqueada
        FROM produtos
    """)

    produtos = [{
        "id": row["id"],
        "nome": row["nome"],
        "quantidade": row["quantidade"],
        "preco": row["preco"],
        "localizacao": row["localizacao"],
        "coluna_armazenada": row["coluna_armazenada"],
        "nivel_armazenado": row["nivel_armazenado"],
        "imagem": row["imagem_base64"],
        "posicao_bloqueada": row["posicao_bloqueada"]
    } for row in cursor.fetchall()]

    conn.close()
    return render_template('estoque.html', produtos=produtos)


@app.route('/estoque_baixo')
def estoque_baixo():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, quantidade, preco, localizacao,
               coluna_armazenada, nivel_armazenado,
               imagem_base64, posicao_bloqueada
        FROM produtos
        WHERE quantidade <= 10
        ORDER BY quantidade ASC
    """)

    produtos = [{
        "id": row["id"],
        "nome": row["nome"],
        "quantidade": row["quantidade"],
        "preco": row["preco"],
        "localizacao": row["localizacao"],
        "coluna_armazenada": row["coluna_armazenada"],
        "nivel_armazenado": row["nivel_armazenado"],
        "imagem": row["imagem_base64"],
        "posicao_bloqueada": row["posicao_bloqueada"]
    } for row in cursor.fetchall()]

    conn.close()
    return render_template('estoque_baixo.html', produtos=produtos)


@app.route('/adicionar_produto', methods=['POST'])
def adicionar_produto():
    nome = request.form['nome'].strip().lower()
    quantidade = request.form['quantidade']
    preco = request.form['preco']
    coluna = request.form['coluna']
    linha = request.form['linha']
    posicao = request.form['posicao']

    imagem = request.files.get('imagem')
    imagem_base64 = ""

    if imagem:
        img = Image.open(imagem)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    localizacao = f"Coluna {coluna}, Linha {linha}, {posicao}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO produtos
        (nome, quantidade, preco, localizacao,
         coluna_armazenada, nivel_armazenado,
         imagem_base64, posicao_bloqueada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, quantidade, preco, localizacao,
          coluna, linha, imagem_base64, posicao))
    conn.commit()
    conn.close()

    return redirect(url_for('estoque'))


@app.route('/deletar_produto/<int:produto_id>', methods=['POST'])
def deletar_produto(produto_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()

    flash("Produto deletado.")
    return redirect(url_for('estoque'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Sessão encerrada.")
    return redirect(url_for('index'))


# -----------------------------------------------------------
# EXECUTAR
# -----------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
