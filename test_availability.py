# -*- coding: utf-8 -*-
"""
Teste de verificacao de disponibilidade com produtos disponiveis.
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
}


@dataclass
class Product:
    name: str
    url: str
    store: str


def check_panini_availability(url: str) -> tuple[bool, Optional[str]]:
    """
    Verifica disponibilidade na loja Panini.
    Produtos indisponiveis contem 'productalert' na pagina.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Debug: mostrar se encontrou productalert
        found_alert = 'productalert' in html_text
        print(f"      [DEBUG] 'productalert' encontrado: {found_alert}")
        
        if found_alert:
            return False, None
        
        price_element = soup.find('span', {'class': 'price'})
        price = price_element.get_text(strip=True) if price_element else None
        
        return True, price
        
    except requests.RequestException as e:
        print(f"Erro ao acessar Panini: {e}")
        return False, None


def check_amazon_availability(url: str) -> tuple[bool, Optional[str]]:
    """Verifica disponibilidade na Amazon."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        unavailable_indicators = [
            'Atualmente indisponivel',
            'Currently unavailable',
            'Temporariamente esgotado',
        ]
        
        page_text = soup.get_text()
        
        for indicator in unavailable_indicators:
            if indicator.lower() in page_text.lower():
                availability_div = soup.find('div', {'id': 'availability'})
                if availability_div and indicator.lower() in availability_div.get_text().lower():
                    return False, None
        
        add_to_cart = soup.find('input', {'id': 'add-to-cart-button'})
        buy_now = soup.find('input', {'id': 'buy-now-button'})
        
        if add_to_cart or buy_now:
            price_element = soup.find('span', {'class': 'a-price-whole'})
            if price_element:
                price_fraction = soup.find('span', {'class': 'a-price-fraction'})
                price = f"R$ {price_element.get_text(strip=True)}"
                if price_fraction:
                    price += price_fraction.get_text(strip=True)
                return True, price
            return True, None
        
        return False, None
        
    except requests.RequestException as e:
        print(f"Erro ao acessar Amazon: {e}")
        return False, None


def check_availability(product: Product) -> tuple[bool, Optional[str]]:
    if product.store == "Panini":
        return check_panini_availability(product.url)
    elif product.store == "Amazon":
        return check_amazon_availability(product.url)
    else:
        return False, None


def main():
    print("=" * 70)
    print("TESTE DE VERIFICACAO DE DISPONIBILIDADE")
    print("=" * 70)
    print()
    
    test_products = [
        Product(
            name="Berserk Vol. 11 (TESTE - Disponivel)",
            url="https://panini.com.br/berserk-edicao-de-luxo-vol-11-amaxs011r4",
            store="Panini"
        ),
        Product(
            name="Amazon ISBN 8542617096 (TESTE)",
            url="https://www.amazon.com.br/gp/product/8542617096",
            store="Amazon"
        ),
        Product(
            name="Berserk Vol. 40 (Original - Indisponivel)",
            url="https://panini.com.br/berserk-edicao-de-luxo-vol-40-amaxs040r",
            store="Panini"
        ),
    ]
    
    print("Verificando produtos...\n")
    
    results = []
    
    for product in test_products:
        print(f"[{product.store}] {product.name}")
        print(f"   URL: {product.url}")
        
        is_available, price = check_availability(product)
        
        if is_available:
            price_info = f" - {price}" if price else ""
            print(f"   >>> DISPONIVEL!{price_info}")
            results.append((True, product.name, price or "-"))
        else:
            print(f"   >>> Indisponivel")
            results.append((False, product.name, "-"))
        
        print()
    
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    available_count = sum(1 for r in results if r[0])
    unavailable_count = sum(1 for r in results if not r[0])
    
    print(f"Disponiveis: {available_count}")
    print(f"Indisponiveis: {unavailable_count}")
    print()
    
    # Resultado esperado
    print("RESULTADO ESPERADO:")
    print("  - Vol. 11 Panini: DISPONIVEL")
    print("  - Amazon 8542617096: DISPONIVEL (se em estoque)")
    print("  - Vol. 40 Panini: INDISPONIVEL")


if __name__ == "__main__":
    main()
