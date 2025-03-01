# Despliegue


### 1. Configuración Inicial AWS
```bash
# Instalar y configurar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws configure
```

### 2. Crear Recursos en AWS
**a. RDS PostgreSQL (Base de datos):**
```bash
aws rds create-db-instance \
    --db-instance-identifier dbproyecto \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --allocated-storage 20 \
    --master-username postgres \
    --master-user-password R00tAnd3s-Rds+ \
    --publicly-accessible \
    --backup-retention-period 0 \
    --no-multi-az \
    --region us-east-1
```

**b. SQS (Cola de mensajes):**
```bash
aws sqs create-queue \
    --queue-name supply_service_queue \
    --region us-east-1
```

**c. ECR (Repositorio de Docker):**
```bash
aws ecr create-repository \
    --repository-name inventory-calculation \
    --region us-east-1
```

### 3. Configurar Docker y Desplegar en ECS
**a. Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

**b. Construir y subir imagen:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [tu-id-cuenta].dkr.ecr.us-east-1.amazonaws.com

docker build -t inventory-calculation .
docker tag inventory-calculation:latest [tu-id-cuenta].dkr.ecr.us-east-1.amazonaws.com/inventory-calculation:latest
docker push [tu-id-cuenta].dkr.ecr.us-east-1.amazonaws.com/inventory-calculation:latest
```

**c. Task Definition ECS (ecs-task-definition.json):**
```json
{
    "family": "inventory-task",
    "networkMode": "awsvpc",
    "containerDefinitions": [
        {
            "name": "inventory-container",
            "image": "[tu-id-cuenta].dkr.ecr.us-east-1.amazonaws.com/inventory-calculation:latest",
            "portMappings": [{"containerPort": 80, "hostPort": 80}],
            "environment": [
                {"name": "DATABASE_URL", "value": "postgresql://postgres:postgres@[rds-endpoint]:5432/dbproyecto"},
                {"name": "QUEUE_SERVICE", "value": "sqs"},
                {"name": "SQS_URL", "value": "https://sqs.us-east-1.amazonaws.com/[tu-id-cuenta]/supply_service_queue"}
            ]
        }
    ],
    "cpu": "256",
    "memory": "512",
    "requiresCompatibilities": ["FARGATE"],
    "executionRoleArn": "arn:aws:iam::[tu-id-cuenta]:role/ecsTaskExecutionRole"
}
```

**d. Registrar Task Definition:**
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

**e. Crear Cluster y Servicio:**
```bash
aws ecs create-cluster --cluster-name inventory-cluster

aws ecs create-service \
    --cluster inventory-cluster \
    --service-name inventory-service \
    --task-definition inventory-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-abc],securityGroups=[sg-xyz]}"
```

### 4. Configuración Autoescalado
```bash
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/inventory-cluster/inventory-service \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 1 \
    --max-capacity 3

aws application-autoscaling put-scaling-policy \
    --policy-name cpu-scaling-policy \
    --service-namespace ecs \
    --resource-id service/inventory-cluster/inventory-service \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        }
    }'
```

### 5. Pruebas de Performance
**a. Prueba de carga con Locust (locustfile.py):**
```python
from locust import HttpUser, task, between

class InventoryUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def enviar_carga(self):
        self.client.post("/enviar")
```

**b. Ejecutar prueba:**
```bash
locust -f locustfile.py --headless -u 100 -r 10 -H http://[ecs-endpoint]
```

**c. Monitorear métricas en AWS CloudWatch:**
- ECS: CPU/Memory Usage
- RDS: Read/Write Latency
- SQS: ApproximateNumberOfMessagesVisible

### 6. Limpieza (Post Pruebas)
```bash
aws ecs update-service --cluster inventory-cluster --service inventory-service --desired-count 0
aws ecs delete-service --cluster inventory-cluster --service inventory-service
aws ecs delete-cluster --cluster inventory-cluster
aws rds delete-db-instance --db-instance-identifier dbproyecto --skip-final-snapshot
aws sqs delete-queue --queue-url https://sqs.us-east-1.amazonaws.com/[tu-id-cuenta]/supply_service_queue
```

### Consideraciones Clave:
1. **Seguridad:**
   - Configurar Security Groups para permitir tráfico entre ECS y RDS
   - Usar IAM Roles para acceder a SQS

2. **Optimización:**
   - Habilitar Enhanced Monitoring en RDS
   - Usar Fargate Spot para reducir costos

3. **Métricas Clave:**
   ```bash
   # Obtener latencia promedio desde CloudWatch
   aws cloudwatch get-metric-statistics \
       --namespace AWS/ECS \
       --metric-name Latency \
       --dimensions Name=ServiceName,Value=inventory-service \
       --start-time 2023-01-01T00:00:00Z \
       --end-time 2023-01-01T23:59:59Z \
       --period 3600 \
       --statistics Average
   ```

Este setup cumple con los requisitos del experimento y utiliza completamente la capa gratuita de AWS. Los tiempos de despliegue aproximados son:
- RDS: 10-15 minutos
- ECS: 5-10 minutos
- SQS: Instantáneo