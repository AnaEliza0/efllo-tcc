#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste para Scanner de Produtos
Testa a função de comparação de imagens
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import base64
import hashlib
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random

# Configurações
PASTA_TESTE = 'static/produtos_imagens'
os.makedirs(PASTA_TESTE, exist_ok=True)

def criar_imagem_teste(nome, cor=(255, 0, 0), texto="PRODUTO"):
    """Cria uma imagem de teste"""
    img = Image.new('RGB', (400, 300), color=cor)
    draw = ImageDraw.Draw(img)
    
    # Adiciona texto
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 130), texto, fill=(255, 255, 255), font=font)
    
    # Salva
    caminho = os.path.join(PASTA_TESTE, nome)
    img.save(caminho, 'JPEG', quality=80)
    print(f"✅ Imagem criada: {caminho}")
    return caminho

def imagem_para_base64(caminho):
    """Converte imagem para base64"""
    with open(caminho, 'rb') as f:
        img_bytes = f.read()
    base64_string = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_string}"

def comparar_imagens_teste(imagem1_base64, imagem2_path):
    """
    Versão de teste da função comparar_imagens
    (Mesma lógica do main.py)
    """
    try:
        if ',' in imagem1_base64:
            imagem1_base64 = imagem1_base64.split(',', 1)[1]
        img1_bytes = base64.b64decode(imagem1_base64)
        
        with open(imagem2_path, 'rb') as f:
            img2_bytes = f.read()
        
        # Método 1: Hash exato
        hash1 = hashlib.md5(img1_bytes).hexdigest()
        hash2 = hashlib.md5(img2_bytes).hexdigest()
        
        print(f"  Hash 1: {hash1[:16]}...")
        print(f"  Hash 2: {hash2[:16]}...")
        
        if hash1 == hash2:
            print(f"  ✅ Match exato por hash!")
            return True
        
        # Método 2: Comparação por tamanho
        size1 = len(img1_bytes)
        size2 = len(img2_bytes)
        diferenca_tamanho = abs(size1 - size2) / max(size1, size2)
        
        print(f"  📊 Tamanho img1: {size1:,} bytes, img2: {size2:,} bytes")
        print(f"  📊 Diferença: {diferenca_tamanho:.2%}")
        
        if diferenca_tamanho < 0.15:
            inicio_match = img1_bytes[:200] == img2_bytes[:200]
            fim_match = img1_bytes[-200:] == img2_bytes[-200:]
            
            print(f"  🔍 Início match: {inicio_match}")
            print(f"  🔍 Fim match: {fim_match}")
            
            if inicio_match and fim_match:
                print(f"  ✅ Match por assinatura!")
                return True
            
            if inicio_match or fim_match:
                if diferenca_tamanho < 0.05:
                    print(f"  ✅ Match aceito por similaridade!")
                    return True
                else:
                    print(f"  ⚠️ Match parcial, mas diferença muito grande")
        else:
            print(f"  ❌ Diferença de tamanho muito grande")
        
        return False
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def executar_testes():
    """Executa bateria de testes"""
    print("\n" + "="*70)
    print("TESTE DO SCANNER DE PRODUTOS")
    print("="*70 + "\n")
    
    # TESTE 1: Mesma imagem (deve dar match)
    print("📌 TESTE 1: Mesma Imagem Exata")
    print("-" * 70)
    img1 = criar_imagem_teste("teste1_mouse.jpg", cor=(255, 0, 0), texto="MOUSE")
    base64_1 = imagem_para_base64(img1)
    resultado = comparar_imagens_teste(base64_1, img1)
    print(f"RESULTADO: {'✅ PASSOU' if resultado else '❌ FALHOU'}")
    print()
    
    # TESTE 2: Imagens idênticas mas arquivos diferentes
    print("📌 TESTE 2: Imagens Idênticas (Arquivos Duplicados)")
    print("-" * 70)
    img2a = criar_imagem_teste("teste2a_teclado.jpg", cor=(0, 255, 0), texto="TECLADO")
    img2b = criar_imagem_teste("teste2b_teclado.jpg", cor=(0, 255, 0), texto="TECLADO")
    base64_2a = imagem_para_base64(img2a)
    resultado = comparar_imagens_teste(base64_2a, img2b)
    print(f"RESULTADO: {'✅ PASSOU' if resultado else '❌ FALHOU'}")
    print()
    
    # TESTE 3: Imagens diferentes (não deve dar match)
    print("📌 TESTE 3: Imagens Totalmente Diferentes")
    print("-" * 70)
    img3a = criar_imagem_teste("teste3a_azul.jpg", cor=(0, 0, 255), texto="PRODUTO A")
    img3b = criar_imagem_teste("teste3b_amarelo.jpg", cor=(255, 255, 0), texto="PRODUTO B")
    base64_3a = imagem_para_base64(img3a)
    resultado = comparar_imagens_teste(base64_3a, img3b)
    print(f"RESULTADO: {'❌ PASSOU (não deveria)' if resultado else '✅ PASSOU (rejeitou corretamente)'}")
    print()
    
    # TESTE 4: Imagem com qualidade diferente
    print("📌 TESTE 4: Mesma Imagem com Qualidade Diferente")
    print("-" * 70)
    # Cria imagem original
    img_original = Image.new('RGB', (400, 300), color=(128, 0, 128))
    draw = ImageDraw.Draw(img_original)
    draw.text((100, 130), "ORIGINAL", fill=(255, 255, 255))
    
    # Salva com qualidade alta
    caminho_alta = os.path.join(PASTA_TESTE, "teste4_alta.jpg")
    img_original.save(caminho_alta, 'JPEG', quality=95)
    
    # Salva com qualidade baixa
    caminho_baixa = os.path.join(PASTA_TESTE, "teste4_baixa.jpg")
    img_original.save(caminho_baixa, 'JPEG', quality=50)
    
    print(f"✅ Imagem alta qualidade: {caminho_alta}")
    print(f"✅ Imagem baixa qualidade: {caminho_baixa}")
    
    base64_alta = imagem_para_base64(caminho_alta)
    resultado = comparar_imagens_teste(base64_alta, caminho_baixa)
    print(f"RESULTADO: {'✅ PASSOU' if resultado else '⚠️ FALHOU (esperado com qualidades diferentes)'}")
    print()
    
    # TESTE 5: Simula frame de câmera (levemente diferente)
    print("📌 TESTE 5: Simula Frame de Câmera (Ruído Adicionado)")
    print("-" * 70)
    # Cria imagem base
    img_base = Image.new('RGB', (400, 300), color=(200, 100, 50))
    draw = ImageDraw.Draw(img_base)
    draw.text((100, 130), "CAMERA", fill=(255, 255, 255))
    caminho_base = os.path.join(PASTA_TESTE, "teste5_base.jpg")
    img_base.save(caminho_base, 'JPEG', quality=80)
    
    # Adiciona ruído (simula diferença de frame)
    pixels = img_base.load()
    for i in range(50):  # Adiciona 50 pixels aleatórios
        x = random.randint(0, 399)
        y = random.randint(0, 299)
        pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    caminho_ruido = os.path.join(PASTA_TESTE, "teste5_ruido.jpg")
    img_base.save(caminho_ruido, 'JPEG', quality=80)
    
    print(f"✅ Imagem base: {caminho_base}")
    print(f"✅ Imagem com ruído: {caminho_ruido}")
    
    base64_base = imagem_para_base64(caminho_base)
    resultado = comparar_imagens_teste(base64_base, caminho_ruido)
    print(f"RESULTADO: {'✅ PASSOU' if resultado else '❌ FALHOU'}")
    print()
    
    # RESUMO
    print("="*70)
    print("📊 RESUMO DOS TESTES")
    print("="*70)
    print("""
    ✅ TESTE 1: Deve reconhecer mesma imagem (hash exato)
    ✅ TESTE 2: Deve reconhecer imagens idênticas
    ✅ TESTE 3: Deve rejeitar imagens diferentes
    ⚠️ TESTE 4: Pode falhar com qualidades diferentes
    ⚠️ TESTE 5: Pode falhar com ruído (frames de câmera)
    
    CONCLUSÃO:
    - Sistema funciona bem para imagens IDÊNTICAS
    - Sistema pode falhar com frames de câmera em tempo real
    - Recomendação: Use QR Code para câmera em tempo real
    """)
    
    print("\n💡 Dica: Verifique as imagens criadas em:")
    print(f"   {os.path.abspath(PASTA_TESTE)}")
    print()

if __name__ == "__main__":
    executar_testes()
