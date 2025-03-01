import json
import time
from app import db
from app.config import settings
from app.utils import get_fecha_actual
from fastapi import Depends
from app.db import SessionLocal, get_db
from sqlalchemy.orm import Session
from app.models import RegistroCarga

def activar_consumer():
    if settings.QUEUE_SERVICE.lower() == "sqs":
        return activar_consumer_sqs()
    elif settings.QUEUE_SERVICE.lower() == "rabbitmq":
        return activar_consumer_rabbitmq()
    else:
        raise ValueError("Servicio de cola no soportado.")
    
def activar_consumer_sqs():
    import boto3
    import json
    cliente = boto3.client('sqs', region_name=settings.AWS_REGION)
    while True:
        response = cliente.receive_message(
            QueueUrl=settings.SQS_URL,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )
        if 'Messages' in response:
            for message in response['Messages']:
                mensaje = message['Body']
                # Procesar el mensaje
                print(f"Mensaje recibido: {mensaje}")
                
                # Procesar el mensaje
                time.sleep(5)
                print(f"Mensaje procesado: {mensaje}")

                # Eliminar el mensaje de la cola
                cliente.delete_message(
                    QueueUrl=settings.SQS_URL,
                    ReceiptHandle=message['ReceiptHandle']
                )
        else:
            print("No hay mensajes en la cola")
            break

def activar_consumer_rabbitmq():
    import pika
    try:
        parametros = pika.URLParameters(settings.RABBITMQ_URL)
        conexion = pika.BlockingConnection(parametros)
        canal = conexion.channel()
        arguments = {
            'x-message-ttl': 1000 * 60 * 60 * 24,  # 24 hours TTL in milliseconds
            'x-max-length': 10000  # max number of messages
        }
        # Declarar la cola (ej.: "supply_service_queue")
        canal.queue_declare(queue="supply_service_queue", durable=True, arguments=arguments)
        def callback(ch, method, properties, body):
            print(f"Mensaje recibido: {body}")
            byte_to_dict = json.loads(body)
            # Procesar el mensaje
            time.sleep(5)
            print(f"Mensaje procesado: {byte_to_dict}")
            
            # Guardar registro en la base de datos
            estado = "PROCESADO"
            db_session = SessionLocal()  # Crear una nueva sesión
            try:
                db_session.query(RegistroCarga).filter(RegistroCarga.id == byte_to_dict['id']).update(
                    {"estado": estado, "fecha_de_consumo": get_fecha_actual()}
                )
                db_session.commit()  # Confirmar los cambios
                print(f"Registro actualizado: {byte_to_dict['id']}")
            except Exception as e:
                db_session.rollback()  # Revertir en caso de error
                print(f"Error al actualizar el registro: {e}")
                raise
            finally:
                db_session.close()  # Cerrar la sesión

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("Mensaje procesado y confirmado")

        canal.basic_consume(queue="supply_service_queue", on_message_callback=callback)
        print('Esperando mensajes...')
        canal.start_consuming()

    except Exception as e:
        print(f"Error: {e}")
        canal.stop_consuming()
        conexion.close()
        raise e
    