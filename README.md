# Backend Ritnova360 - Academia de Baile en Línea

Este repositorio contiene la API REST desarrollada para Ritnova360, una plataforma web que gestiona los servicios de una academia de baile en línea: administración de usuarios (directores, administradores, profesores, estudiantes), catálogo de coreografías (con clips de video), carrito de compras y simulador de facturación/ventas.

## Tecnologías Utilizadas
- **Lenguaje:** Python 3.10+
- **Framework Principal:** Django 6.0 & Django Rest Framework (DRF)
- **Autenticación:** JWT (JSON Web Tokens) vía SimpleJWT
- **Base de Datos:** PostgreSQL (alojada en Supabase)
- **Despliegue sugerido:** Render (Backend)

## Guía de Instalación y Configuración Local
Sigue estos pasos detallados para configurar y ejecutar el proyecto en tu entorno local después de haber clonado el repositorio:

### 1. Preparación del Entorno Virtual
Es necesario aislar las dependencias del proyecto utilizando un entorno virtual (venv).

#### Crear el entorno virtual:
```Bash
python -m venv venv
```
Activar el entorno virtual:
En Windows (CMD):
```Bash
venv\Scripts\activate
```
En Windows (PowerShell):
```Bash
Powershell
.\venv\Scripts\Activate.ps1
```
En macOS / Linux:
```Bash
source venv/bin/activate
```

## 2. Instalación de Dependencias
Con el entorno virtual activo, instala todas las librerías necesarias especificadas en el archivo requirements.txt:
```Bash
pip install -r requirements.txt
```

## Usuarios disponibles
Usuarios listos creados desde el backend para experimentación con el programa.

---

**Superusuario**

    correo: admin@gmail.com
    password: ritnova1234

**Director**

    correo: director.juan@ritnova360.com
    password: Password123

**Profesor de Danza**

    correo: profesor.carlos@ritnova360.com
    password: Password123

**Estudiante**

    correo: estudiante.pedro@correo.com
    password: Password123