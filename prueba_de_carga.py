import time
import json
import logging
import statistics
from datetime import datetime
from locust import HttpUser, task, between, events, constant_pacing
from typing import Dict, List

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'prueba_carga_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
logger = logging.getLogger("load_test")

# Almacenamiento de métricas detalladas
class MetricsCollector:
    def __init__(self):
        self.sqs_publish_times: List[float] = []
        self.db_write_times: List[float] = []
        self.total_response_times: List[float] = []
        self.processing_times: Dict[int, float] = {}  # ID de mensaje -> tiempo cuando fue publicado
        self.message_processing_times: List[float] = []  # Tiempo entre publicación y procesamiento

metrics = MetricsCollector()

# Listeners para eventos de Locust (versión 2.x)
@events.request.add_listener
def request_handler(request_type, name, response_time, response, context, exception, **kwargs):
    if exception:
        # Si hay una excepción, no procesar
        logger.error(f"Error en solicitud {name}: {exception}")
        return
        
    # Procesar solo solicitudes exitosas
    if name == "/enviar" and request_type == "POST":
        metrics.total_response_times.append(response_time)
        try:
            data = response.json()
            if 'registro' in data and 'metricas' in data:
                # Extraer métricas detalladas
                msg_id = data['registro']['id']
                metrics.processing_times[msg_id] = time.time()
                
                if 'tiempo_db_ms' in data['metricas']:
                    metrics.db_write_times.append(data['metricas']['tiempo_db_ms'])
                
                if 'tiempo_sqs_ms' in data['metricas']:
                    metrics.sqs_publish_times.append(data['metricas']['tiempo_sqs_ms'])
                
                logger.info(f"Mensaje {msg_id} enviado - Tiempo respuesta: {response_time}ms")
        except Exception as e:
            logger.error(f"Error procesando respuesta: {str(e)}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Iniciando prueba de carga")
    print("Iniciando prueba de carga para el servicio de inventario")
    print("========================================================")
    print("Métricas que se evaluarán:")
    print("1. Tiempo de respuesta del endpoint /enviar")
    print("2. Tiempo de escritura en base de datos")
    print("3. Tiempo de publicación en SQS")
    print("4. Procesamiento asíncrono de mensajes")
    print("5. Comportamiento bajo diferentes niveles de carga")
    print("========================================================")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Prueba de carga finalizada")
    
    # Generar estadísticas
    if metrics.total_response_times:
        total_response_avg = sum(metrics.total_response_times) / len(metrics.total_response_times)
        total_response_p95 = sorted(metrics.total_response_times)[int(len(metrics.total_response_times) * 0.95)]
        
        db_write_avg = sum(metrics.db_write_times) / len(metrics.db_write_times) if metrics.db_write_times else 0
        sqs_publish_avg = sum(metrics.sqs_publish_times) / len(metrics.sqs_publish_times) if metrics.sqs_publish_times else 0
        
        processing_avg = sum(metrics.message_processing_times) / len(metrics.message_processing_times) if metrics.message_processing_times else 0
        
        # Guardar resultados en archivo para análisis posterior
        with open(f'resultados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump({
                "total_response_avg_ms": total_response_avg,
                "total_response_p95_ms": total_response_p95,
                "db_write_avg_ms": db_write_avg,
                "sqs_publish_avg_ms": sqs_publish_avg,
                "processing_avg_s": processing_avg,
                "messages_published": len(metrics.processing_times),
                "messages_processed": len(metrics.message_processing_times)
            }, f, indent=2)
        
        # Mostrar resumen
        print("\n========================================================")
        print("RESUMEN DE LA PRUEBA DE CARGA")
        print("========================================================")
        print(f"Tiempo promedio de respuesta: {total_response_avg:.2f} ms")
        print(f"Percentil 95 de tiempo de respuesta: {total_response_p95:.2f} ms")
        print(f"Tiempo promedio de escritura en DB: {db_write_avg:.2f} ms")
        print(f"Tiempo promedio de publicación en SQS: {sqs_publish_avg:.2f} ms")
        print(f"Tiempo promedio de procesamiento asíncrono: {processing_avg:.2f} s")
        print(f"Mensajes publicados: {len(metrics.processing_times)}")
        print(f"Mensajes procesados y confirmados: {len(metrics.message_processing_times)}")
        print("========================================================")
        
        logger.info(f"Tiempo promedio de respuesta: {total_response_avg:.2f} ms")
        logger.info(f"Percentil 95 de tiempo de respuesta: {total_response_p95:.2f} ms")

# Usuarios para escenarios de prueba
class BaseLoadUser(HttpUser):
    """Usuario para prueba de carga base (10 RPS)"""
    wait_time = between(1, 2)
    
    @task(3)
    def post_inventory(self):
        response = self.client.post("/enviar")
        self.process_response(response)
            
    @task(1)
    def get_registros(self):
        response = self.client.get("/registros")
        if response.status_code == 200:
            data = response.json()
            # Verificar mensajes procesados
            for registro in data.get('registros', []):
                if registro['id'] in metrics.processing_times and registro['estado'] == "PROCESADO":
                    # Calcular tiempo de procesamiento end-to-end
                    message_id = registro['id']
                    publish_time = metrics.processing_times.pop(message_id)
                    process_time = time.time() - publish_time
                    metrics.message_processing_times.append(process_time)
                    logger.info(f"Mensaje {message_id} procesado en {process_time:.2f}s")
    
    @task(1)
    def check_health(self):
        self.client.get("/")
        
    def process_response(self, response):
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Mensaje enviado. ID: {data['registro']['id']}")
            except:
                pass
        else:
            print(f"Error: {response.status_code} - {response.text}")

class MediumLoadUser(HttpUser):
    """Usuario para prueba de carga media (50 RPS)"""
    wait_time = between(0.2, 0.5)
    
    @task
    def post_inventory(self):
        response = self.client.post("/enviar")
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Mensaje enviado (carga media). ID: {data['registro']['id']}")
            except:
                pass
        else:
            logger.error(f"Error en carga media: {response.status_code}")

class HighLoadUser(HttpUser):
    """Usuario para prueba de carga alta (100+ RPS)"""
    wait_time = constant_pacing(0.05)  # 20 RPS por usuario
    
    @task
    def post_inventory_burst(self):
        for _ in range(5):  # Enviar 5 mensajes en ráfaga
            response = self.client.post("/enviar")
            if response.status_code != 200:
                logger.error(f"Error en carga alta: {response.status_code}")

# Este script debe ejecutarse con diferentes perfiles:
# 1. Carga Base:
#    locust -f prueba_de_carga.py --host=http://publisher-load-balancer-2073021256.us-east-1.elb.amazonaws.com -u 10 -r 1 -t 2m --only-summary --headless --class-picker BaseLoadUser
# 2. Carga Media:
#    locust -f prueba_de_carga.py --host=http://publisher-load-balancer-2073021256.us-east-1.elb.amazonaws.com -u 50 -r 5 -t 5m --only-summary --headless --class-picker MediumLoadUser
# 3. Carga Alta:
#    locust -f prueba_de_carga.py --host=http://publisher-load-balancer-2073021256.us-east-1.elb.amazonaws.com -u 100 -r 10 -t 10m --only-summary --headless --class-picker HighLoadUser