## 1. Creación de usuario

1. Dirigirse al IAM --> Crear usuario
   ![[Pasted image 20250301004907.png]]
   ![[screencapture-us-east-1-console-aws-amazon-iam-home-2024-11-27-23_29_52.png]]
   1. Seleccionamos adjuntar politícas directamente y buscamos el acceso de adminsitrador que permite acceso completo a los servicios y recursos de AWS. https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AdministratorAccess.html ![[Pasted image 20241127232702.png]] y NEXT
   2.  Así quedaría y hacemos clic en crear usuario: ![[Pasted image 20241127233037.png]]
   3. Se generan las credenciales: ![[Pasted image 20241127233129.png]]
   4.  Luego entramos al usuario y creamos clave de acceso para poder ingresar por CLI qué allí si dejara poner los accesos ![[Pasted image 20241127234301.png]] ![[Pasted image 20241127234313.png]] ![[Pasted image 20241127234324.png]] 

   5.  Ahora dentro de vscode para poder gestionar las credenciales usamos:  aws configure --profile andes_root_account
    ![[Pasted image 20241127234943.png]] ![[Pasted image 20241127235010.png]]
    ![[Pasted image 20241127235055.png]]

## 2. Creando RDS

Creamos nuestra base de datos desde el servicio RDS de AWS, para nuestro proyecto usaremos postgresql.
![[Pasted image 20241020205145.png]]

![[Pasted image 20241020170623.png]]

Definimos las credenciales de la instancia.
![[Pasted image 20241020174115.png]]
Nos aseguramos de usar la capa free tier:
![[Pasted image 20241020205704.png]]

Configuramos la IP publica para la conexión de RDS desde internet.
![[Pasted image 20241020174348.png]]

Nos aseguramos que la base de datos mantenga el puerto 5432 y Database authentication.
![[Pasted image 20241020174523.png]]

Creamos la base de datos.
![[Pasted image 20241020174544.png]]

Una vez la instancia de base de datos se encuentre desplegada. Ingresamos a la base de datos al grupo de seguridad
![[Pasted image 20241020210647.png]]

Seleccionamos el grupo
![[Pasted image 20241020211352.png]]
![[Pasted image 20241020211503.png]]
Agregamos las reglas de entrada, para permitir todo el tráfico.
![[Pasted image 20241020212823.png]]
![[Pasted image 20241020212847.png]]
Por ultimo añadimos otro permiso para que la base de datos sea totalmente visible
![[Pasted image 20241020215615.png]]
Dando como resultado:
![[Pasted image 20241020215650.png]]


## 3. Creación de imagen y cargue a ECR

Se hará uso del servicio de ECR de Amazon.
![[Pasted image 20241117120252.png]]
Se crea el repositorio, con las configuraciones planteadas en la imagen, para este caso se nombra como `devops_08`
![[Pasted image 20241117120328.png]]
![[Pasted image 20241117121136.png]]

Una vez creado el repositorio copiamos la URI generada. ![[Pasted image 20241117121325.png]]
URI: `051826725299.dkr.ecr.us-east-1.amazonaws.com/publisher`

Ahora es necesario ingresar al repositorio para usar los comandos que permitirán subir la imagen desde el ambiente local hasta el repositorio.
![[Pasted image 20241117121805.png]]

Desde esta lista de comandos realizaremos el proceso para subir la imagen; se debe tener en cuenta el sistema operativo del ambiente local, para este caso se utilizará MacOs.

### Cargue de imagen.
![[Pasted image 20241117122020.png]]

Con el uso de estos comando realizamos el cargue de la imagen desde la terminal del ambiente local. 

Al correr el comando de login si el usuario ya cuenta con los permisos el login debe completarse.
![[Pasted image 20241117130034.png]]
Generamos la imagen docker con el siguiente comando.
![[Pasted image 20241117130530.png]]
![[Pasted image 20241117130411.png]]
Creamos el tag para la imagen creada.
![[Pasted image 20241117130548.png]]
![[Pasted image 20241117130613.png]]
Subimos la imagen al repositorio de AWS y se tendría en en el repositorio.
![[Pasted image 20241117130641.png]]
![[Pasted image 20241117130714.png]]
![[Pasted image 20241117132307.png]]
#### Error aws configuration
> Si se presenta el error `Unable to locate credentials` debe configurarse la cuenta aws en el cli.
> ![[Pasted image 20241117122333.png]]
> Por medio del servicio IAM creamos un nuevo usuario si aun no se lo tiene y una nueva acccess key ![[Pasted image 20241117123152.png]]
> ![[Pasted image 20241117123226.png]]
> ![[Pasted image 20241117123306.png]]
> Al nuevo usuario se le debe agregar los permisos requeridos, se sugiere crear un nuevo grupo con permisos de administrador. Para este caso un grupo ya se había creado anteriormente. Se crea el usuario en el último paso. ![[Pasted image 20241117123425.png]]
> Seleccionamos el usuario para crear la nueva Key de acceso. ![[Pasted image 20241117123638.png]]![[Pasted image 20241117123735.png]]
> La nueva Key debe configurarse para acceder desde CLI. ![[Pasted image 20241117123819.png]]
> Se crea la nueva key de acceso y se descarga el archivo que la contiene, para poder configurar nuestro aws cli.
> ![[Pasted image 20241117123932.png]]
> Se procede a configurar aws cli con el comando `aws configure` utilizando el Access Key y el Secret Access Key descargado anteriormente.
> ![[Pasted image 20241117124300.png]] 

#### Error ECR policies
> Una vez configurado aws cli se ejecuta nuevamente el comando indicado en los Push Commands.
> ![[Pasted image 20241117125046.png]]
> El error AccessDeniedException puede deberse a que las siguientes políticas deben agregarse al usuario.
> **Para acceso de solo lectura a ECR**: `AmazonEC2ContainerRegistryReadOnly`
> **Para acceso completo a ECR**:`AmazonEC2ContainerRegistryPowerUser`
> **Para acceso administrativo completo** (no recomendado a menos que sea necesario): `AmazonEC2ContainerRegistryFullAccess`
> 
> Por tanto vamos nuevamente a IAM y agregamos al usuario las políticas necesarias.
> ![[Pasted image 20241117125534.png]]
> ![[Pasted image 20241117125627.png]]




## 4. Crear Aplicación Load Balancer y Target Groups

Para este paso utilizamos el servicio EC2 en el balanceador de carga los Targe Groups
![[Pasted image 20241117133304.png]]
![[Pasted image 20241117133415.png]]
![[Pasted image 20250308072252.png]]

Se crea el grupo definiendo el tipo IP address, el nombre y el puerto, el resto de configuraciones se dejan por defecto.
![[Pasted image 20241117134556.png]]
Si no hubo errores en la configuración el grupo se listará en los Target Groups  ![[Pasted image 20241117134721.png]]

A continuación se crea el balanceador de carga de tipo `Application Load Balancer`
![[Pasted image 20241117134830.png]]
![[Pasted image 20241117134851.png]]
![[Pasted image 20241117135012.png]]

Definimos el nombre del balanceador y las configuraciones de networking por defecto.
![[Pasted image 20241117135144.png]]
![[Pasted image 20241117135502.png]]

Para el security group se requiere que las reglas de entrada y salida permitan todo el tráfico para ello se crea un nuevo secutiry group con estas configuraciones y lo seleccionamos.

> Ahora obliga en una ventana aparte y quedaría así pero apoyarse en lo de abajo
> ![[Pasted image 20250308073518.png]]

![[Pasted image 20241117135920.png]]
> Se debe recargar
>  ![[Pasted image 20250308073620.png]]

![[Pasted image 20241117140015.png]]

Para la configuración de listeners agregamos dos uno apuntando al puerto 80 y el otro apuntando al puerto 8080 los dos redirigidos al grupo creado anteriormente.
![[Pasted image 20241117140206.png]]

Con ello se deja el resto de configuraciones por defecto y se crea el balanceador. ![[Pasted image 20241117140313.png]]

## 5. Creación de Task Definition y Cluster sobre ECS
Para ello usamos el servicio ECS y sobre el menú Clústeres creamos un Cluster nuevo.
![[Pasted image 20241117140529.png]]
clic en get started
![[Pasted image 20250308073924.png]]

Se define el nombre del cluster y la infraestructura AWS Fargate, el resto de configuraciones se mantiene por defecto.

![[Pasted image 20241117140748.png]]

Luego se procede a crear la tarea para el clúster definiendo el nombre la infraestructura Fargate, la CPU y se selecciona crear un nuevo rol, para habilitar las politicas de ECS.
![[Pasted image 20241117141117.png]]
![[Pasted image 20241117141406.png]]

Se definen los valores para el contenedor, asignándole un nombre y la URI obtenida en el paso 2, ademas del puerto sobre el que corre la app.
![[Pasted image 20241117141731.png]]

Finalmente se dejan el resto de configuraciones por defecto y se crea la tarea, con ello se mostrarán los detalles y el valor del nuevo rol creado, dicho nombre se utilizará en próximas configuraciones por tanto guardamos ese valor.
![[Pasted image 20241117142011.png]]
Role: `ecsTaskExecutionRole`

Ahora dentro del clúster creado anteriormente, creamos un nuevo servicio.
![[Pasted image 20241117142350.png]]

Definimoss la configuración de computo como Launch Type de tipo Fargate y en la configuración de despliegue seleccionamos servicio, la tarea creada anteoriormente y para el tipo de servicio se selecciona replicas y el numero de nodos.

![[Pasted image 20241117142501.png]]
![[Pasted image 20241117142631.png]]

En opciones de despliegue usamos el modelo Blue/Green para definir como se comportará el ruteo y ademas asignamos el role creado anteriormente que tiene las políticas requeridas para el despliegue.
![[Pasted image 20241117142944.png]]
> el rol se ve aquí
> ![[Pasted image 20250308080634.png]]

Para la sección de red configuramos la VPC y sus respectivas Subnets por defecto, además seleccionamos el rol que ya se había creado que contenga la configuración de entradas y salidas de red.
![[Pasted image 20241117143305.png]]

Ahora se procede a configurar el balanceador de carga para este servicio y los listeners de producción y pruebas.
![[Pasted image 20241117143800.png]]

Para la configuración de Targe Groups usamos los que ya teniamos creados y damos en la opción crear.
![[Pasted image 20241117144014.png]]

Con la configuración realizada el servicio procede al despliegue de la tarea y confirma el estado desde la interfaz de servicios y por medio del DNS del balanceador de cargas se puede consultar el estado de salud del servidor.
![[Pasted image 20241117164413.png]]
![[Pasted image 20241117164506.png]]

Se aprecia que los target groups registran IPs privadas y que en CodeDeploy la aplicación ya se encuentra corriendo.
![[Pasted image 20241117164727.png]]
![[Pasted image 20241117164923.png]]

## 5. Configuración de archivos para CodeBuild

Dentro del repositorio se construye el archivo con base en la estructura planteada en el manual guía del curso, siguiendo los comandos entregados por aws para el despliegue de imagenes al repositorio configurado anteriormente.
![[Pasted image 20241117173416.png]]
