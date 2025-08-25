"""
Procesador de correos de Gmail para extraer archivos ZIP y subirlos a Google Drive
Autor: Sistema automatizado
Fecha: 2025
"""

import os
import pickle
import zipfile
import io
import base64
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import config


class GmailProcessor:
    """Clase para procesar correos de Gmail y subir archivos a Drive"""
    
    # Scopes necesarios para Gmail (solo lectura) y Drive (escritura de archivos)
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        """
        Inicializa el procesador de Gmail
        
        Args:
            credentials_file (str): Ruta al archivo de credenciales OAuth 2.0
            token_file (str): Ruta al archivo de token para evitar re-autenticación
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.gmail_service = None
        self.drive_service = None
        
    def authenticate(self):
        """Autentica y crea los servicios de Gmail y Drive"""
        creds = None
        
        # Carga el token existente si está disponible
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Si no hay credenciales válidas disponibles, permite al usuario autenticarse
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Guarda las credenciales para la próxima ejecución
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Construye los servicios
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        
        print("✅ Autenticación exitosa - Servicios Gmail y Drive inicializados")
    
    def get_emails_from_sender(self, sender_email, days_back=12):
        """
        Obtiene correos del remitente especificado en el período dado
        
        Args:
            sender_email (str): Email del remitente a buscar
            days_back (int): Número de días hacia atrás para buscar (default: 12)
            
        Returns:
            list: Lista de mensajes encontrados
        """
        try:
            # Calcula la fecha hace dos semanas
            start_date = datetime.now() - timedelta(days=days_back)
            date_str = start_date.strftime('%Y/%m/%d')
            
            # Construye la query de búsqueda
            query = f'from:{sender_email} after:{date_str} has:attachment'
            
            print(f"🔍 Buscando correos de {sender_email} desde {date_str}")
            
            # Realiza la búsqueda
            result = self.gmail_service.users().messages().list(
                userId='me', q=query).execute()
            
            messages = result.get('messages', [])
            print(f"📧 Encontrados {len(messages)} correos con archivos adjuntos")
            
            return messages
            
        except Exception as error:
            print(f"❌ Error al buscar correos: {error}")
            return []
    
    def download_attachment(self, message_id, attachment_id):
        """
        Descarga un archivo adjunto específico
        
        Args:
            message_id (str): ID del mensaje
            attachment_id (str): ID del archivo adjunto
            
        Returns:
            bytes: Contenido del archivo adjunto
        """
        try:
            attachment = self.gmail_service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id).execute()
            
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            
            return file_data
            
        except Exception as error:
            print(f"❌ Error al descargar archivo adjunto: {error}")
            return None
    
    def extract_zip_content(self, zip_data, password=None):
        """
        Extrae el contenido de un archivo ZIP
        
        Args:
            zip_data (bytes): Datos del archivo ZIP
            password (str): Contraseña del ZIP si está protegido
            
        Returns:
            dict: Diccionario con nombres de archivos y su contenido
        """
        try:
            extracted_files = {}
            
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
                # Si se proporciona contraseña, la configura
                if password:
                    zip_file.setpassword(password.encode())
                
                # Extrae todos los archivos
                for file_info in zip_file.infolist():
                    if not file_info.is_dir():
                        try:
                            file_content = zip_file.read(file_info.filename)
                            extracted_files[file_info.filename] = file_content
                            print(f"📄 Extraído: {file_info.filename}")
                        except Exception as e:
                            print(f"❌ Error al extraer {file_info.filename}: {e}")
            
            return extracted_files
            
        except Exception as error:
            print(f"❌ Error al extraer ZIP: {error}")
            return {}
    
    def upload_to_drive(self, file_name, file_content, folder_name="NOMINAS"):
        """
        Sube un archivo a Google Drive en la estructura NOMINAS/2025/
        
        Args:
            file_name (str): Nombre del archivo
            file_content (bytes): Contenido del archivo
            folder_name (str): Nombre de la carpeta padre (default: "NOMINAS")
            
        Returns:
            str: ID del archivo subido o None si hubo error
        """
        try:
            # Obtiene el ID de la carpeta del año (crea estructura si no existe)
            year = file_name[-8:-4] if file_name.lower().endswith('.pdf') else file_name[-4:]
            target_folder_id = self.get_or_create_folder(folder_name, year)
            if not target_folder_id:
                print(f"❌ No se pudo configurar la carpeta de destino")
                return None
            
            # Crea el archivo
            file_metadata = {
                'name': file_name,
                'parents': [target_folder_id] if target_folder_id else []
            }
            
            # Sube el archivo
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype='application/octet-stream'
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            print(f"✅ Archivo subido a Drive: {file_name} (ID: {file_id})")
            
            return file_id
            
        except Exception as error:
            print(f"❌ Error al subir archivo a Drive: {error}")
            return None

    def get_or_create_folder(self, folder_name, year):
        """
        Busca una carpeta en Drive por nombre o la crea si no existe
        Crea estructura jerárquica: NOMINAS/2025/
        
        Args:
            folder_name (str): Nombre de la carpeta padre (ej: "NOMINAS")
            
        Returns:
            str: ID de la carpeta del año actual donde se guardarán los archivos
        """
        try:
            # Obtiene el año actual para crear la subcarpeta
            # current_year = datetime.now().year
            year_folder_name = str(year)
            
            print(f"🗂️  Configurando estructura: {folder_name}/{year_folder_name}/")
            
            # Paso 1: Buscar o crear la carpeta padre (NOMINAS)
            parent_folder_id = self._find_or_create_parent_folder(folder_name)
            
            if not parent_folder_id:
                print(f"❌ No se pudo crear la carpeta padre: {folder_name}")
                return None
            
            # Paso 2: Buscar o crear la carpeta del año dentro de la carpeta padre
            year_folder_id = self._find_or_create_year_folder(year_folder_name, parent_folder_id)
            
            if year_folder_id:
                print(f"✅ Carpeta de destino lista: {folder_name}/{year_folder_name}/ (ID: {year_folder_id})")
            
            return year_folder_id
                
        except Exception as error:
            print(f"❌ Error al manejar estructura de carpetas: {error}")
            return None
    
    def _find_or_create_parent_folder(self, folder_name):
        """
        Busca o crea la carpeta padre (NOMINAS)
        
        Args:
            folder_name (str): Nombre de la carpeta padre
            
        Returns:
            str: ID de la carpeta padre
        """
        try:
            # Busca carpetas existentes por nombre en la raíz
            results = self.drive_service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name, parents)",
                orderBy="createdTime desc"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                # Prioriza carpetas en la raíz (sin padres)
                root_folders = [f for f in folders if not f.get('parents')]
                selected_folder = root_folders[0] if root_folders else folders[0]
                
                folder_id = selected_folder['id']
                print(f"📁 Usando carpeta padre existente: {folder_name} (ID: {folder_id})")
                
                if len(folders) > 1:
                    print(f"ℹ️  Se encontraron {len(folders)} carpetas '{folder_name}', usando la de la raíz")
                
                return folder_id
            else:
                # Crea nueva carpeta padre en la raíz
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                print(f"📁 Carpeta padre creada: {folder_name} (ID: {folder_id})")
                
                return folder_id
                
        except Exception as error:
            print(f"❌ Error al manejar carpeta padre: {error}")
            return None
    
    def _find_or_create_year_folder(self, year_folder_name, parent_id):
        """
        Busca o crea la carpeta del año dentro de la carpeta padre
        
        Args:
            year_folder_name (str): Nombre de la carpeta del año (ej: "2025")
            parent_id (str): ID de la carpeta padre
            
        Returns:
            str: ID de la carpeta del año
        """
        try:
            # Busca la carpeta del año dentro de la carpeta padre
            results = self.drive_service.files().list(
                q=f"name='{year_folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false",
                fields="files(id, name)",
                spaces='drive'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                year_folder_id = folders[0]['id']
                print(f"📁 Usando carpeta de año existente: {year_folder_name} (ID: {year_folder_id})")
                return year_folder_id
            else:
                # Crea nueva carpeta del año dentro de la carpeta padre
                folder_metadata = {
                    'name': year_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                year_folder_id = folder.get('id')
                print(f"📁 Carpeta de año creada: {year_folder_name} (ID: {year_folder_id})")
                
                return year_folder_id
                
        except Exception as error:
            print(f"❌ Error al manejar carpeta del año: {error}")
            return None
    
    def _get_email_date(self, msg_detail):
        """
        Obtiene la fecha de recepción del correo
        
        Args:
            msg_detail: Detalles del mensaje de Gmail
            
        Returns:
            datetime: Fecha de recepción del correo
        """
        try:
            # Obtiene el timestamp interno del correo (en milisegundos)
            internal_date = int(msg_detail.get('internalDate', 0))
            
            # Convierte de milisegundos a fecha
            email_date = datetime.fromtimestamp(internal_date / 1000)
            
            print(f"📅 Fecha del correo: {email_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return email_date
            
        except Exception as error:
            print(f"❌ Error al obtener fecha del correo: {error}")
            # Si hay error, usa la fecha actual como fallback
            return datetime.now()

    def _generate_month_filename(self, email_date, original_filename, zipname):
        """
        Genera el nombre del archivo basado en el mes anterior al de recepción del correo
        
        Args:
            email_date (datetime): Fecha de recepción del correo
            original_filename (str): Nombre original del archivo
            
        Returns:
            str: Nombre del archivo en formato "MM NOMBRE_MES"
        """
        try:
            # Nombres de los meses en español
            month_names = {
                1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
                5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 
                9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
            }
            
            # Calcula el mes anterior
            year = email_date.year - 1 if email_date.month == 1 else email_date.year
            current_day = email_date.day
            current_month = email_date.month
            previous_month = current_month - 1 if current_month > 1 else 12

            # Obtiene el nombre del mes anterior
            month_name = month_names[previous_month]
            
            # Obtiene la extensión del archivo original
            file_extension = ""
            if '.' in original_filename:
                file_extension = '.' + original_filename.split('.')[-1]
            
            # Genera el nombre final
            if current_day < 14:
                final_filename = f"{previous_month:02d} {month_name} {year}{file_extension}"
            else:
                final_filename = f"{current_month:02d} extra {month_names[current_month]} {year}{file_extension}"

            # Cuando es el Certificado Ingresos y Retenciones
            if zipname[0] == 'Z':
                final_filename = f"Certificado_Ingresos_y_Retenciones_ejercicio_{year-1}{file_extension}"

            print(f"📝 Nombre del archivo: {final_filename} (mes anterior a {email_date.strftime('%B %Y')})")
            
            return final_filename
            
        except Exception as error:
            print(f"❌ Error al generar nombre del archivo: {error}")
            # Si hay error, usa un nombre con timestamp como fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{timestamp}_{original_filename}"

    def process_emails(self, sender_email='rrhh@empresa.com', zip_password=None):
        """
        Procesa todos los correos del remitente, extrae los ZIP y sube los archivos a Drive
        
        Args:
            sender_email (str): Email del remitente
            zip_password (str): Contraseña de los archivos ZIP
        """
        try:
            print(f"🚀 Iniciando procesamiento de correos de {sender_email}")
            
            # Autentica servicios
            self.authenticate()
            
            # Busca correos
            messages = self.get_emails_from_sender(sender_email, config.DAYS_TO_SEARCH)
            
            if not messages:
                print("📭 No se encontraron correos para procesar")
                return
            
            processed_count = 0
            
            for message in messages:
                message_id = message['id']
                
                # Obtiene los detalles del mensaje
                msg_detail = self.gmail_service.users().messages().get(
                    userId='me', id=message_id).execute()
                
                # Busca archivos adjuntos ZIP
                payload = msg_detail['payload']
                parts = payload.get('parts', [])
                
                # Si no hay partes, el mensaje podría ser simple
                if not parts:
                    parts = [payload]
                
                for part in parts:
                    if part.get('filename', '').lower().endswith('.zip'):
                        attachment_id = part['body'].get('attachmentId')
                        
                        if attachment_id:
                            zipname = part['filename']
                            print(f"📎 Procesando archivo: {zipname}")
                            
                            # Descarga el ZIP
                            zip_data = self.download_attachment(message_id, attachment_id)
                            
                            if zip_data:
                                # Extrae el contenido
                                extracted_files = self.extract_zip_content(zip_data, zip_password)
                                
                                # Sube cada archivo extraído a Drive
                                for filename, content in extracted_files.items():
                                    # Obtiene la fecha del correo para nombrar el archivo
                                    email_date = self._get_email_date(msg_detail)
                                    
                                    # Calcula el mes anterior y genera el nombre del archivo
                                    file_name = self._generate_month_filename(email_date, filename, zipname)
                                    
                                    # Sube el archivo a la estructura NOMINAS/2025/
                                    self.upload_to_drive(
                                        file_name, 
                                        content,
                                        folder_name=config.DRIVE_FOLDER_NAME
                                    )
                                    processed_count += 1
            
            print(f"✅ Procesamiento completado. {processed_count} archivos procesados.")
            
        except Exception as error:
            print(f"❌ Error durante el procesamiento: {error}")


if __name__ == "__main__":
    
    # Crea el procesador
    processor = GmailProcessor(
        credentials_file=config.CREDENTIALS_FILE,
        token_file=config.TOKEN_FILE
    )
    
    # Procesa los correos
    processor.process_emails(
        sender_email=config.SENDER_EMAIL,
        zip_password=config.ZIP_PASSWORD if config.ZIP_PASSWORD else None
    )
