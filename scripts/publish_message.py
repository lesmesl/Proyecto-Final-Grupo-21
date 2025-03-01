import pika
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RabbitMQ connection parameters (from docker-compose.yml)
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'user'
RABBITMQ_PASS = 'password'
RETRY_INTERVAL = 5  # seconds between retry attempts
MAX_RETRIES = 10

# Queue configuration
QUEUE_NAME = 'supply_service_queue'
EXCHANGE_NAME = 'supply_service_exchange'
ROUTING_KEY = 'supply.request'


def send_test_message():
    """Send a test message to verify the queue setup"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection_params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        message = "Test message from supply service setup script"
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='text/plain'
            )
        )
        
        logger.info(f"Test message sent to queue '{QUEUE_NAME}'")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Failed to send test message: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting RabbitMQ setup script...")
    

    if send_test_message():
        logger.info("Test message sent successfully")
    else:
        logger.error("Failed to send test message")