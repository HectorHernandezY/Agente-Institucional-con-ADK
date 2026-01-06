"""
upload_to_storage.py — Tool para subir archivos a Google Cloud Storage

Esta tool es responsable de:
- Subir archivos PDF a Google Cloud Storage
- Generar URLs firmadas para acceso temporal
"""
import os
from datetime import timedelta
from google.adk.tools import FunctionTool
from google.cloud import storage
import logging

logger = logging.getLogger(__name__)


def upload_pdf_to_storage(
    local_file_path: str,
    bucket_name: str = "db_agent_utem",
    destination_folder: str = "reportes_utem_pdf"
) -> dict:
    """
    Sube un archivo PDF a Google Cloud Storage y retorna una URL firmada.
    
    Args:
        local_file_path: Ruta local del archivo PDF a subir.
        bucket_name: Nombre del bucket de GCS (default: db_agent_utem).
        destination_folder: Carpeta dentro del bucket (default: reportes_utem_pdf).
        
    Returns:
        dict: Diccionario con el resultado de la operación:
            - ok: bool indicando si fue exitoso
            - signed_url: URL firmada del archivo (si ok=True)
            - gcs_uri: URI del archivo en GCS (si ok=True)
            - error: Mensaje de error (si ok=False)
    """
    try:
        import google.auth
        from google.auth.transport import requests as google_requests
        from google.auth import impersonated_credentials
        
        # Verificar que el archivo existe
        if not os.path.exists(local_file_path):
            return {
                "ok": False,
                "error": f"El archivo no existe: {local_file_path}"
            }
        
        # Verificar que es un PDF
        if not local_file_path.lower().endswith('.pdf'):
            return {
                "ok": False,
                "error": "El archivo debe ser un PDF"
            }
        
        # Inicializar cliente de Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Obtener el nombre del archivo
        filename = os.path.basename(local_file_path)
        
        # Crear el path completo en el bucket (carpeta/nombre_archivo)
        blob_name = f"{destination_folder}/{filename}"
        blob = bucket.blob(blob_name)
        
        # Subir el archivo con content-type apropiado
        blob.upload_from_filename(local_file_path, content_type='application/pdf')
        logger.info(f"✓ Archivo subido: gs://{bucket_name}/{blob_name}")
        
        # =====================================================================
        # GENERAR URL FIRMADA USANDO IAM SIGNBLOB (funciona en Cloud Run)
        # =====================================================================
        try:
            # Obtener credenciales del entorno
            credentials, project = google.auth.default()
            auth_request = google_requests.Request()
            
            # Refrescar credenciales si es necesario
            if hasattr(credentials, 'refresh'):
                credentials.refresh(auth_request)
            
            # Obtener el service account email
            # En Cloud Run, esto es el email del service account del servicio
            service_account_email = None
            
            if hasattr(credentials, 'service_account_email'):
                service_account_email = credentials.service_account_email
            elif hasattr(credentials, '_service_account_email'):
                service_account_email = credentials._service_account_email
            else:
                # Intentar obtener de metadata server (Cloud Run)
                try:
                    import requests
                    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
                    response = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=2)
                    if response.status_code == 200:
                        service_account_email = response.text
                except Exception:
                    pass
            
            if not service_account_email:
                # Fallback: usar project default service account
                service_account_email = f"{project}@appspot.gserviceaccount.com"
            
            logger.info(f"Usando service account: {service_account_email}")
            
            # Crear credenciales de firma usando impersonación (funciona en Cloud Run)
            signing_credentials = impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=service_account_email,
                target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
            )
            
            # Generar URL firmada (7 días de expiración)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET",
                credentials=signing_credentials,
            )
            
            logger.info(f"✓ URL firmada generada correctamente")
            
            return {
                "ok": True,
                "signed_url": signed_url,
                "gcs_uri": f"gs://{bucket_name}/{blob_name}",
                "expires_in": "7 days",
                "filename": filename
            }
            
        except Exception as sign_error:
            # Si falla la firma, retornar ERROR, no URL pública
            logger.error(f"Error al firmar URL: {sign_error}")
            
            # Intentar método alternativo: hacer el blob público temporalmente
            try:
                blob.make_public()
                public_url = blob.public_url
                logger.warning(f"Usando URL pública como fallback: {public_url}")
                
                return {
                    "ok": True,
                    "signed_url": public_url,
                    "gcs_uri": f"gs://{bucket_name}/{blob_name}",
                    "filename": filename,
                    "warning": "URL pública (sin expiración). Considera configurar IAM para URLs firmadas."
                }
            except Exception as public_error:
                return {
                    "ok": False,
                    "error": f"No se pudo generar URL de acceso. Error de firma: {str(sign_error)}. Error público: {str(public_error)}",
                    "gcs_uri": f"gs://{bucket_name}/{blob_name}",
                    "filename": filename
                }
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        return {
            "ok": False,
            "error": f"Error al subir archivo a Cloud Storage: {str(e)}"
        }


# Exportar como FunctionTool
upload_pdf_to_storage_tool = FunctionTool(upload_pdf_to_storage)

