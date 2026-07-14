"""
UCOM Credit Check API
=====================
Prototipo de API REST para verificación de crédito de empresas.

Tecnologías:
- FastAPI: Framework web de alto rendimiento
- Pydantic: Validación de datos y serialización
- Python 3.9+ compatible (usa Optional/Union en lugar de |)

Flujo de negocio:
1. Registrar empresa → POST /companies
2. Crear cuenta asociada → POST /accounts (valores default: limite=5000, descuento=5%)
3. Verificar crédito → POST /credit-check (genera calificación 1-10)
4. Consultar historial → GET /credit-history/{company_name}

Seguridad:
- Autenticación mediante Bearer Token (header Authorization)
- Token estático de prueba: ucom-secret-token-2026
- Todos los endpoints protegidos excepto / y /openapi.yaml

Autor: Victor Martinez
Institución: UCOM
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional, Union  # Python 3.9 compatible
from uuid import uuid4
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

app = FastAPI(
    title="UCOM Credit Check API",
    description=(
        "API REST para registrar empresas y cuentas, realizar "
        "verificaciones de crédito y consultar su historial. "
        "Todos los endpoints protegidos requieren Bearer Token."
    ),
    version="1.0.0",
    contact={
        "name": "Victor Martinez",
        "url": "https://github.com/ziroch/ucom-credit-check-api"
    },
    license_info={
        "name": "Uso académico",
        "url": "https://ucom.edu.py"
    }
)

# Rutas de archivos estáticos
BASE_DIR = Path(__file__).resolve().parent.parent
OPENAPI_YAML_PATH = BASE_DIR / "openapi.yaml"

# Token estático de autenticación (modo prototipo)
# En producción, usar JWT o OAuth2 con rotación de tokens
STATIC_TOKEN = "ucom-secret-token-2026"

# auto_error=False permite devolver nuestro propio error 401 personalizado
security = HTTPBearer(auto_error=False)


# ============================================================
# SEGURIDAD - AUTENTICACIÓN BEARER TOKEN
# ============================================================

def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Verifica que el encabezado Authorization contenga un Bearer Token válido.

    Flujo de autenticación:
    1. Verificar que el header Authorization esté presente
    2. Verificar que el esquema sea "Bearer"
    3. Verificar que el token coincida con STATIC_TOKEN
    4. Retornar el token válido para uso en endpoints

    Args:
        credentials: Credenciales extraídas del header Authorization

    Returns:
        str: Token válido verificado

    Raises:
        HTTPException: 401 si el token es inválido, ausente o tiene esquema incorrecto
    """

    # Paso 1: Verificar presencia del token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado. Incluya el header Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Paso 2: Verificar esquema Bearer
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema de autenticación inválido. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Paso 3: Verificar token usando compare_digest (timing-safe)
    if not secrets.compare_digest(credentials.credentials, STATIC_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o no autorizado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Token válido
    return credentials.credentials


# ============================================================
# MODELOS DE DATOS (PYDANTIC)
# ============================================================

class CompanyCreate(BaseModel):
    """
    Modelo para crear una nueva empresa.
    Todos los campos son obligatorios excepto status (default: ACTIVE).
    """
    companyName: str = Field(
        min_length=2,
        max_length=120,
        description="Nombre comercial de la empresa",
        examples=["UCOM Technologies"]
    )
    streetAddress: str = Field(
        min_length=3,
        description="Dirección fiscal completa",
        examples=["Av. Mariscal López 1234"]
    )
    city: str = Field(
        min_length=2,
        description="Ciudad de ubicación",
        examples=["Asunción"]
    )
    stateProvince: str = Field(
        min_length=2,
        description="Estado o provincia",
        examples=["Central"]
    )
    postalCode: str = Field(
        min_length=2,
        description="Código postal",
        examples=["1209"]
    )
    country: str = Field(
        min_length=2,
        description="País de operación",
        examples=["Paraguay"]
    )
    phone: str = Field(
        min_length=6,
        description="Teléfono de contacto principal",
        examples=["+59521456123"]
    )
    email: str = Field(
        min_length=5,
        description="Correo electrónico corporativo",
        examples=["contacto@ucom.com.py"]
    )
    status: Literal["ACTIVE", "INACTIVE"] = Field(
        default="ACTIVE",
        description="Estado de la empresa: ACTIVE o INACTIVE"
    )


class Company(CompanyCreate):
    """
    Modelo de empresa registrada.
    Extiende CompanyCreate agregando el identificador UUID generado.
    """
    id: str = Field(
        description="Identificador único UUID generado automáticamente",
        examples=["14b758d8-357c-4c8f-a9e2-c6055cc8ab30"]
    )


class AccountCreate(BaseModel):
    """
    Modelo para crear una cuenta corporativa.

    Valores predeterminados:
    - spendingLimit: 5000
    - discountPercentage: 5
    - status: ACTIVE
    """
    companyId: str = Field(
        min_length=1,
        description="ID UUID de la empresa a la que pertenece la cuenta",
        examples=["14b758d8-357c-4c8f-a9e2-c6055cc8ab30"]
    )
    division: str = Field(
        min_length=2,
        max_length=100,
        description="División o departamento de la empresa",
        examples=["Corporate"]
    )
    spendingLimit: float = Field(
        default=5000,
        ge=0,
        description="Límite máximo de gasto. Default: $5,000",
        examples=[5000]
    )
    discountPercentage: float = Field(
        default=5,
        ge=0,
        le=100,
        description="Porcentaje de descuento. Default: 5%",
        examples=[5]
    )
    status: Literal["ACTIVE", "INACTIVE", "BLOCKED"] = Field(
        default="ACTIVE",
        description="Estado de la cuenta: ACTIVE, INACTIVE o BLOCKED"
    )


class Account(AccountCreate):
    """
    Modelo de cuenta registrada.
    Extiende AccountCreate agregando el identificador UUID.
    """
    id: str = Field(
        description="Identificador único UUID de la cuenta",
        examples=["9c44dbd0-f75b-41ab-85d3-a4a6acd2db19"]
    )


class CreditRequest(BaseModel):
    """
    Payload para solicitar una verificación de crédito.
    Requiere el nombre exacto de una empresa previamente registrada.
    """
    companyName: str = Field(
        min_length=2,
        max_length=120,
        description="Nombre exacto de la empresa a verificar",
        examples=["UCOM Technologies"]
    )


class CreditResponse(BaseModel):
    """
    Respuesta de una verificación de crédito exitosa.
    Incluye la calificación generada y los valores recomendados.
    """
    companyName: str = Field(
        description="Nombre de la empresa verificada",
        examples=["UCOM Technologies"]
    )
    creditScore: int = Field(
        ge=1,
        le=10,
        description="Calificación de crédito (1=Riesgo alto, 10=Riesgo bajo)",
        examples=[8]
    )
    recommendedSpendingLimit: float = Field(
        ge=0,
        description="Límite de gasto recomendado según calificación",
        examples=[15000]
    )
    recommendedDiscountPercentage: float = Field(
        ge=0,
        le=100,
        description="Porcentaje de descuento recomendado",
        examples=[12]
    )


class CreditHistory(BaseModel):
    """
    Registro de historial de una verificación de crédito.
    Permite auditar las calificaciones asignadas a lo largo del tiempo.
    """
    id: str = Field(
        description="Identificador único del registro de historial",
        examples=["a70d4dc1-a855-44ef-8a41-81c4995a0037"]
    )
    companyName: str = Field(
        description="Nombre de la empresa verificada",
        examples=["UCOM Technologies"]
    )
    requestDate: datetime = Field(
        description="Fecha y hora de la solicitud (zona horaria Paraguay, UTC-3)",
        examples=["2026-06-28T14:35:00-03:00"]
    )
    creditScore: int = Field(
        ge=1,
        le=10,
        description="Calificación generada en la verificación",
        examples=[8]
    )


# ============================================================
# ALMACENAMIENTO EN MEMORIA (PROTOTIPO)
# ============================================================
# En producción, reemplazar por PostgreSQL, MongoDB, etc.

companies: list = []
accounts: list = []
credit_history: list = []


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def find_company_by_id(company_id: str) -> Optional[Company]:
    """Busca una empresa por su identificador UUID."""
    return next(
        (company for company in companies if company.id == company_id),
        None
    )


def find_company_by_name(company_name: str) -> Optional[Company]:
    """
    Busca una empresa por nombre (búsqueda case-insensitive).
    Normaliza el nombre eliminando espacios y convirtiendo a minúsculas.
    """
    normalized_name = company_name.strip().lower()
    return next(
        (
            company
            for company in companies
            if company.companyName.strip().lower() == normalized_name
        ),
        None
    )


def calculate_credit_score(company_name: str) -> int:
    """
    Algoritmo académico simplificado de generación de calificación.

    Genera una calificación entre 1 y 10 a partir de la longitud
    del nombre de la empresa. En una solución real, el método
    utilizaría información financiera, historial de pagos, reportes
    de buró de crédito y otros datos confidenciales.

    Args:
        company_name: Nombre de la empresa a calificar

    Returns:
        int: Calificación entre 1 (riesgo alto) y 10 (riesgo bajo)
    """
    return (len(company_name.strip()) % 10) + 1


def get_paraguay_datetime() -> datetime:
    """
    Obtiene la fecha y hora actual en la zona horaria de Paraguay (UTC-3).
    """
    paraguay_timezone = timezone(timedelta(hours=-3))
    return datetime.now(paraguay_timezone)


# ============================================================
# ENDPOINTS GENERALES
# ============================================================

@app.get(
    "/",
    tags=["General"],
    summary="Información general de la API",
    description="Devuelve información básica sobre la API y enlaces a la documentación."
)
def home():
    """Endpoint raíz — información general y enlaces a documentación."""
    return {
        "message": "UCOM Credit Check API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapiYaml": "/openapi.yaml"
    }


@app.get(
    "/openapi.yaml",
    tags=["General"],
    summary="Descargar especificación OpenAPI YAML",
    description="Devuelve el archivo de especificación OpenAPI en formato YAML.",
    include_in_schema=False
)
def get_openapi_yaml():
    """Endpoint para descargar la especificación OpenAPI YAML completa."""
    if not OPENAPI_YAML_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el archivo openapi.yaml"
        )

    return FileResponse(
        path=OPENAPI_YAML_PATH,
        media_type="application/yaml",
        filename="openapi.yaml"
    )


# ============================================================
# ENDPOINTS DE EMPRESAS (COMPANIES)
# ============================================================

@app.post(
    "/companies",
    tags=["Companies"],
    summary="Registrar una empresa",
    description=(
        "Registra una nueva empresa en el sistema. "
        "Genera automáticamente un UUID como identificador. "
        "Valida que el nombre y correo no estén duplicados."
    ),
    response_model=Company,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Token ausente o inválido"},
        409: {"description": "La empresa o el correo ya están registrados"},
        422: {"description": "Datos de entrada inválidos"}
    }
)
def create_company(
    company_data: CompanyCreate,
    token: str = Depends(verify_token)
):
    """
    Crea una nueva empresa en el sistema.

    Reglas de negocio:
    - El nombre de empresa debe ser único (case-insensitive)
    - El correo electrónico debe ser único (case-insensitive)
    - Se genera automáticamente un UUID v4 como identificador
    - El estado predeterminado es ACTIVE
    """
    del token  # Token ya verificado por el dependency

    # Validar duplicados por nombre
    duplicated_name = find_company_by_name(company_data.companyName)
    if duplicated_name is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una empresa con ese nombre"
        )

    # Validar duplicados por correo
    duplicated_email = next(
        (
            company
            for company in companies
            if company.email.strip().lower()
            == company_data.email.strip().lower()
        ),
        None
    )
    if duplicated_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una empresa con ese correo electrónico"
        )

    # Crear empresa con UUID
    company = Company(
        id=str(uuid4()),
        **company_data.model_dump()
    )

    companies.append(company)

    return company


@app.get(
    "/companies",
    tags=["Companies"],
    summary="Listar todas las empresas",
    description="Devuelve el listado completo de empresas registradas en el sistema.",
    response_model=list,
    responses={
        401: {"description": "Token ausente o inválido"}
    }
)
def list_companies(token: str = Depends(verify_token)):
    """Obtiene todas las empresas registradas."""
    del token
    return companies


@app.get(
    "/companies/{company_id}",
    tags=["Companies"],
    summary="Buscar empresa por ID",
    description="Recupera los detalles de una empresa específica mediante su UUID.",
    response_model=Company,
    responses={
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Empresa no encontrada"}
    }
)
def get_company(
    company_id: str,
    token: str = Depends(verify_token)
):
    """Busca una empresa por su identificador UUID."""
    del token

    company = find_company_by_id(company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    return company


# ============================================================
# ENDPOINTS DE CUENTAS (ACCOUNTS)
# ============================================================

@app.post(
    "/accounts",
    tags=["Accounts"],
    summary="Registrar una cuenta",
    description=(
        "Registra una cuenta vinculada a una empresa existente. "
        "El límite predeterminado es 5000 y el descuento es 5%."
    ),
    response_model=Account,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Empresa asociada no encontrada"},
        422: {"description": "Datos de entrada inválidos"}
    }
)
def create_account(
    account_data: AccountCreate,
    token: str = Depends(verify_token)
):
    """
    Crea una nueva cuenta corporativa.

    Reglas de negocio:
    - La empresa referenciada por companyId debe existir
    - Se genera automáticamente un UUID como identificador
    - Valores predeterminados: spendingLimit=5000, discountPercentage=5, status=ACTIVE
    """
    del token

    # Verificar que la empresa exista
    company = find_company_by_id(account_data.companyId)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una empresa con el companyId indicado"
        )

    # Crear cuenta con UUID
    account = Account(
        id=str(uuid4()),
        **account_data.model_dump()
    )

    accounts.append(account)

    return account


@app.get(
    "/accounts",
    tags=["Accounts"],
    summary="Listar todas las cuentas",
    description="Devuelve el listado completo de cuentas registradas.",
    response_model=list,
    responses={
        401: {"description": "Token ausente o inválido"}
    }
)
def list_accounts(token: str = Depends(verify_token)):
    """Obtiene todas las cuentas registradas."""
    del token
    return accounts


# ============================================================
# VERIFICACIÓN DE CRÉDITO (CREDIT CHECK)
# ============================================================

@app.post(
    "/credit-check",
    tags=["Credit Check"],
    summary="Ejecutar verificación de crédito",
    description=(
        "Calcula una calificación entre 1 y 10, recomienda un límite "
        "de gasto y un descuento, y registra automáticamente el historial."
    ),
    response_model=CreditResponse,
    responses={
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Empresa no encontrada"},
        422: {"description": "Datos de entrada inválidos"}
    }
)
def verify_credit(
    request: CreditRequest,
    token: str = Depends(verify_token)
):
    """
    Ejecuta una verificación de crédito para una empresa.

    Proceso:
    1. Busca la empresa por nombre (case-insensitive)
    2. Genera calificación 1-10 usando algoritmo académico
    3. Determina límite y descuento recomendados según calificación
    4. Registra el resultado en el historial

    Tabla de calificaciones:
    - 1-4: Riesgo Alto → $3,000 / 2%
    - 5-7: Riesgo Medio → $8,000 / 7%
    - 8-10: Riesgo Bajo → $15,000 / 12%
    """
    del token

    # Buscar empresa por nombre
    company = find_company_by_name(request.companyName)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La empresa debe registrarse antes de verificar su crédito"
        )

    # Generar calificación
    score = calculate_credit_score(company.companyName)

    # Determinar valores recomendados según calificación
    if score >= 8:
        spending_limit = 15000
        discount_percentage = 12
    elif score >= 5:
        spending_limit = 8000
        discount_percentage = 7
    else:
        spending_limit = 3000
        discount_percentage = 2

    # Registrar en historial
    history_record = CreditHistory(
        id=str(uuid4()),
        companyName=company.companyName,
        requestDate=get_paraguay_datetime(),
        creditScore=score
    )

    credit_history.append(history_record)

    return CreditResponse(
        companyName=company.companyName,
        creditScore=score,
        recommendedSpendingLimit=spending_limit,
        recommendedDiscountPercentage=discount_percentage
    )


# ============================================================
# HISTORIAL DE CRÉDITO (CREDIT HISTORY)
# ============================================================

@app.get(
    "/credit-history/{company_name}",
    tags=["Credit History"],
    summary="Consultar historial de crédito",
    description=(
        "Devuelve las verificaciones realizadas para una empresa. "
        "La búsqueda no distingue mayúsculas y minúsculas."
    ),
    response_model=list,
    responses={
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Historial no encontrado"}
    }
)
def get_credit_history(
    company_name: str,
    token: str = Depends(verify_token)
):
    """
    Recupera el historial de verificaciones de crédito para una empresa.

    La búsqueda es case-insensitive y devuelve resultados ordenados
    por fecha descendente (más recientes primero).
    """
    del token

    normalized_name = company_name.strip().lower()

    result = [
        record
        for record in credit_history
        if record.companyName.strip().lower() == normalized_name
    ]

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe historial para esta empresa"
        )

    return result
