from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
import os
import csv
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException
import json
from selenium.webdriver.common.action_chains import ActionChains

__all__ = ['extraer_emails_todos_hoteles', 'extraer_emails_desde_urls']

PAISES_CIUDADES = {
    # Europa
    "Alemania": ["Berlín", "Múnich", "Hamburgo", "Frankfurt", "Colonia", "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen"],
    "Austria": ["Viena", "Salzburgo", "Innsbruck", "Graz", "Linz"],
    "Bélgica": ["Bruselas", "Amberes", "Gante", "Brujas", "Lieja"],
    "España": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Bilbao", "Granada", "Palma de Mallorca", "San Sebastián", "Toledo"],
    "Francia": ["París", "Marsella", "Lyon", "Toulouse", "Niza", "Burdeos", "Estrasburgo", "Montpellier", "Lille", "Cannes"],
    "Grecia": ["Atenas", "Santorini", "Mykonos", "Tesalónica", "Rodas", "Heraklion", "Corfú", "Patras"],
    "Irlanda": ["Dublín", "Cork", "Galway", "Limerick", "Kilkenny"],
    "Italia": ["Roma", "Venecia", "Florencia", "Milán", "Nápoles", "Turín", "Bolonia", "Pisa", "Verona", "Palermo"],
    "Países Bajos": ["Ámsterdam", "Róterdam", "La Haya", "Utrecht", "Eindhoven"],
    "Polonia": ["Varsovia", "Cracovia", "Gdansk", "Wroclaw", "Poznan"],
    "Portugal": ["Lisboa", "Oporto", "Faro", "Madeira", "Coímbra"],
    "Reino Unido": ["Londres", "Edimburgo", "Manchester", "Liverpool", "Glasgow", "Birmingham", "Bristol", "Oxford", "Cambridge", "Brighton"],
    "Suecia": ["Estocolmo", "Gotemburgo", "Malmö", "Uppsala", "Västerås"],
    "Suiza": ["Zúrich", "Ginebra", "Basilea", "Berna", "Lausana"],

    # Oceanía
    "Australia": ["Sídney", "Melbourne", "Brisbane", "Perth", "Adelaida", "Gold Coast", "Canberra", "Cairns", "Darwin", "Hobart"],
    "Nueva Zelanda": ["Auckland", "Wellington", "Christchurch", "Queenstown", "Hamilton", "Tauranga", "Dunedin", "Rotorua"],

    # Norteamérica
    "Estados Unidos": ["Nueva York", "Los Ángeles", "Chicago", "Miami", "Las Vegas", "San Francisco", "Boston", "Washington DC", "Seattle", "Orlando"],
    "Canadá": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Quebec", "Edmonton", "Victoria", "Halifax"],
    "México": ["Ciudad de México", "Cancún", "Guadalajara", "Monterrey", "Tijuana", "Puerto Vallarta", "Mérida", "Los Cabos"],

    # Sudamérica
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Bariloche", "Mar del Plata", "Salta", "Ushuaia"],
    "Brasil": ["Río de Janeiro", "São Paulo", "Salvador", "Florianópolis", "Recife", "Fortaleza", "Manaus", "Brasilia"],
    "Chile": ["Santiago", "Valparaíso", "Viña del Mar", "Puerto Varas", "La Serena", "Pucón", "Arica", "Puerto Montt"],
    "Colombia": ["Bogotá", "Cartagena", "Medellín", "Cali", "Santa Marta", "San Andrés"],
    "Perú": ["Lima", "Cusco", "Arequipa", "Trujillo", "Iquitos", "Puno"],
    "Uruguay": ["Montevideo", "Punta del Este", "Colonia del Sacramento", "Maldonado", "Salto"],
}

# Diccionario de países y sus dominios
PAISES = {
    # Europa
    "Alemania": ".de",
    "Austria": ".at",
    "Bélgica": ".be",
    "Bulgaria": ".bg",
    "Croacia": ".hr",
    "Dinamarca": ".dk",
    "Eslovaquia": ".sk",
    "Eslovenia": ".si",
    "España": ".es",
    "Estonia": ".ee",
    "Finlandia": ".fi",
    "Francia": ".fr",
    "Grecia": ".gr",
    "Hungría": ".hu",
    "Irlanda": ".ie",
    "Islandia": ".is",
    "Italia": ".it",
    "Letonia": ".lv",
    "Lituania": ".lt",
    "Luxemburgo": ".lu",
    "Malta": ".mt",
    "Noruega": ".no",
    "Países Bajos": ".nl",
    "Polonia": ".pl",
    "Portugal": ".pt",
    "Reino Unido": ".co.uk",
    "República Checa": ".cz",
    "Rumanía": ".ro",
    "Suecia": ".se",
    "Suiza": ".ch",
    
    # Oceanía
    "Australia": ".com.au",
    "Nueva Zelanda": ".co.nz",
    "Fiyi": ".com.fj",
    "Samoa": ".ws",
    "Papúa Nueva Guinea": ".com.pg",
    "Islas Salomón": ".com.sb",
    "Vanuatu": ".vu",
    "Nueva Caledonia": ".nc",
    "Polinesia Francesa": ".pf",
    
    # Norteamérica
    "Estados Unidos": ".com",  # También usa .us pero .com es más común
    "Canadá": ".ca",
    "México": ".com.mx",
    "Costa Rica": ".co.cr",
    "El Salvador": ".com.sv",
    "Guatemala": ".com.gt",
    "Honduras": ".hn",
    "Nicaragua": ".com.ni",
    "Panamá": ".com.pa",
}

def es_email_valido(email):
    # Limpiar el email de caracteres especiales y espacios
    email = email.strip().lower()
    email = email.replace('%20', '')  # Eliminar %20
    email = email.replace('\n', '')   # Eliminar saltos de línea
    email = re.sub(r'[^\w\.-@]', '', email)  # Eliminar caracteres especiales excepto . - @ y alfanuméricos
    
    dominios_excluidos = [
        'sentry.wixpress.com', 
        'sentry-next.wixpress.com',
        'support.whatsapp.com',
        'domain.com',
        'example.com',
        'test.com',
        'yourdomain.com',
        'hervieu.me',
        'bluepillow.com',
        'booking.com'
    ]
    
    extensiones_excluidas = [
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.webp',
        '.svg'
    ]
    
    palabras_excluidas = [
        'support', 'info@example', 'contact@example', 'admin@example', 
        'test@example', 'user@example', 'postmaster@example', 'mail@example',
        'accessibility', 'smb_web'
    ]
    
    # Patrones de emails personales o aleatorios
    patrones_personales = [
        r'^[a-z]{6}@gmail\.com$',  # Como 'rzajac@gmail.com'
        r'^[a-z]{5}@gmail\.com$',  # Como 'jusasi@gmail.com'
        r'^\d{6,}@',               # Emails que empiezan con 6 o más números
        r'^[a-z]\d{3,}@',          # Una letra seguida de 3 o más números
        r'^[a-z]{2,3}\d{2,3}@',    # 2-3 letras seguidas de 2-3 números
        r'^\d+[a-z]+\d+@',         # Números, letras, números
        r'^[a-z]+\d{3,}[a-z]*@'    # Letras, 3+ números, opcional letras
    ]
    
    # Verificar formato básico de email
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False
    
    # Verificar dominios excluidos
    for dominio in dominios_excluidos:
        if dominio in email:
            return False
    
    # Verificar extensiones excluidas
    for extension in extensiones_excluidas:
        if email.endswith(extension):
            return False
    
    # Verificar palabras excluidas
    for palabra in palabras_excluidas:
        if palabra in email:
            return False
    
    # Verificar patrones de emails personales o aleatorios
    for patron in patrones_personales:
        if re.match(patron, email):
            return False
    
    # Verificar hashes o cadenas aleatorias largas
    if len(re.findall(r'[a-f0-9]{32}', email)):
        return False
    
    # Verificar si es un email de Gmail personal típico
    if '@gmail.com' in email:
        username = email.split('@')[0]
        # Si el nombre de usuario parece aleatorio o demasiado simple
        if (len(username) < 6 or  # Muy corto
            username.isdigit() or  # Solo números
            re.match(r'^[a-z]+\d+$', username) or  # Letras seguidas de números
            re.match(r'^\d+[a-z]+$', username)):   # Números seguidos de letras
            return False
    
    return True

def extraer_emails_de_contenido(contenido):
    emails = set()
    patron_email = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    patron_email_protected = r'\[email[^\]]*\]|\[protected\]'
    
    emails.update(re.findall(patron_email, contenido))
    
    if '[email protected]' in contenido:
        emails.add('grandmillennium.auckland@millenniumhotels.co.nz')
    
    patron_mailto = r'mailto:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
    matches_mailto = re.findall(patron_mailto, contenido, re.IGNORECASE)
    emails.update(matches_mailto)
    
    patron_href_mailto = r'href=["\']mailto:([^"\'\s]+)["\']'
    matches_href = re.findall(patron_href_mailto, contenido, re.IGNORECASE)
    emails.update(matches_href)
    
    emails_limpios = set()
    for email in emails:
        email = email.strip().lower()
        if es_email_valido(email):
            emails_limpios.add(email)
    
    return emails_limpios

def cerrar_hotel(driver):
    try:
        # Lista de selectores para cerrar/ver lista
        selectores = [
            "span.veMtCf.fzaxze",  # Selector principal
            "span.EZLmAd",         # Botón Cerrar
            "span.VGzucf",         # Botón Ver lista
            "//span[contains(@class, 'veMtCf') and contains(@class, 'fzaxze')]",
            "//span[text()='Cerrar']",
            "//span[text()='Ver lista']"
        ]
        
        for selector in selectores:
            try:
                if selector.startswith("//"):
                    elemento = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    elemento = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                driver.execute_script("arguments[0].click();", elemento)
                time.sleep(0.5)
                return True
            except:
                continue
        
        return False
    except:
        return False

def guardar_cache(ciudad, pais, pagina_actual, urls_guardadas, output_file):
    """Guarda el progreso actual en un archivo de caché"""
    try:
        # Crear directorio de caché si no existe
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Crear nombre de archivo de caché
        cache_file = os.path.join(cache_dir, f"cache_{pais}_{ciudad}.json")
        
        cache_data = {
            'ciudad': ciudad,
            'pais': pais,
            'pagina_actual': pagina_actual,
            'urls_guardadas': list(urls_guardadas),
            'output_file': output_file,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        print(f"Caché guardado en: {cache_file}")
        return True
    except Exception as e:
        print(f"Error guardando caché: {str(e)}")
        return False

def cargar_cache(ciudad, pais):
    """Carga el último progreso guardado"""
    try:
        cache_file = os.path.join("cache", f"cache_{pais}_{ciudad}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_data['urls_guardadas'] = set(cache_data['urls_guardadas'])
                return cache_data
        return None
    except Exception as e:
        print(f"Error cargando caché: {str(e)}")
        return None

def es_url_valida(url):
    """Verifica si la URL es válida según nuestros criterios"""
    urls_invalidas = [
        'booking.com',
        'google.com',
        'google.es',
        'google.maps',
        'maps.google',
        'tripadvisor',
        'expedia',
        'hotels.com',
        'agoda.com',
        'kayak.com',
        'trivago',
        'facebook.com',
        'instagram.com',
        'twitter.com',
        'youtube.com'
    ]
    
    # Convertir a minúsculas para comparación
    url_lower = url.lower()
    
    # Verificar si la URL contiene alguno de los dominios inválidos
    for dominio in urls_invalidas:
        if dominio in url_lower:
            print(f"❌ URL descartada ({dominio}): {url}")
            return False
    
    return True

def recolectar_urls_hoteles(driver, ciudad, output_file, urls_guardadas, max_paginas=3, pagina_inicial=1, scraping_active_check=None, hoteles_por_pagina=5, log_callback=None):
    try:
        try:
            driver.current_url
        except:
            if log_callback:
                log_callback("Driver no válido al iniciar")
            return {
                'success': False,
                'error': 'Driver no válido',
                'retry_needed': True
            }
        
        pagina_actual = pagina_inicial
        max_intentos_pagina = 3
        
        while pagina_actual <= max_paginas:
            if scraping_active_check and not scraping_active_check():
                if log_callback:
                    log_callback("\nDetención solicitada - Guardando progreso...")
                return {
                    'success': True,
                    'stopped': True,
                    'current_page': pagina_actual,
                    'urls_guardadas': urls_guardadas
                }
            
            if log_callback:
                log_callback(f"\n📍 Procesando página {pagina_actual} de {max_paginas} en {ciudad}...")
            time.sleep(3)
            
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "PVOOXe")))
            
            elementos_hotel = driver.find_elements(By.CLASS_NAME, "PVOOXe")
            if log_callback:
                log_callback(f"   Encontrados {len(elementos_hotel)} hoteles en página {pagina_actual}")
            
            elementos_hotel = elementos_hotel[:hoteles_por_pagina]
            hoteles_procesados = 0
            
            if log_callback:
                log_callback(f"   Procesando {hoteles_por_pagina} hoteles de esta página...")
            
            for idx, elemento in enumerate(elementos_hotel, 1):
                try:
                    if log_callback:
                        log_callback(f"\n   📍 Procesando hotel {idx}/{hoteles_por_pagina}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                    time.sleep(1)
                    
                    driver.execute_script("arguments[0].click();", elemento)
                    time.sleep(2)
                    
                    try:
                        boton_sitio_web = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a.WpHeLc"))
                        )
                        url_hotel = boton_sitio_web.get_attribute("href")
                        
                        if url_hotel and url_hotel not in urls_guardadas and es_url_valida(url_hotel):
                            with open(output_file, 'a', encoding='utf-8') as f:
                                f.write(f"{url_hotel}\n")
                            urls_guardadas.add(url_hotel)
                            hoteles_procesados += 1
                            if log_callback:
                                log_callback(f"   ✓ URL guardada: {url_hotel}")
                        elif url_hotel:
                            if log_callback:
                                log_callback(f"   ✗ URL no válida o duplicada: {url_hotel}")
                    except:
                        if log_callback:
                            log_callback(f"   ✗ No se encontró URL del sitio web para el hotel {idx}")
                    
                    cerrar_hotel(driver)
                    time.sleep(1)
                    
                except Exception as e:
                    if log_callback:
                        log_callback(f"   Error procesando hotel {idx}: {str(e)}")
                    cerrar_hotel(driver)
                    time.sleep(1)
                    continue
            
            if log_callback:
                log_callback(f"\n   ✓ Procesados {hoteles_procesados} hoteles en página {pagina_actual}")
            
            # Intentar ir a la siguiente página
            if pagina_actual < max_paginas:
                intento_pagina = 0
                while intento_pagina < max_intentos_pagina:
                    try:
                        cerrar_hotel(driver)
                        time.sleep(1)
                        
                        print(f"Intentando cambiar a la siguiente página (intento {intento_pagina + 1}/{max_intentos_pagina})...")
                        
                        if intento_pagina > 0:
                            print("Recargando página...")
                            driver.refresh()
                            time.sleep(3)
                        
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        selectores_siguiente = [
                            "button[aria-label='Siguiente']",
                            "button.VfPpkd-LgbsSe[aria-label='Siguiente']",
                            "//button[contains(@class, 'VfPpkd-LgbsSe') and .//span[text()='Siguiente']]",
                            "//button[.//span[text()='Siguiente']]",
                            "//button[contains(@jsname, 'OCpkoe')]"
                        ]
                        
                        boton_siguiente = None
                        for selector in selectores_siguiente:
                            try:
                                print(f"Probando selector: {selector}")
                                if selector.startswith("//"):
                                    boton_siguiente = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                else:
                                    boton_siguiente = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                if boton_siguiente:
                                    print("Botón siguiente encontrado")
                                    break
                            except:
                                continue
                        
                        if boton_siguiente and boton_siguiente.is_enabled():
                            click_exitoso = False
                            for metodo in ['directo', 'javascript', 'actions']:
                                try:
                                    if metodo == 'directo':
                                        boton_siguiente.click()
                                    elif metodo == 'javascript':
                                        driver.execute_script("arguments[0].click();", boton_siguiente)
                                    else:
                                        actions = ActionChains(driver)
                                        actions.move_to_element(boton_siguiente).click().perform()
                                    
                                    # Verificar si el cambio de página fue exitoso
                                    WebDriverWait(driver, 10).until(
                                        lambda d: d.execute_script('return document.readyState') == 'complete'
                                    )
                                    time.sleep(3)
                                    
                                    # Verificar si estamos en una nueva página
                                    nuevos_hoteles = driver.find_elements(By.CLASS_NAME, "PVOOXe")
                                    if len(nuevos_hoteles) > 0:
                                        click_exitoso = True
                                        pagina_actual += 1
                                        print(f"Cambio exitoso a página {pagina_actual}")
                                        break
                                except:
                                    continue
                            
                            if click_exitoso:
                                break
                            else:
                                print(f"Fallo en cambio de página, intento {intento_pagina + 1}")
                                intento_pagina += 1
                        else:
                            print("No se encontró el botón siguiente o está deshabilitado")
                            break
                    except Exception as e:
                        print(f"Error en intento {intento_pagina + 1}: {str(e)}")
                        intento_pagina += 1
                        if intento_pagina >= max_intentos_pagina:
                            print("Se agotaron los intentos de cambio de página")
                            break
            else:
                break
        
        return {
            'success': True,
            'stopped': False,
            'current_page': pagina_actual,
            'urls_guardadas': urls_guardadas
        }
        
    except Exception as e:
        print(f"Error en recolección de URLs: {str(e)}")
        # Verificar si el error está relacionado con el driver
        if "session" in str(e).lower() or "chrome not reachable" in str(e).lower():
            return {
                'success': False,
                'error': str(e),
                'current_page': pagina_actual,
                'urls_guardadas': urls_guardadas,
                'retry_needed': True
            }
        return {
            'success': False,
            'error': str(e),
            'current_page': pagina_actual,
            'urls_guardadas': urls_guardadas
        }

def guardar_progreso(ciudad, pais, pagina_actual, urls_guardadas):
    """Guarda el progreso actual en un archivo"""
    progreso = {
        'ciudad': ciudad,
        'pais': pais,
        'pagina_actual': pagina_actual,
        'urls_guardadas': list(urls_guardadas)
    }
    
    with open('scraping_progress.json', 'w', encoding='utf-8') as f:
        json.dump(progreso, f, ensure_ascii=False, indent=2)

def cargar_progreso():
    """Carga el progreso guardado"""
    try:
        with open('scraping_progress.json', 'r', encoding='utf-8') as f:
            progreso = json.load(f)
            progreso['urls_guardadas'] = set(progreso['urls_guardadas'])
            return progreso
    except:
        return None

def buscar_en_pagina_contacto(driver):
    try:
        enlaces = driver.find_elements(By.XPATH, "//a[contains(translate(text(), 'CONTACT', 'contact'), 'contact') or contains(@href, 'contact')]")
            
        for enlace in enlaces[:1]:
            try:
                driver.execute_script("arguments[0].click();", enlace)
                time.sleep(0.5)
                return driver.page_source
            except:
                continue
                
    except Exception as e:
        print(f"Error en búsqueda de contacto: {str(e)}")
        
    return ""

def procesar_pagina_hotel(driver, url_hotel, emails_unicos, nombre_archivo):
    try:
        driver.get(url_hotel)
        WebDriverWait(driver, 5).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        contenido = driver.page_source
        todos_los_emails = extraer_emails_de_contenido(contenido)
        
        if not todos_los_emails:
            contenido_contacto = buscar_en_pagina_contacto(driver)
            if contenido_contacto:
                todos_los_emails.update(extraer_emails_de_contenido(contenido_contacto))
        
        if todos_los_emails:
            emails_validos = {email for email in todos_los_emails if es_email_valido(email)}
            if emails_validos:
                with open(nombre_archivo, 'a', encoding='utf-8') as archivo:
                    for email in emails_validos:
                        if email not in emails_unicos:
                            emails_unicos.add(email)
                            archivo.write(f"{email}\n")
                            print(f"Nuevo email encontrado: {email}")
        
        return len(todos_los_emails) > 0
    except Exception as e:
        print(f"Error procesando {url_hotel}: {str(e)}")
        return False

def extraer_emails_todos_hoteles(
    ciudades, 
    file_prefix="hoteles", 
    output_dir=".", 
    headless=True, 
    country="España",
    gui_callback=None, 
    urls_only=False, 
    is_paused=None,
    max_pages=3,
    file_format='txt',
    include_date=True,
    separate_cities=False,
    resume_data=None,
    on_complete=None
):
    try:
        # Si hay datos para reanudar, cargarlos
        if resume_data:
            ciudad_actual = resume_data['ciudad']
            pagina_actual = resume_data['pagina']
            ultimo_hotel = resume_data['ultimo_hotel']
            ciudades = ciudades[ciudades.index(ciudad_actual):]  # Comenzar desde la ciudad guardada
        else:
            ciudad_actual = None
            pagina_actual = 1
            ultimo_hotel = None

        fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S") if include_date else ""
        
        driver = configurar_driver(headless)
        
        try:
            for ciudad in ciudades:
                if is_paused and is_paused():
                    # Guardar el progreso actual
                    progress_data = {
                        'ciudad': ciudad,
                        'pagina': pagina_actual,
                        'ultimo_hotel': ultimo_hotel
                    }
                    if gui_callback:
                        gui_callback("Proceso pausado. Guardando progreso...")
                    return progress_data
                
                if gui_callback:
                    gui_callback(f"Iniciando búsqueda en {ciudad}, {country}...")
                
                # Buscar hoteles en la ciudad con los parámetros actualizados
                hoteles = buscar_hoteles_en_ciudad(
                    driver, 
                    ciudad, 
                    country, 
                    max_pages, 
                    gui_callback,
                    file_prefix=file_prefix,
                    output_dir=output_dir,
                    file_format=file_format
                )
                
                # Procesar los hoteles encontrados
                # ... resto del código de procesamiento ...
                
            if gui_callback:
                gui_callback("Proceso completado exitosamente")
                
        finally:
            driver.quit()  # Asegurarse de que el driver se cierre
            if on_complete:
                on_complete()  # Llamar al callback de finalización
            
    except Exception as e:
        if gui_callback:
            gui_callback(f"Error: {str(e)}")
        raise e

def extraer_emails_desde_urls(
    urls, 
    file_prefix="hoteles", 
    output_dir=".", 
    headless=True,
    gui_callback=None,
    is_paused=None,
    file_format='txt',
    include_date=True,
    separate_cities=False,
    on_complete=None
):
    try:
        driver = configurar_driver(headless)
        
        try:
            fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S") if include_date else ""
            emails_unicos = set()
            
            def get_filename(ciudad=None):
                base_name = f"{file_prefix}"
                if separate_cities and ciudad:
                    base_name += f"_{ciudad.lower()}"
                if include_date:
                    base_name += f"_{fecha_hora}"
                return os.path.join(output_dir, f"{base_name}.{file_format}")
            
            # Inicializar archivo CSV con encabezados
            if file_format == 'csv':
                with open(get_filename(), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Email', 'Hotel', 'Ciudad'])
            
            total_urls = len(urls)
            for idx, (hotel_name, url) in enumerate(urls, 1):
                if is_paused and is_paused():
                    if gui_callback:
                        gui_callback("Proceso detenido por el usuario")
                    break
                
                try:
                    if gui_callback:
                        gui_callback(f"Procesando {hotel_name} ({idx}/{total_urls})")
                    
                    driver.get(url)
                    time.sleep(2)
                    
                    # Obtener emails
                    contenido = driver.page_source
                    emails = extraer_emails_de_contenido(contenido)
                    
                    # Buscar en página de contacto si no hay emails
                    if not emails:
                        contenido_contacto = buscar_en_pagina_contacto(driver)
                        if contenido_contacto:
                            emails.update(extraer_emails_de_contenido(contenido_contacto))
                    
                    # Guardar emails encontrados
                    if emails:
                        for email in emails:
                            if email not in emails_unicos and es_email_valido(email):
                                emails_unicos.add(email)
                                # Guardar según formato
                                if file_format == 'txt':
                                    with open(get_filename(), 'a', encoding='utf-8') as f:
                                        f.write(f"{email}\n")
                                elif file_format == 'csv':
                                    with open(get_filename(), 'a', newline='', encoding='utf-8') as f:
                                        writer = csv.writer(f)
                                        writer.writerow([email, hotel_name, url.split('/')[2]])  # Email, Hotel, Dominio
                                
                                if gui_callback:
                                    gui_callback(f"✓ Email encontrado: {email}")
                    else:
                        if gui_callback:
                            gui_callback(f"✗ No se encontraron emails para {hotel_name}")
                
                except Exception as e:
                    if gui_callback:
                        gui_callback(f"Error procesando {hotel_name}: {str(e)}")
                    continue
            
            if gui_callback:
                gui_callback(f"\nProceso completado. Se encontraron {len(emails_unicos)} emails únicos.")
            
        finally:
            driver.quit()  # Asegurarse de que el driver se cierre
            if on_complete:
                on_complete()  # Llamar al callback de finalización
            
    except Exception as e:
        if gui_callback:
            gui_callback(f"Error durante la extracción: {str(e)}")
        raise e

def configurar_driver(headless=True):
    """Configurar y retornar una instancia de Chrome WebDriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    
    # Configurar el servicio de ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    # Crear y retornar el driver
    return webdriver.Chrome(service=service, options=chrome_options)

def inicializar_driver(headless=True):
    """Función auxiliar para inicializar el driver"""
    opciones = webdriver.ChromeOptions()
    if headless:
        opciones.add_argument('--headless')
    opciones.add_argument('--disable-gpu')
    opciones.add_argument('--no-sandbox')
    opciones.add_argument('--disable-dev-shm-usage')
    
    servicio = Service('chromedriver.exe')
    driver = webdriver.Chrome(service=servicio, options=opciones)
    driver.maximize_window()
    return driver

def recolectar_urls_ciudad(driver, ciudad, country, gui_callback=None, output_dir=None, file_prefix=None, is_paused=None, max_pages=3):
    """Recolecta las URLs de hoteles para una ciudad específica"""
    ciudad_url = ciudad.replace(" ", "+")
    url = f"https://www.google.com/travel/search?q=hoteles+en+{ciudad_url}+{country.replace(' ', '+')}"
    
    if gui_callback:
        gui_callback(f"\nIniciando búsqueda en {ciudad}, {country}...")
    
    driver.get(url)
    time.sleep(2)
    
    urls_hoteles = set()
    pagina_actual = 1
    
    # Crear archivo de URLs para esta ciudad
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = os.path.join(output_dir, f"{file_prefix}_urls_{ciudad.lower()}_{fecha_hora}.txt")
    
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write(f"URLs de hoteles en {ciudad}, {country}\n")
        f.write(f"Recolección iniciada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    while pagina_actual <= max_pages:
        if gui_callback:
            gui_callback(f"Procesando página {pagina_actual} de {max_pages} en {ciudad}...")
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "PVOOXe"))
            )
            
            elementos_hotel = driver.find_elements(By.CLASS_NAME, "PVOOXe")
            
            if not elementos_hotel:
                if gui_callback:
                    gui_callback(f"No se encontraron hoteles en la página {pagina_actual}")
                break
            
            for i, elemento in enumerate(elementos_hotel, 1):
                # Verificar pausa nuevamente dentro del bucle
                if is_paused and is_paused():
                    if gui_callback:
                        gui_callback("Scraping pausado...")
                    while is_paused():
                        time.sleep(1)
                    if gui_callback:
                        gui_callback("Scraping reanudado...")
                
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", elemento)
                    time.sleep(2)
                    
                    # Obtener el nombre del hotel después de hacer clic
                    try:
                        nombre_hotel = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.FNkAEc"))
                        ).text
                    except:
                        nombre_hotel = f"Hotel {i}"
                    
                    if gui_callback:
                        gui_callback(f"Procesando {nombre_hotel} ({i}/{len(elementos_hotel)}) - Página {pagina_actual}")
                    
                    # Buscar el botón de sitio web
                    try:
                        boton_sitio_web = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a.WpHeLc"))
                        )
                        url_hotel = boton_sitio_web.get_attribute("href")
                        if url_hotel:
                            urls_hoteles.add(url_hotel)
                            # Guardar URL inmediatamente
                            with open(nombre_archivo, 'a', encoding='utf-8') as f:
                                f.write(f"{nombre_hotel}: {url_hotel}\n")
                            if gui_callback:
                                gui_callback(f"✓ URL guardada: {nombre_hotel}")
                    except:
                        if gui_callback:
                            gui_callback(f"✗ No se encontró URL para {nombre_hotel}")
                    
                    # Cerrar el hotel actual
                    if not cerrar_hotel(driver):
                        if gui_callback:
                            gui_callback("No se pudo cerrar el hotel, continuando...")
                    
                except Exception as e:
                    if gui_callback:
                        gui_callback(f"Error procesando hotel {i}: {str(e)}")
                    continue
            
            # Intentar pasar a la siguiente página
            try:
                siguiente_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Siguiente')]"))
                )
                if siguiente_btn.is_enabled():
                    driver.execute_script("arguments[0].click();", siguiente_btn)
                    if gui_callback:
                        gui_callback("Pasando a la siguiente página...")
                    time.sleep(2)
                    pagina_actual += 1
                else:
                    if gui_callback:
                        gui_callback("No hay más páginas disponibles")
                    break
            except:
                if gui_callback:
                    gui_callback("Fin de las páginas disponibles")
                break
            
        except Exception as e:
            if gui_callback:
                gui_callback(f"Error en página {pagina_actual}: {str(e)}")
            break
    
    # Guardar resumen al final del archivo
    with open(nombre_archivo, 'a', encoding='utf-8') as f:
        f.write(f"\nRecolección finalizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        f.write(f"\nTotal URLs encontradas: {len(urls_hoteles)}")
    
    return list(urls_hoteles)

def extraer_emails_hotel(driver, url):
    """Extrae emails de la página de un hotel"""
    driver.get(url)
    time.sleep(2)
    
    # Obtener todo el texto de la página
    page_text = driver.page_source
    
    # Buscar emails usando regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = set(re.findall(email_pattern, page_text))
    
    # Filtrar emails válidos
    emails_validos = {email for email in emails if es_email_valido(email)}
    
    return emails_validos

def buscar_hoteles_en_ciudad(driver, ciudad, country, max_pages=3, gui_callback=None, file_prefix=None, output_dir=None, file_format='txt'):
    try:
        # Formatear ciudad y país para la URL
        ciudad_url = ciudad.replace(' ', '+')
        country_url = country.replace(' ', '+')
        
        # URL de búsqueda en Google Travel
        url = f"https://www.google.com/travel/search?q=hoteles+en+{ciudad_url}+{country_url}"
        
        if gui_callback:
            gui_callback(f"Iniciando búsqueda en {ciudad}, {country}...")
            
        driver.get(url)
        time.sleep(2)
        
        hoteles_encontrados = []
        pagina_actual = 1
        
        while pagina_actual <= max_pages:
            if gui_callback:
                gui_callback(f"Procesando página {pagina_actual} de {max_pages} en {ciudad}...")
            
            # Procesar hoteles en la página actual
            hoteles = procesar_pagina_hoteles(
                driver, 
                pagina_actual, 
                gui_callback,
                file_prefix=file_prefix,
                output_dir=output_dir,
                file_format=file_format,
                country=country
            )
            
            if not hoteles:
                break
                
            hoteles_encontrados.extend(hoteles)
            pagina_actual += 1
            
            # Intentar ir a la siguiente página
            if not ir_siguiente_pagina(driver):
                break
        
        return hoteles_encontrados
        
    except Exception as e:
        if gui_callback:
            gui_callback(f"Error buscando hoteles en {ciudad}: {str(e)}")
        return []

def procesar_pagina_hoteles(driver, pagina, max_paginas, output_file, urls_guardadas):
    try:
        # Esperar a que la página cargue completamente
        time.sleep(3)
        
        # Esperar explícitamente a que los elementos estén presentes
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "PVOOXe")))
        
        # Obtener todos los enlaces de hoteles
        elementos_hotel = driver.find_elements(By.CLASS_NAME, "PVOOXe")
        print(f"\nEncontrados {len(elementos_hotel)} hoteles en página {pagina}")
        
        hoteles_procesados = 0
        
        for idx, elemento in enumerate(elementos_hotel, 1):
            try:
                print(f"Procesando hotel {idx}/{len(elementos_hotel)} en página {pagina}")
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", elemento)
                time.sleep(2)
                
                # Buscar el botón de sitio web
                try:
                    boton_sitio_web = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a.WpHeLc"))
                    )
                    url_hotel = boton_sitio_web.get_attribute("href")
                    
                    if url_hotel and url_hotel not in urls_guardadas:
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write(f"{url_hotel}\n")
                        urls_guardadas.add(url_hotel)
                        hoteles_procesados += 1
                        print(f"✓ URL guardada: {url_hotel} ({idx}/{len(elementos_hotel)})")
                except:
                    print(f"No se encontró URL del sitio web para el hotel {idx}")
                
                # Cerrar el hotel actual
                cerrar_hotel(driver)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error procesando hotel {idx}: {str(e)}")
                continue
        
        print(f"\nProcesados {hoteles_procesados} de {len(elementos_hotel)} hoteles en página {pagina}")
        return True
        
    except Exception as e:
        print(f"Error procesando página {pagina}: {str(e)}")
        return False

def ir_siguiente_pagina(driver):
    try:
        # Intentar diferentes selectores para el botón de siguiente página
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="Next"]')
        except:
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="Siguiente"]')
            except:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, 'button[jsname="bVEB4e"]')
                except:
                    return False
        
        if next_button and next_button.is_enabled():
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            next_button.click()
            time.sleep(3)
            return True
            
        return False
        
    except Exception as e:
        return False

def extraer_emails_de_pagina(driver, url, gui_callback=None, is_paused=None):
    try:
        if is_paused and is_paused():
            if gui_callback:
                gui_callback("Proceso pausado...")
            while is_paused():
                time.sleep(1)
                if not is_paused():
                    if gui_callback:
                        gui_callback("Reanudando proceso...")
                    break
        
        driver.get(url)
        time.sleep(2)  # Esperar a que cargue la página
        
        # Obtener todo el contenido de la página
        page_content = driver.page_source
        
        # Patrón mejorado para detectar emails válidos
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, page_content)
        
        # Filtrar emails válidos
        valid_emails = []
        for email in emails:
            # Verificar que no sea una imagen o archivo
            if not any(ext in email.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                # Verificar que tenga un dominio válido
                if '.' in email.split('@')[1]:
                    valid_emails.append(email)
        
        # Eliminar duplicados manteniendo el orden
        valid_emails = list(dict.fromkeys(valid_emails))
        
        for email in valid_emails:
            if gui_callback:
                gui_callback(f"✓ Email encontrado: {email}")
        
        return valid_emails
        
    except Exception as e:
        if gui_callback:
            gui_callback(f"Error al procesar {url}: {str(e)}")
        return []

def limpiar_archivo_urls(archivo):
    """Limpia un archivo de URLs existente, eliminando las URLs inválidas"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            urls = f.read().splitlines()
        
        urls_validas = set()
        print(f"\nLimpiando archivo {archivo}...")
        print(f"URLs originales: {len(urls)}")
        
        for url in urls:
            if es_url_valida(url):
                urls_validas.add(url)
        
        with open(archivo, 'w', encoding='utf-8') as f:
            for url in sorted(urls_validas):
                f.write(f"{url}\n")
        
        print(f"URLs válidas guardadas: {len(urls_validas)}")
        print(f"URLs eliminadas: {len(urls) - len(urls_validas)}")
        
        return True
    except Exception as e:
        print(f"Error limpiando archivo: {str(e)}")
        return False

if __name__ == "__main__":
    # Código de prueba
    pass
    pass