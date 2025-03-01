import pika
import time
import sys
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
QUEUE_DURABLE = True  # survive broker restart
QUEUE_ARGUMENTS = {
    'x-message-ttl': 1000 * 60 * 60 * 24,  # 24 hours TTL in milliseconds
    'x-max-length': 10000  # max number of messages
}

def setup_rabbitmq():
    """Create exchange, queue and bind them in RabbitMQ"""
    
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # Setup connection
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection_params = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600
            )
            
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            
            # Create exchange
            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type='direct',
                durable=True
            )
            logger.info(f"Exchange '{EXCHANGE_NAME}' created or confirmed")
            
            # Create queue
            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=QUEUE_DURABLE,
                arguments=QUEUE_ARGUMENTS
            )
            logger.info(f"Queue '{QUEUE_NAME}' created or confirmed")
            
            # Bind queue to exchange
            channel.queue_bind(
                queue=QUEUE_NAME,
                exchange=EXCHANGE_NAME,
                routing_key=ROUTING_KEY
            )
            logger.info(f"Queue '{QUEUE_NAME}' bound to exchange '{EXCHANGE_NAME}' with routing key '{ROUTING_KEY}'")
            
            # Create a dead letter queue for failed messages
            channel.exchange_declare(
                exchange=f"{EXCHANGE_NAME}.dead-letter",
                exchange_type='direct',
                durable=True
            )
            
            channel.queue_declare(
                queue=f"{QUEUE_NAME}.dead-letter",
                durable=True
            )
            
            channel.queue_bind(
                queue=f"{QUEUE_NAME}.dead-letter",
                exchange=f"{EXCHANGE_NAME}.dead-letter",
                routing_key=f"{ROUTING_KEY}.dead-letter"
            )
            logger.info(f"Dead letter queue configured for '{QUEUE_NAME}'")
            
            connection.close()
            logger.info("RabbitMQ setup completed successfully")
            return True
            
        except pika.exceptions.AMQPConnectionError as e:
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logger.warning(f"Failed to connect to RabbitMQ (attempt {retry_count}/{MAX_RETRIES}). Retrying in {RETRY_INTERVAL} seconds...")
                time.sleep(RETRY_INTERVAL)
            else:
                logger.error(f"Failed to connect to RabbitMQ after {MAX_RETRIES} attempts: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up RabbitMQ: {e}")
            return False

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
    
    if setup_rabbitmq():
        logger.info("Queue setup successful")
        
        # Send test message if "--test" is provided as argument
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            if send_test_message():
                logger.info("Test message sent successfully")
            else:
                logger.error("Failed to send test message")
    else:
        logger.error("Failed to set up RabbitMQ queues")
        sys.exit(1)