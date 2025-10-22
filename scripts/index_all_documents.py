"""
Script para indexar documentos UNO POR UNO (streaming mode)
Minimiza uso de RAM procesando y liberando memoria inmediatamente
"""
import os
import sys
import gc
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import storage
from google.auth import default

# Configuración
PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "muruna-utem-project")
GCS_BUCKET = os.getenv("GCS_RAG_BUCKET", "db_agent_utem")


def get_file_iterator(folder_path: str = "files_utem/"):
    """
    Generador que retorna archivos UNO a la vez (no carga la lista completa)
    """
    credentials, _ = default(quota_project_id=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID, credentials=credentials)
    
    bucket = storage_client.bucket(GCS_BUCKET)
    
    # Usar iterator en lugar de list() - NO carga todo en memoria
    for blob in bucket.list_blobs(prefix=folder_path):
        if not blob.name.endswith('/'):  # Ignorar carpetas
            yield blob.name


def count_files(folder_path: str = "files_utem/") -> int:
    """Cuenta archivos sin cargarlos en memoria"""
    count = 0
    for _ in get_file_iterator(folder_path):
        count += 1
    return count


def main():
    print("Iniciando indexación de documentos (modo streaming)")
    print("=" * 70)
    
    # Contar archivos primero
    print("\n🔍 Contando archivos en GCS...")
    try:
        total_files = count_files(folder_path="files_utem/")
    except Exception as e:
        print(f"❌ Error al acceder a GCS: {e}")
        return
    
    if total_files == 0:
        print("⚠️  No se encontraron archivos para indexar")
        return
    
    print(f"📁 Se procesarán {total_files} archivos\n")
    
    # Importar la función SOLO cuando se necesite
    from my_agent_utem.tools.index_documents import index_document_from_gcs
    
    # Contadores
    success_count = 0
    error_count = 0
    errors_list = []
    success_list = []
    
    # Procesar archivo por archivo usando el generador
    for idx, file_path in enumerate(get_file_iterator("files_utem/"), 1):
        print("=" * 70)
        print(f"[{idx}/{total_files}] Procesando: {file_path}")
        print("-" * 70)
        
        try:
            # Indexar documento (esto hace las llamadas a GCP)
            result = index_document_from_gcs(file_path)
            
            if result["ok"]:
                success_count += 1
                chunks = result.get('chunks_created', 0)
                print(f"✅ Éxito - {chunks} chunks creados")
                success_list.append((file_path, chunks))
            else:
                error_count += 1
                error_msg = result.get('message', 'Unknown error')
                print(f"❌ Error: {error_msg}")
                errors_list.append((file_path, error_msg))
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Indexación interrumpida por el usuario")
            break
            
        except Exception as e:
            error_count += 1
            error_msg = str(e)
            print(f"❌ Excepción: {error_msg}")
            errors_list.append((file_path, error_msg))
        
        # CRÍTICO: Forzar liberación de memoria
        gc.collect()
        
        # Pausa para evitar rate limiting de APIs
        if idx < total_files:
            time.sleep(0.5)
        
        print()
    
    # Resumen final
    print("=" * 70)
    print("📊 RESUMEN FINAL")
    print("=" * 70)
    processed = success_count + error_count
    print(f"Total archivos procesados: {processed}/{total_files}")
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Errores: {error_count}")
    
    if processed > 0:
        print(f"📈 Tasa de éxito: {(success_count/processed*100):.1f}%")
    
    # Detalles de errores
    if errors_list:
        print(f"\n❌ ARCHIVOS CON ERRORES ({len(errors_list)}):")
        print("-" * 70)
        for file_path, error_msg in errors_list:
            print(f"  • {os.path.basename(file_path)}")
            print(f"    → {error_msg[:100]}...")
    
    # Detalles de éxitos
    if success_list:
        print(f"\n✅ ARCHIVOS INDEXADOS ({len(success_list)}):")
        print("-" * 70)
        total_chunks = 0
        for file_path, chunks in success_list:
            print(f"  • {os.path.basename(file_path)} ({chunks} chunks)")
            total_chunks += chunks
        print(f"\n  📦 Total de chunks creados: {total_chunks}")
    
    print("\n" + "=" * 70)
    print("🎉 Indexación completada")
    print("=" * 70)


if __name__ == "__main__":
    main()