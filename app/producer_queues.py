from app.config import settings

def enviar_mensaje_cola(mensaje: str):
    if settings.QUEUE_SERVICE.lower() == "sqs":
        return enviar_mensaje_sqs(mensaje)
    elif settings.QUEUE_SERVICE.lower() == "rabbitmq":
        return enviar_mensaje_rabbitmq(mensaje)
    else:
        raise ValueError("Servicio de cola no soportado.")

def enviar_mensaje_sqs(mensaje: str):
    import boto3
    cliente = boto3.client('sqs', region_name=settings.AWS_REGION)
    respuesta = cliente.send_message(
        QueueUrl=settings.SQS_URL,
        MessageBody=mensaje
    )
    return respuesta

def enviar_mensaje_rabbitmq(mensaje: str):
    import pika
    parametros = pika.URLParameters(settings.RABBITMQ_URL)
    conexion = pika.BlockingConnection(parametros)
    canal = conexion.channel()
    arguments = {
        'x-message-ttl': 1000 * 60 * 60 * 24,  # 24 hours TTL in milliseconds
        'x-max-length': 10000  # max number of messages
    }
    # Declarar la cola (ej.: "supply_service_queue")
    canal.queue_declare(queue="supply_service_queue", durable=True, arguments=arguments)
    canal.basic_publish(
        exchange='supply_service_exchange',
        routing_key="supply.request",
        body=mensaje,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Hace el mensaje persistente
        )
    )
    conexion.close()
    return {"mensaje": "Mensaje enviado a RabbitMQ"}
