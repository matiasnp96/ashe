# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import json
import os
from datetime import datetime
from exe import (
    recolectar_urls_hoteles,
    extraer_emails_de_pagina,
    PAISES_CIUDADES,
    procesar_pagina_hoteles,
    extraer_emails_de_contenido,
    es_email_valido
)
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from urllib.parse import quote
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import concurrent.futures
import emoji
import urllib3
import socket
from selenium.webdriver.common.action_chains import ActionChains

# Emojis directos usando UTF-8
EMOJI_SEARCH = "🔍"  # U+1F50D
EMOJI_STOP = "⏹️"    # U+23F9
EMOJI_EMAIL = "📧"   # U+1F4E7
EMOJI_FILE = "📁"    # U+1F4C1
EMOJI_CHECK = "✅"   # U+2705
EMOJI_ERROR = "❌"   # U+274C

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
socket.setdefaulttimeout(30)  # Timeout global de 30 segundos

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotel Email Scraper")
        self.root.configure(bg='#1E1E1E')
        
        # Cargar fuente personalizada
        self.custom_font = ('Segoe UI', 10)
        self.custom_font_bold = ('Segoe UI', 10, 'bold')
        
        # Configuración por defecto
        self.config = {
            'excluded_domains': [
                'bluepillow',
                'booking.com',
                'tripadvisor',
                'expedia',
                'hotels.com',
                'kayak',
                'trivago',
                'agoda',
                'hoteles.com',
                'despegar',
                'almundo',
                'airbnb'
            ]
        }
        
        # Variables
        self.scraping_active = False
        self.country_var = tk.StringVar()
        self.pages_var = tk.StringVar(value="3")
        self.hotels_per_page_var = tk.StringVar(value="5")
        self.current_driver = None
        self.valid_emails = set()
        self.invalid_emails = set()
        self.api_key = "299337569f8143a2854baf0c3c9d1142"
        
        # Configurar tema oscuro
        self.style = ttk.Style()
        self.configure_dark_theme()
        
        # Crear notebook y frames
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Crear frames
        self.scraper_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.validator_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        
        # Agregar pestañas
        self.notebook.add(self.scraper_frame, text='Extraer Emails')
        self.notebook.add(self.validator_frame, text='Validar Emails')
        
        # Configurar las interfaces
        self.setup_scraper_gui()
        self.setup_validator_gui()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Cargar íconos
        self.icons = {
            'check_small': tk.PhotoImage(file='check_small.png'),
            'error_small': tk.PhotoImage(file='error_small.png'),
            'check': tk.PhotoImage(file='check.png'),
            'error': tk.PhotoImage(file='error.png'),
            'warning': tk.PhotoImage(file='warning.png')
        }

    def load_custom_font(self):
        """Carga la fuente Montserrat"""
        # Asegúrate de que el archivo de fuente exista en el directorio del proyecto
        font_path = "Montserrat-Regular.ttf"
        if not os.path.exists(font_path):
            # Si no existe, usar una fuente del sistema similar
            self.custom_font = ('Segoe UI', 9)
            self.custom_font_bold = ('Segoe UI', 9, 'bold')
        else:
            # Cargar Montserrat
            self.root.tk.call('font', 'create', 'Montserrat', '-family', 'Montserrat', '-size', 9)
            self.custom_font = 'Montserrat'
            self.custom_font_bold = ('Montserrat', 9, 'bold')

    def configure_dark_theme(self):
        """Configura el tema oscuro mejorado"""
        # Colores
        bg_color = '#1E1E1E'
        fg_color = '#E0E0E0'
        select_color = '#007ACC'
        input_bg = '#2D2D2D'
        
        # Crear y configurar tema personalizado
        self.style.theme_create('DarkTheme', parent='alt', settings={
            'TNotebook': {
                'configure': {
                    'background': bg_color,
                    'borderwidth': 0,
                    'tabmargins': [0, 0, 0, 0]
                }
            },
            'TNotebook.Tab': {
                'configure': {
                    'padding': [10, 2],
                    'background': '#2D2D2D',
                    'foreground': '#FFFFFF',
                    'font': self.custom_font
                },
                'map': {
                    'background': [('selected', '#007ACC'),
                                 ('active', '#005999')],
                    'foreground': [('selected', '#FFFFFF'),
                                 ('active', '#FFFFFF')]
                }
            }
        })
        
        # Aplicar el tema
        self.style.theme_use('DarkTheme')
        
        # Estilo para widgets ttk
        self.style.configure('Dark.TFrame', 
                           background=bg_color)
        
        self.style.configure('Dark.TLabel',
                           background=bg_color,
                           foreground=fg_color,
                           font=self.custom_font)
        
        self.style.configure('Dark.TButton',
                           background=select_color,
                           foreground=fg_color,
                           font=self.custom_font,
                           padding=5,
                           relief='flat')
        
        self.style.map('Dark.TButton',
                      background=[('active', '#005999')],
                      relief=[('pressed', 'sunken')])
        
        # LabelFrame
        self.style.configure('Dark.TLabelframe',
                           background=bg_color,
                           foreground=fg_color)
        self.style.configure('Dark.TLabelframe.Label',
                           background=bg_color,
                           foreground=fg_color,
                           font=self.custom_font_bold)
        
        # Combobox (país)
        self.style.map('TCombobox',
                      fieldbackground=[('readonly', '#FFFFFF')],
                      selectbackground=[('readonly', '#007ACC')],
                      selectforeground=[('readonly', '#000000')],
                      background=[('readonly', '#FFFFFF')],
                      foreground=[('readonly', '#000000')])
        
        self.style.configure('TCombobox',
                           background='#FFFFFF',
                           foreground='#000000',
                           fieldbackground='#FFFFFF',
                           selectbackground='#007ACC',
                           selectforeground='#000000',
                           font=self.custom_font)
        
        # Entry
        self.style.configure('Dark.TEntry',
                           fieldbackground=input_bg,
                           foreground=fg_color,
                           insertcolor=fg_color,
                           font=self.custom_font)

    def setup_scraper_gui(self):
        """Configura la interfaz del scraper con estilo mejorado"""
        # Frame principal
        main_frame = ttk.Frame(self.scraper_frame, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame superior
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill='x', pady=5)
        
        # País
        country_frame = ttk.LabelFrame(
            top_frame,
            text="País",
            style='Dark.TLabelframe'
        )
        country_frame.pack(side='left', padx=5)
        
        self.country_combo = ttk.Combobox(
            country_frame,
            textvariable=self.country_var,
            values=sorted([
                'Argentina', 'Australia', 'Brasil', 'Canadá', 'Chile', 'Colombia',
                'España', 'Estados Unidos', 'Francia', 'Italia', 'México',
                'Nueva Zelanda', 'Perú', 'Portugal', 'Reino Unido', 'Uruguay'
            ]),
            state='readonly',
            width=20
        )
        self.country_combo.pack(padx=5, pady=5)
        self.country_combo.bind('<<ComboboxSelected>>', self.on_country_selected)
        
        # Ciudades
        cities_frame = ttk.LabelFrame(
            top_frame,
            text="Ciudades",
            style='Dark.TLabelframe'
        )
        cities_frame.pack(side='left', padx=5, fill='both')
        
        self.cities_listbox = tk.Listbox(
            cities_frame,
            selectmode='multiple',
            bg='#2D2D2D',
            fg='#E0E0E0',
            selectbackground='#007ACC',
            selectforeground='#FFFFFF',
            height=6,
            width=25,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#2D2D2D',
            highlightcolor='#007ACC'
        )
        self.cities_listbox.pack(padx=5, pady=5)
        
        # Configuraciones
        config_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        config_frame.pack(side='left', padx=5)
        
        # Páginas
        pages_frame = ttk.LabelFrame(
            config_frame,
            text="Páginas",
            style='Dark.TLabelframe'
        )
        pages_frame.pack(fill='x', pady=2)
        
        self.pages_entry = ttk.Entry(
            pages_frame,
            textvariable=self.pages_var,
            width=5
        )
        self.pages_entry.pack(padx=5, pady=2)
        
        # Hoteles por página
        hotels_frame = ttk.LabelFrame(
            config_frame,
            text="Hoteles por página",
            style='Dark.TLabelframe'
        )
        hotels_frame.pack(fill='x', pady=2)
        
        self.hotels_entry = ttk.Entry(
            hotels_frame,
            textvariable=self.hotels_per_page_var,
            width=5
        )
        self.hotels_entry.pack(padx=5, pady=2)
        
        # Frame para botones
        button_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        button_frame.pack(fill='x', pady=5)
        
        # Botones personalizados con tk.Button
        button_configs = [
            (f"{EMOJI_SEARCH} Extraer URLs", self.start_scraping_thread),
            (f"{EMOJI_STOP} Detener", self.stop_scraping),
            (f"{EMOJI_EMAIL} Extraer Emails", self.extract_emails)
        ]
        
        for text, command in button_configs:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                font=("Segoe UI Emoji", 10),  # Fuente específica para emojis
                bg='#007ACC',
                fg='#FFFFFF',
                activebackground='#005999',
                activeforeground='#FFFFFF',
                relief='flat',
                padx=10,
                pady=5,
                border=0
            )
            btn.pack(side='left', padx=2)
            
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#005999'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='#007ACC'))
        
        # Área de resultados
        results_frame = ttk.LabelFrame(
            main_frame,
            text="Progreso y Resultados",
            style='Dark.TLabelframe'
        )
        results_frame.pack(fill='both', expand=True, pady=5)
        
        self.scraper_text = tk.Text(
            results_frame,
            height=20,
            width=60,
            bg='#2D2D2D',
            fg='#E0E0E0',
            font=self.custom_font,
            insertbackground='#E0E0E0',
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#2D2D2D',
            highlightcolor='#007ACC'
        )
        self.scraper_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient='vertical',
            command=self.scraper_text.yview,
            style='Dark.Vertical.TScrollbar'
        )
        scrollbar.pack(side='right', fill='y')
        self.scraper_text.configure(yscrollcommand=scrollbar.set)

    def setup_validator_gui(self):
        """Configura la interfaz de la pestaña de validación"""
        main_frame = ttk.Frame(self.validator_frame, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame de controles
        control_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        control_frame.pack(fill='x', pady=5)
        
        # Botones personalizados con tk.Button
        button_configs = [
            ("📁 Seleccionar archivo", self.select_file),
            ("✅ Iniciar validación", self.start_validation),
            ("⏹️ Detener", self.stop_validation)
        ]
        
        for text, command in button_configs:
            btn = tk.Button(
                control_frame,
                text=text,
                command=command,
                font=('Segoe UI Emoji', 10),  # Fuente específica para emojis
                bg='#007ACC',
                fg='#FFFFFF',
                activebackground='#005999',
                activeforeground='#FFFFFF',
                relief='flat',
                padx=10,
                pady=5,
                border=0
            )
            btn.pack(side='left', padx=5)
            
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#005999'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='#007ACC'))
        
        # Área de resultados
        results_frame = ttk.LabelFrame(
            main_frame,
            text="Progreso y Resultados",
            style='Dark.TLabelframe'
        )
        results_frame.pack(fill='both', expand=True, pady=5)
        
        self.validator_text = tk.Text(
            results_frame,
            height=20,
            width=60,
            bg='#2D2D2D',
            fg='#E0E0E0',
            font=self.custom_font,
            insertbackground='#E0E0E0',
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#2D2D2D',
            highlightcolor='#007ACC'
        )
        self.validator_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient='vertical',
            command=self.validator_text.yview,
            style='Dark.Vertical.TScrollbar'
        )
        scrollbar.pack(side='right', fill='y')
        self.validator_text.configure(yscrollcommand=scrollbar.set)
        
        # Barra de progreso
        self.progress_var = tk.StringVar(value="0%")
        progress_label = ttk.Label(
            main_frame,
            textvariable=self.progress_var,
            style='Dark.TLabel'
        )
        progress_label.pack(pady=5)

    def get_cities_for_country(self, country):
        """Retorna la lista de ciudades para un país"""
        cities = {
            'Argentina': ['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata'],
            'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide'],
            'Brasil': ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza'],
            'Canadá': ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Ottawa'],
            'Chile': ['Santiago', 'Valparaíso', 'Viña del Mar', 'Concepción', 'La Serena'],
            'Colombia': ['Bogotá', 'Medellín', 'Cali', 'Cartagena', 'Barranquilla'],
            'España': ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Málaga'],
            'Estados Unidos': ['New York', 'Los Angeles', 'Chicago', 'Miami', 'Las Vegas'],
            'Francia': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice'],
            'Italia': ['Roma', 'Milán', 'Venecia', 'Florencia', 'Nápoles'],
            'México': ['Ciudad de México', 'Cancún', 'Guadalajara', 'Monterrey', 'Tijuana'],
            'Nueva Zelanda': ['Auckland', 'Wellington', 'Christchurch', 'Hamilton', 'Dunedin'],
            'Perú': ['Lima', 'Cusco', 'Arequipa', 'Trujillo', 'Chiclayo'],
            'Portugal': ['Lisboa', 'Oporto', 'Faro', 'Coimbra', 'Braga'],
            'Reino Unido': ['Londres', 'Manchester', 'Liverpool', 'Edinburgh', 'Glasgow'],
            'Uruguay': ['Montevideo', 'Punta del Este', 'Colonia', 'Maldonado', 'Salto']
        }
        return cities.get(country, [])

    def on_country_selected(self, event=None):
        """Maneja la selección de país"""
        country = self.country_var.get()
        if country:
            self.cities_listbox.delete(0, tk.END)
            cities = self.get_cities_for_country(country)
            for city in cities:
                self.cities_listbox.insert(tk.END, city)

    def start_scraping_thread(self):
        """Inicia el proceso de scraping en un hilo separado"""
        if not self.validate_scraping_inputs():
            return
            
        self.scraping_active = True
        self.update_buttons_state(True)
        threading.Thread(target=lambda: self.scraping_process(int(self.hotels_per_page_var.get())), daemon=True).start()

    def validate_scraping_inputs(self):
        """Valida las entradas antes de comenzar el scraping"""
        if not self.country_var.get():
            messagebox.showwarning("Advertencia", "Por favor seleccione un país")
            return False
            
        if not self.cities_listbox.curselection():
            messagebox.showwarning("Advertencia", "Por favor seleccione al menos una ciudad")
            return False
            
        try:
            pages = int(self.pages_var.get())
            hotels = int(self.hotels_per_page_var.get())
            if pages < 1 or hotels < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Advertencia", "Por favor ingrese números válidos")
            return False
            
        return True

    def scraping_process(self, hoteles_por_pagina):
        """Proceso principal de scraping"""
        try:
            selected_indices = self.cities_listbox.curselection()
            selected_cities = [self.cities_listbox.get(idx) for idx in selected_indices]
            country = self.country_var.get()
            
            for city in selected_cities:
                if not self.scraping_active:
                    break
                    
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'{country}_{city}_{timestamp}.txt'
                
                self.scraper_text.insert(tk.END, f"\nIniciando búsqueda en {city}, {country}...")
                self.scraper_text.see(tk.END)
                self.root.update_idletasks()
                
                driver = self.create_chrome_driver()
                self.current_driver = driver
                
                try:
                    search_url = self.build_search_url(city, country)
                    driver.get(search_url)
                    time.sleep(3)
                    
                    max_paginas = int(self.pages_var.get())
                    
                    urls_guardadas = self.recolectar_urls_hoteles(
                        ciudad=city,
                        pais=country,
                        paginas=max_paginas,
                        hoteles_por_pagina=hoteles_por_pagina
                    )
                    
                    # Guardar URLs en archivo
                    if urls_guardadas:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            for url in urls_guardadas:
                                f.write(f"{url}\n")
                        self.scraper_text.insert(tk.END, f"\nURLs guardadas en: {output_file}")
                        self.scraper_text.see(tk.END)
                        self.root.update_idletasks()
                    
                except Exception as e:
                    self.scraper_text.insert(tk.END, f"Error procesando {city}: {str(e)}\n")
                    self.scraper_text.see(tk.END)
                    self.root.update_idletasks()
                finally:
                    if driver:
                        driver.quit()
                        self.current_driver = None
            
            if self.scraping_active:
                self.scraper_text.insert(tk.END, "\nProceso completado exitosamente\n")
                self.scraper_text.see(tk.END)
                self.root.update_idletasks()
            
        except Exception as e:
            self.scraper_text.insert(tk.END, f"Error general en el proceso: {str(e)}\n")
            self.scraper_text.see(tk.END)
            self.root.update_idletasks()
        finally:
            self.scraping_active = False
            self.update_buttons_state(False)

    def extract_emails(self):
        """Inicia el proceso de extracción de emails desde múltiples archivos"""
        if self.scraper_text:
            self.scraper_text.delete(1.0, tk.END)
        
        archivos_urls = filedialog.askopenfilenames(
            title="Seleccionar archivos de URLs",
            filetypes=[("Archivos de texto", "*.txt")],
            initialdir="."
        )
        
        if not archivos_urls:
            return
        
        prefijo_comun = os.path.basename(archivos_urls[0]).split('_')[0] if archivos_urls else ''
        archivo_emails = filedialog.asksaveasfilename(
            title="Guardar todos los emails como",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt")],
            initialdir=".",
            initialfile=f'{prefijo_comun}_emails_combinados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
        
        if not archivo_emails:
            return

        def clean_email(email):
            """Limpia el email de caracteres invisibles y espacios"""
            # Eliminar caracteres invisibles y espacios
            cleaned = ''.join(char for char in email if char.isprintable() and not char.isspace())
            return cleaned.lower().strip()

        def process_url_batch(urls_batch, session, emails_lock):
            # Dominios a excluir
            DOMINIOS_EXCLUIDOS = [
                'bluepillow',
                'booking.com',
                'tripadvisor',
                'expedia',
                'hotels.com',
                'kayak',
                'trivago',
                'agoda',
                'hoteles.com',
                'despegar',
                'almundo',
                'airbnb'
            ]
            
            def is_valid_domain(url):
                """Verifica si el dominio es válido para procesar"""
                return not any(dominio in url.lower() for dominio in DOMINIOS_EXCLUIDOS)
            
            emails_encontrados = set()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            def get_with_retry(url, max_retries=3):
                """Función auxiliar para hacer requests con reintentos y múltiples métodos"""
                for intento in range(max_retries):
                    try:
                        # Primer intento con requests
                        response = session.get(
                            url, 
                            headers=headers, 
                            timeout=15,
                            verify=False,
                            allow_redirects=True
                        )
                        response.raise_for_status()
                        return response
                    except Exception as e:
                        if intento == max_retries - 1:
                            # Último intento: usar urllib3 directamente
                            try:
                                http = urllib3.PoolManager(
                                    retries=urllib3.Retry(3),
                                    timeout=urllib3.Timeout(connect=10, read=20)
                                )
                                response = http.request('GET', url, headers=headers)
                                if response.status == 200:
                                    return type('Response', (), {
                                        'text': response.data.decode('utf-8', errors='ignore'),
                                        'status_code': response.status
                                    })
                            except Exception as e2:
                                self.scraper_text.insert(tk.END, f"   ⚠️ Reintento fallido para {url}: {str(e2)}\n")
                                return None
                        time.sleep(2)  # Esperar más tiempo entre intentos
                return None

            # Crear o leer el archivo de emails existentes
            with emails_lock:
                if not os.path.exists(archivo_emails):
                    open(archivo_emails, 'w', encoding='utf-8').close()
                with open(archivo_emails, 'r', encoding='utf-8') as f:
                    existing_emails = {clean_email(line.strip()) for line in f}

            for url in urls_batch:
                if not self.scraping_active:
                    break
                
                # Verificar si el dominio es válido
                if not is_valid_domain(url):
                    self.scraper_text.insert(tk.END, f"   ⏭️ Saltando dominio excluido: {url}\n")
                    self.scraper_text.see(tk.END)
                    self.root.update_idletasks()
                    continue
                
                try:
                    # Obtener página principal con reintentos
                    self.scraper_text.insert(tk.END, f"   🔍 Intentando acceder a: {url}\n")
                    self.scraper_text.see(tk.END)
                    self.root.update_idletasks()
                    
                    response = get_with_retry(url)
                    if not response:
                        self.scraper_text.insert(tk.END, f"   ⚠️ No se pudo acceder a: {url}\n")
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Buscar emails en el HTML
                    emails = set()
                    
                    # Método 1: Buscar patrones de email directamente en el HTML
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    emails.update(re.findall(email_pattern, response.text))
                    
                    # Método 2: Buscar en atributos href="mailto:"
                    for mailto in soup.select('a[href^="mailto:"]'):
                        email = mailto['href'].replace('mailto:', '').split('?')[0]
                        emails.add(email)
                    
                    # Método 3: Buscar en la página de contacto con reintentos
                    contact_links = soup.find_all('a', href=re.compile(r'contact|contacto|Contact|Contacto'))
                    for link in contact_links:
                        try:
                            contact_url = urljoin(url, link['href'])
                            contact_response = get_with_retry(contact_url)
                            if contact_response:
                                emails.update(re.findall(email_pattern, contact_response.text))
                        except:
                            continue
                    
                    # Procesar emails encontrados
                    if emails:
                        # Limpiar y validar emails
                        emails_validos = {clean_email(email) for email in emails if es_email_valido(email)}
                        # Filtrar emails que ya existen
                        nuevos_emails = emails_validos - existing_emails
                        
                        if nuevos_emails:
                            with emails_lock:
                                with open(archivo_emails, 'a', encoding='utf-8') as f:
                                    for email in nuevos_emails:
                                        emails_encontrados.add(email)
                                        existing_emails.add(email)
                                        f.write(f"{email}\n")
                                        self.scraper_text.insert(tk.END, f"   ✓ Nuevo email encontrado en {url}: {email}\n")
                                        self.scraper_text.see(tk.END)
                                        self.root.update_idletasks()
                        else:
                            self.scraper_text.insert(tk.END, f"   ℹ️ No se encontraron nuevos emails en: {url}\n")
                    else:
                        self.scraper_text.insert(tk.END, f"   ✗ No se encontraron emails en: {url}\n")
                            
                except Exception as e:
                    self.scraper_text.insert(tk.END, f"   ✗ Error procesando {url}: {str(e)}\n")
                    self.scraper_text.see(tk.END)
                    self.root.update_idletasks()
                    continue
                    
            return emails_encontrados

        def process_emails():
            self.scraper_text.insert(tk.END, "\nIniciando extracción de emails...\n")
            self.scraper_text.see(tk.END)
            self.root.update_idletasks()
            
            todas_urls = []
            for archivo in archivos_urls:
                with open(archivo, 'r', encoding='utf-8') as f:
                    todas_urls.extend([url.strip() for url in f if url.strip()])
            
            total_urls = len(todas_urls)
            urls_procesadas = 0
            emails_unicos = set()
            
            # Crear una sesión de requests para reutilizar conexiones
            with requests.Session() as session:
                # Procesar URLs en paralelo
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    emails_lock = threading.Lock()
                    
                    # Dividir URLs en batches
                    batch_size = 1
                    for i in range(0, len(todas_urls), batch_size):
                        batch = todas_urls[i:i + batch_size]
                        future = executor.submit(process_url_batch, batch, session, emails_lock)
                        futures.append(future)
                    
                    # Procesar resultados
                    for future in concurrent.futures.as_completed(futures):
                        urls_procesadas += batch_size
                        emails_unicos.update(future.result())
                        self.scraper_text.insert(tk.END, f"Progreso: {urls_procesadas}/{total_urls} URLs procesadas\n")
                        self.scraper_text.see(tk.END)
                        self.root.update_idletasks()
            
            self.scraper_text.insert(tk.END, f"\n✅ Proceso completado\n")
            self.scraper_text.see(tk.END)
            self.root.update_idletasks()
            self.scraper_text.insert(tk.END, f"   • URLs procesadas: {urls_procesadas}/{total_urls}\n")
            self.scraper_text.see(tk.END)
            self.scraper_text.insert(tk.END, f"   • Emails únicos: {len(emails_unicos)}\n")
        
        self.scraping_active = True
        threading.Thread(target=process_emails, daemon=True).start()

    def create_chrome_driver(self):
        """Crea una nueva instancia de Chrome con configuraciones mejoradas"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-features=NetworkService')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Agregar manejo de errores específicos
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('detach', False)
            
            # Intentar cerrar todas las instancias existentes de Chrome
            try:
                os.system('taskkill /f /im chrome.exe')
                time.sleep(2)
            except:
                pass
            
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configurar timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            return driver
        except Exception as e:
            self.scraper_text.insert(tk.END, f"Error creando el driver: {str(e)}\n")
            self.scraper_text.see(tk.END)
            self.root.update_idletasks()
            raise

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if messagebox.askokcancel("Salir", "¿Desea cerrar la aplicación?"):
            self.cleanup_chrome()
            self.root.destroy()

    def cleanup_chrome(self):
        """Limpia las instancias de Chrome"""
        if self.current_driver:
            try:
                self.current_driver.quit()
            except:
                pass
            self.current_driver = None

    def update_buttons_state(self, scraping_active):
        """Actualiza el estado de los botones según el estado del scraping"""
        state = 'disabled' if scraping_active else 'normal'
        for widget in self.scraper_frame.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Entry, tk.Listbox)):
                try:
                    widget.configure(state=state)
                except:
                    pass

    def build_search_url(self, city, country):
        """Construye la URL de búsqueda para Google Travel"""
        base_url = "https://www.google.com/travel/hotels"
        # Formatear ciudad y país para la URL
        city_query = f"{city}, {country}".replace(" ", "%20")
        return f"{base_url}?q=hotels%20in%20{city_query}"

    def verify_email(self, email: str) -> tuple:
        """Verifica un email usando Abstract API"""
        url = f"https://emailvalidation.abstractapi.com/v1/?api_key={self.api_key}&email={email}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            is_deliverable = data.get("deliverability") == "DELIVERABLE"
            
            if is_deliverable:
                message = "Email puede recibir correos"
            else:
                message = f"Email no puede recibir correos (Status: {data.get('deliverability', 'UNKNOWN')})"
            
            return is_deliverable, message
            
        except Exception as e:
            return False, f"Error: {str(e)}"

    def process_emails(self, emails):
        """Procesa la lista de emails"""
        total = len(emails)
        processed = 0

        for email in emails:
            if not self.scraping_active:
                break

            is_valid, message = self.verify_email(email.strip())
            
            if is_valid:
                self.valid_emails.add(email)
                self.log_validator_message(f"{EMOJI_CHECK} {email}: {message}")
            else:
                self.invalid_emails.add(email)
                self.log_validator_message(f"{EMOJI_ERROR} {email}: {message}")

            processed += 1
            progress = (processed / total) * 100
            self.progress_var.set(f"{progress:.1f}%")
            self.root.update_idletasks()
            
            time.sleep(1)

        self.save_validation_results()

    def select_file(self):
        """Selecciona el archivo de emails a validar"""
        self.filename = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt")]
        )
        if self.filename:
            self.log_validator_message(f"{EMOJI_FILE} Archivo seleccionado: {self.filename}")

    def start_validation(self):
        """Inicia el proceso de validación"""
        if not hasattr(self, 'filename'):
            messagebox.showerror("Error", "Por favor seleccione un archivo primero")
            return

        try:
            with open(self.filename, 'r') as f:
                emails = [line.strip() for line in f if line.strip()]

            self.scraping_active = True
            self.valid_emails = set()
            self.invalid_emails = set()
            self.progress_var.set("0%")
            self.validator_text.delete(1.0, tk.END)

            threading.Thread(target=self.process_emails, args=(emails,), daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo: {str(e)}")

    def stop_validation(self):
        """Detiene el proceso de validación"""
        self.scraping_active = False

    def log_validator_message(self, message):
        """Registra un mensaje en la interfaz del validador"""
        self.validator_text.insert(tk.END, message + "\n")
        self.validator_text.see(tk.END)
        self.root.update_idletasks()

    def save_validation_results(self):
        """Guarda los resultados de la validación"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.valid_emails:
            filename = f'emails_validos_{timestamp}.txt'
            with open(filename, 'w') as f:
                for email in self.valid_emails:
                    f.write(email + '\n')
            self.log_validator_message(f"{EMOJI_CHECK} Emails válidos guardados en: {filename}")

        if self.invalid_emails:
            filename = f'emails_invalidos_{timestamp}.txt'
            with open(filename, 'w') as f:
                for email in self.invalid_emails:
                    f.write(email + '\n')
            self.log_validator_message(f"{EMOJI_ERROR} Emails inválidos guardados en: {filename}")

    def stop_scraping(self):
        """Detiene el proceso de scraping"""
        self.scraping_active = False
        if self.current_driver:
            try:
                self.current_driver.quit()
            except:
                pass
            self.current_driver = None
        self.update_buttons_state(False)

    def recolectar_urls_hoteles(self, ciudad, pais, paginas=3, hoteles_por_pagina=5):
        """Recolecta URLs de hoteles usando Selenium"""
        urls_hoteles = set()
        dominios_excluidos = self.config['excluded_domains'] + ['maps.google']
        
        def decodificar_url(url):
            """Decodifica una URL que contiene caracteres Unicode escapados"""
            return url.encode('utf-8').decode('unicode-escape').replace('\\/', '/')
        
        try:
            driver = self.current_driver
            pagina = 1
            
            def esperar_carga_pagina():
                try:
                    # Esperar a que el botón "Siguiente" esté visible
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Siguiente')]"))
                    )
                    return True
                except Exception as e:
                    print(f"   ❌ Error al esperar la carga de la página: {e}")
                    return False

            for pagina in range(1, paginas + 1):
                print(f"\n📄 Procesando página {pagina} de {paginas}...")
                
                # Esperar a que la página cargue
                if not esperar_carga_pagina():
                    print("   ⚠️ No se pudo cargar la página correctamente")
                    break
                
                # Obtener el HTML actual
                html_actual = driver.page_source
                urls_pagina_actual = set()
                
                # Extraer URLs
                patron = r'\[null,null,"(https?://[^"]+?)"\]'
                urls_encontradas = re.findall(patron, html_actual)
                
                print(f"\n   🔍 URLs encontradas en página {pagina}:")
                for url in urls_encontradas:
                    if not any(dominio in url.lower() for dominio in dominios_excluidos):
                        url_decodificada = decodificar_url(url)
                        print(f"      → {url_decodificada}")
                        urls_pagina_actual.add(url_decodificada)
                        urls_hoteles.add(url_decodificada)
                
                print(f"\n   ✨ URLs únicas en esta página: {len(urls_pagina_actual)}")
                
                # Si no es la última página, cambiar a la siguiente
                if pagina < paginas:
                    try:
                        # Encontrar el botón y asegurarse de que sea clickeable
                        boton_siguiente = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Siguiente')]"))
                        )
                        
                        # Scroll hasta el botón para asegurarnos de que sea visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", boton_siguiente)
                        time.sleep(1)  # Pequeña pausa después del scroll
                        
                        # Intentar click con JavaScript si el click normal falla
                        try:
                            boton_siguiente.click()
                        except:
                            driver.execute_script("arguments[0].click();", boton_siguiente)
                            
                        print("\n   ⏳ Esperando carga de siguiente página...")
                        
                        # Espera inicial
                        time.sleep(3)
                        
                        # Forzar actualización del DOM con scroll
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)  # Esperar después del scroll
                        
                        # Scroll hacia arriba para asegurar que vemos todo el contenido
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"   ❌ Error al cambiar de página: {str(e)}")
                        break
        
        except Exception as e:
            print(f"   ❌ Error recolectando URLs: {str(e)}")
        
        # Guardar las URLs encontradas
        if urls_hoteles:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"urls_hoteles_{ciudad}_{timestamp}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for url in urls_hoteles:
                        f.write(url + '\n')
                print(f"\n📁 URLs guardadas en: {filename}")
            except Exception as e:
                print(f"❌ Error al guardar las URLs: {str(e)}")
        
        print(f"\n✨ Total de URLs únicas encontradas: {len(urls_hoteles)}")
        return list(urls_hoteles)

def main():
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
