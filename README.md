# Procesador Automático de Nóminas

Este proyecto automatiza la descarga de correos de Gmail desde un remitente específico, extrae archivos ZIP adjuntos y los sube a Google Drive.

## Características

- 🔍 Búsqueda automática de correos de `rrhh@empresa.com`
- 📧 Filtrado por correos de las últimoa 12 días con archivos adjuntos
- 🔐 Soporte para archivos ZIP protegidos con contraseña
- 🗂️ Extracción automática de archivos del ZIP
- ☁️ Subida automática a Google Drive con organización en carpetas

## Requisitos

- Python 3.8+
- Archivo `credentials.json` de Google Cloud Console con permisos OAuth 2.0
- Acceso a Gmail API (solo lectura)
- Acceso a Google Drive API (escritura de archivos)

## Configuración

### 1. Configurar Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita las APIs de Gmail y Google Drive
4. Crea credenciales OAuth 2.0 para aplicación de escritorio
5. Descarga el archivo `credentials.json` y colócalo en la carpeta del proyecto

### 2. Configurar el proyecto

1. **Asegúrate de que el archivo `credentials.json` esté en la carpeta del proyecto**

2. **Edita el archivo `config.py` para configurar la contraseña del ZIP:**
   ```python
   ZIP_PASSWORD = "tu_contraseña_aqui"  # Reemplaza con la contraseña real
   ```

3. **Opcional: Ajusta otros parámetros en `config.py`:**
   - `SENDER_EMAIL`: Email del remitente (por defecto: rrhh@empresa.com)
   - `DAYS_TO_SEARCH`: Días hacia atrás para buscar (por defecto: 12)
   - `DRIVE_FOLDER_NAME`: Nombre de la carpeta en Drive

## Instalación

Para crear y preparar el entorno virtual con las dependecias necesarias, ejecuta en PowerShell:

```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

## Uso

### Ejecución Manual

Para ejecutar el procesamiento una sola vez:

```powershell
.venv\Scripts\python.exe main.py
```

Si solo quieres usar la clase GmailProcessor (no hace las verificaciones):

```powershell
.venv\Scripts\python.exe gmail_processor.py
```

### Ejecución Automática

Para la ejecución automática se utiliza el archivo por lotes (`ejecutar_procesador.bat`) que inicia el procesamiento de nóminas.

Este archivo `.bat` se programa usando el Programador de Tareas de Windows para ejecutarse automáticamente los días **12** y **25** de cada mes, sin intervención manual.

El proceso:
- El programador de tareas de Windows ejecuta `ejecutar_procesador.bat` en las fechas indicadas
- Se inicia el procesamiento y subida de nóminas de forma automática

Puedes modificar la programación desde el Programador de Tareas de Windows para ajustar las fechas o la frecuencia según tus necesidades.

## Estructura del Proyecto

```
Auto nominas/
├── .venv/                    # Entorno virtual de Python
├── credentials.json          # Credenciales OAuth 2.0 (ya existe)
├── token.pickle              # Token de autenticación (se genera automáticamente)
├── config.py                 # Configuración del proyecto
├── gmail_processor.py        # Clase principal del procesador
├── main.py                   # Script de ejecución simple
├── requirements.txt          # Dependencias del proyecto
├── ejecutar_procesador.bat   # Script por lotes
└── README.md                 # Esta documentación
```

## Funcionamiento

1. **Autenticación**: Se autentica con Google usando OAuth 2.0
2. **Búsqueda**: Busca correos del remitente en las últimos 12 días
3. **Filtrado**: Solo procesa correos con archivos adjuntos ZIP
4. **Descarga**: Descarga los archivos ZIP adjuntos
5. **Extracción**: Extrae el contenido de los ZIP (con contraseña si es necesario)
6. **Subida**: Sube cada archivo extraído a Google Drive
7. **Organización**: Los archivos se guardan en la carpeta "NOMINAS"

## Archivos de Salida

- **Google Drive**: Los archivos extraídos se suben a la carpeta especificada
- **Token**: `token.pickle` almacena el token de autenticación para evitar re-autenticar

## Solución de Problemas

### Error de Autenticación
- Verifica que `credentials.json` esté en la carpeta correcta
- Elimina `token.pickle` para forzar nueva autenticación

### Error de Contraseña ZIP
- Verifica que la contraseña en `config.py` sea correcta
- Algunos ZIP pueden no estar protegidos con contraseña

### Error de Permisos
- Asegúrate de que las APIs estén habilitadas en Google Cloud Console
- Verifica que los scopes incluyan Gmail readonly y Drive file

### No se encuentran correos
- Verifica que el email del remitente sea correcto
- Ajusta el número de días de búsqueda en `config.py`

## Seguridad

- Las credenciales se almacenan localmente en `credentials.json` y `token.pickle`
- El proyecto solo tiene permisos de lectura en Gmail
- El acceso a Drive está limitado a archivos creados por la aplicación
- La contraseña del ZIP se almacena en texto plano en `config.py` (considera cifrarla para mayor seguridad)

## Personalización

Puedes modificar `gmail_processor.py` para:
- Cambiar el formato de nombres de archivos
- Añadir filtros adicionales para los correos
- Modificar la estructura de carpetas en Drive
- Añadir procesamiento adicional de los archivos extraídos
