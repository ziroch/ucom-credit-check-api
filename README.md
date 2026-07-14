# UCOM Credit Check API

API REST para la gestión de empresas, cuentas corporativas y verificación de crédito.

##Descripción

Este proyecto implementa un prototipo de API para BigCo, Inc. que permite:

1. Registrar empresas clientes con datos de contacto completos
2. Crear cuentas corporativas con límite de gasto y descuento (valores default: $5,000 / 5%)
3. Ejecutar verificaciones de crédito que generan una calificación del 1 al 10
4. Consultar historial de verificaciones para auditoría

##Arquitectura

```
ucom-credit-check-api/
├── app/
│   └── main.py              # Aplicación FastAPI con endpoints y lógica
├── capturas/                # Evidencias de Swagger y pruebas de seguridad
├── docs/                    # Documentación adicional
├── tests/                   # Scripts de prueba
├── openapi.yaml             # Especificación OpenAPI 3.1 enriquecida
├── requirements.txt         # Dependencias Python
├── .gitignore
└── README.md
```

## Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/hernansilgueira-ccp/ucom-credit-check-api.git
cd ucom-credit-check-api
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# o
.venv\Scripts\activate       # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la API
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Acceder a la documentación
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI YAML: http://localhost:8000/openapi.yaml

## Seguridad

La API utiliza autenticación mediante Bearer Token.

### Token de prueba
```
ucom-secret-token-2026
```

### Uso en peticiones
Incluir el header:
```
Authorization: Bearer ucom-secret-token-2026
```

### Endpoints protegidos
Todos los endpoints requieren autenticación excepto:
- `GET /` — Información general
- `GET /openapi.yaml` — Descargar especificación

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información general |
| GET | `/openapi.yaml` | Descargar especificación OpenAPI |
| POST | `/companies` | Registrar empresa |
| GET | `/companies` | Listar empresas |
| GET | `/companies/{company_id}` | Buscar empresa por ID |
| POST | `/accounts` | Registrar cuenta |
| GET | `/accounts` | Listar cuentas |
| POST | `/credit-check` | Verificar crédito |
| GET | `/credit-history/{company_name}` | Consultar historial |

## Pruebas con cURL

### 1. Sin token (debe fallar con 401)
```bash
curl -X GET "http://localhost:8000/companies"
```

### 2. Con token válido
```bash
curl -X GET "http://localhost:8000/companies" \
  -H "Authorization: Bearer ucom-secret-token-2026"
```

### 3. Crear empresa
```bash
curl -X POST "http://localhost:8000/companies" \
  -H "Authorization: Bearer ucom-secret-token-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "companyName": "UCOM Technologies",
    "streetAddress": "Av. Mariscal López 1234",
    "city": "Asunción",
    "stateProvince": "Central",
    "postalCode": "1209",
    "country": "Paraguay",
    "phone": "+59521456123",
    "email": "contacto@ucom.com.py",
    "status": "ACTIVE"
  }'
```

### 4. Verificar crédito
```bash
curl -X POST "http://localhost:8000/credit-check" \
  -H "Authorization: Bearer ucom-secret-token-2026" \
  -H "Content-Type: application/json" \
  -d '{"companyName": "UCOM Technologies"}'
```

### 5. Consultar historial
```bash
curl -X GET "http://localhost:8000/credit-history/UCOM%20Technologies" \
  -H "Authorization: Bearer ucom-secret-token-2026"
```

## Tabla de Calificaciones

| Calificación | Riesgo | Límite Recomendado | Descuento Recomendado |
|-------------|--------|-------------------|----------------------|
| 1-4 | Alto | $3,000 | 2% |
| 5-7 | Medio | $8,000 | 7% |
| 8-10 | Bajo | $15,000 | 12% |

## 📝 Especificación OpenAPI

El archivo `openapi.yaml` contiene la especificación completa en formato YAML con:
- Descripciones detalladas de cada endpoint
- Ejemplos de entrada y salida (`examples`)
- Esquema de seguridad Bearer Token
- Modelos de datos con ejemplos para Swagger/ReDoc
- Tags organizados por dominio
- Respuestas de error documentadas


