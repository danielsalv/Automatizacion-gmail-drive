"""
Script principal para ejecutar el procesador de nóminas
"""

import sys
import os
from gmail_processor import GmailProcessor
import config


def main():
    """Función principal"""
    try:
        print("=" * 50)
        print("🏢 PROCESADOR AUTOMÁTICO DE NÓMINAS")
        print("=" * 50)
        print(f"📧 Buscando correos de: {config.SENDER_EMAIL}")
        print(f"📅 Período de búsqueda: últimos {config.DAYS_TO_SEARCH} días")
        print(f"📁 Carpeta de destino en Drive: {config.DRIVE_FOLDER_NAME}")
        print("-" * 50)
        
        # Verifica que exista el archivo de credenciales
        if not os.path.exists(config.CREDENTIALS_FILE):
            print(f"❌ Error: No se encontró el archivo {config.CREDENTIALS_FILE}")
            print("   Asegúrate de que el archivo de credenciales OAuth 2.0 esté en la carpeta del proyecto.")
            return 1
        
        # Verifica que se haya configurado la contraseña del ZIP
        if not config.ZIP_PASSWORD:
            print("⚠️  Advertencia: No se ha configurado contraseña para los archivos ZIP")
            response = input("¿Deseas continuar sin contraseña? (s/N): ").lower()
            if response not in ['s', 'si', 'sí', 'y', 'yes']:
                print("💡 Configura la contraseña en config.py y vuelve a ejecutar")
                return 1
        
        # Crea y ejecuta el procesador
        processor = GmailProcessor(
            credentials_file=config.CREDENTIALS_FILE,
            token_file=config.TOKEN_FILE
        )
        
        processor.process_emails(
            sender_email=config.SENDER_EMAIL,
            zip_password=config.ZIP_PASSWORD if config.ZIP_PASSWORD else None
        )
        
        print("-" * 50)
        print("✅ ¡Procesamiento completado exitosamente!")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
