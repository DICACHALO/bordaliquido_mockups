#!/usr/bin/env python3
"""
Web Scraper para extraer imágenes y PDFs
Uso: python scraper_images_pdfs.py <URL> [directorio_salida]
"""

import os
import sys
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
import time

class WebScraper:
    def __init__(self, url, output_dir=None):
        self.url = url
        self.domain = urlparse(url).netloc
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Crear directorios
        self.img_dir = self.output_dir / "imagenes"
        self.pdf_dir = self.output_dir / "pdfs"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        print(f"🔍 Scrapeando: {url}")
        print(f"📁 Guardando en: {self.output_dir}")

    def fetch_page(self):
        """Obtiene el HTML de la página"""
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al descargar la página: {e}")
            return None

    def extract_urls(self, html):
        """Extrae URLs de imágenes y PDFs del HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        images = set()
        pdfs = set()

        # Imágenes en <img>
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.add(urljoin(self.url, src))

        # Imágenes en CSS backgrounds
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            if 'url(' in style:
                import re
                urls = re.findall(r'url\([\'"]?([^\)\'\"]+)[\'"]?\)', style)
                for url in urls:
                    images.add(urljoin(self.url, url))

        # PDFs en <a href>
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.lower().endswith('.pdf'):
                pdfs.add(urljoin(self.url, href))

        return images, pdfs

    def download_file(self, url, directory, file_type):
        """Descarga un archivo"""
        try:
            filename = urlparse(url).path.split('/')[-1]
            if not filename:
                filename = f"{file_type}_{int(time.time())}"

            # Validar extensión
            if file_type == "imagen" and not any(filename.lower().endswith(ext)
                                                   for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                filename = filename.split('?')[0]  # Eliminar parámetros

            filepath = directory / filename

            # No descargar si ya existe
            if filepath.exists():
                print(f"⏭️  Ya existe: {filename}")
                return True

            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ Descargado: {filename} ({size_mb:.2f} MB)")
            return True

        except Exception as e:
            print(f"⚠️  Error descargando {url}: {e}")
            return False

    def run(self):
        """Ejecuta el scraper"""
        html = self.fetch_page()
        if not html:
            return False

        images, pdfs = self.extract_urls(html)

        print(f"\n📊 Encontrado: {len(images)} imágenes, {len(pdfs)} PDFs")

        # Descargar imágenes
        if images:
            print(f"\n🖼️  Descargando imágenes...")
            for i, url in enumerate(images, 1):
                print(f"[{i}/{len(images)}]", end=" ")
                self.download_file(url, self.img_dir, "imagen")

        # Descargar PDFs
        if pdfs:
            print(f"\n📄 Descargando PDFs...")
            for i, url in enumerate(pdfs, 1):
                print(f"[{i}/{len(pdfs)}]", end=" ")
                self.download_file(url, self.pdf_dir, "pdf")

        print(f"\n✨ Completado!")
        print(f"📁 Imágenes en: {self.img_dir}")
        print(f"📁 PDFs en: {self.pdf_dir}")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scraper_images_pdfs.py <URL> [directorio_salida]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    scraper = WebScraper(url, output_dir)
    success = scraper.run()
    sys.exit(0 if success else 1)
