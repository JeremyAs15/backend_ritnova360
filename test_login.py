import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

@pytest.fixture
def driver():
    chrome_options = Options()
    
    # 1. Configuraciones para ocultar la automatización de Selenium ante Cloudflare
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Ocultar la bandera de webdriver en el navegador
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

def test_login_flow(driver):
    # 1. Navegar a tu servidor de Frontend local
    driver.get("http://localhost:5173/login")
    
    # Esperamos a que se cargue el widget del CAPTCHA de desarrollo
    time.sleep(3)
    
    # 2. Localizar campos de correo, clave y el botón de submit
    email_input = driver.find_element(By.XPATH, "//input[@type='email']")
    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    # 3. Rellenar las credenciales
    email_input.send_keys("estudiante.pedro@correo.com")
    password_input.send_keys("Password123")
    
    # Pequeña pausa antes de dar clic para simular interacción natural
    time.sleep(2)
    
    # 4. Hacer clic en el botón de ingreso
    submit_button.click()
    
    # Damos tiempo para que el servidor local de Django procese el inicio de sesión
    time.sleep(3)

    # 5. Diagnóstico de errores de credenciales (si el login fallara)
    try:
        error_box = driver.find_element(By.XPATH, "//div[contains(@style, 'color: rgb(211, 47, 47)') or contains(@style, 'color: #d32f2f')]")
        print(f"\n[Alerta de la Interfaz]: {error_box.text}")
    except Exception:
        pass

    # 6. Aserción A: Esperar a que la URL cambie y confirme la redirección a /perfil
    WebDriverWait(driver, 15).until(
        EC.url_contains("/perfil")
    )
    print("\n[Éxito] Redirección correcta detectada hacia la ruta /perfil")

    # 7. Aserción B: Confirmar que cargó el Sidebar y el nombre de usuario de Pedro está visible
    welcome_msg = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sidebar__user-name"))
    )
    
    print(f"[Éxito] Nombre del usuario detectado en la barra lateral: {welcome_msg.text}")
    
    # Validación final de que el nombre del estudiante se está renderizando correctamente
    assert len(welcome_msg.text) > 0
    print("\n[Resultado] Test de Login: COMPLETADO CON ÉXITO")