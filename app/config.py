from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", validate_default=False, env_file='.env')

    DATABASE_URL: str = "postgresql://postgres:R00tAnd3s-Rds+@localhost:5440/dbproyecto" #"sqlite:///./test.db"
    QUEUE_SERVICE: str = "rabbitmq" #'sqs' o 'rabbitmq'.
    AWS_REGION: str = "us-east-1"
    SQS_URL: str = "https://sqs.us-east-1.amazonaws.com/tu_id_cuenta/tu_nombre_de_cola"
    RABBITMQ_URL: str = "amqp://user:password@localhost:5672/"

settings = Settings()
