"""Tool para subir archivos a Google Cloud Storage."""
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
    """Sube un archivo PDF a GCS y retorna una URL firmada."""
    try:
        import google.auth
        from google.auth.transport import requests as google_requests
        from google.auth import impersonated_credentials
        
        if not os.path.exists(local_file_path):
            return {
                "ok": False,
                "error": f"El archivo no existe: {local_file_path}"
            }
        
        if not local_file_path.lower().endswith('.pdf'):
            return {
                "ok": False,
                "error": "El archivo debe ser un PDF"
            }
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        filename = os.path.basename(local_file_path)
        
        blob_name = f"{destination_folder}/{filename}"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_filename(local_file_path, content_type='application/pdf')
        logger.info(f"Archivo subido: gs://{bucket_name}/{blob_name}")
        
        try:
            credentials, project = google.auth.default()
            auth_request = google_requests.Request()
            
            if hasattr(credentials, 'refresh'):
                credentials.refresh(auth_request)
            
            service_account_email = None
            
            if hasattr(credentials, 'service_account_email'):
                service_account_email = credentials.service_account_email
            elif hasattr(credentials, '_service_account_email'):
                service_account_email = credentials._service_account_email
            else:
                try:
                    import requests
                    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
                    response = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=2)
                    if response.status_code == 200:
                        service_account_email = response.text
                except Exception:
                    pass
            if not service_account_email:
                service_account_email = f"{project}@appspot.gserviceaccount.com"
            
            logger.info(f"Usando service account: {service_account_email}")
            
            signing_credentials = impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=service_account_email,
                target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
            )
            
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET",
                credentials=signing_credentials,
            )
            
            logger.info(f"URL firmada generada correctamente")
            
            return {
                "ok": True,
                "signed_url": signed_url,
                "gcs_uri": f"gs://{bucket_name}/{blob_name}",
                "expires_in": "7 days",
                "filename": filename
            }
        except Exception as sign_error:
            logger.error(f"Error al firmar URL: {sign_error}")
            
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


upload_pdf_to_storage_tool = FunctionTool(upload_pdf_to_storage)

