# API Test

API REST con **FastAPI + SQLModel + MySQL**, levantada con **Docker**.

- Registro e inicio de sesión con 3 métodos de autenticación.
- Roles `admin` y `cliente`.
- CRUD de clientes (solo `admin`).

## Puesta en marcha

```bash
cp .env.example .env   # edita las contraseñas y el JWT_SECRET
docker compose up --build
```

- Swagger: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health
- MySQL expuesto en `localhost:3307`.

Al arrancar se crean las tablas, los roles `admin` / `cliente` y el administrador definido en `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

## Autenticación

| Método | Cómo se obtiene | Cómo se envía |
|---|---|---|
| **JWT** (access 15 min + refresh 7 días con rotación) | `POST /api/v1/auth/login` | `Authorization: Bearer <access_token>` |
| **Sesión con cookie** HttpOnly / Secure / SameSite=Strict | `POST /api/v1/auth/session/login` | Cookie `session_id` (automática en el navegador) |
| **API key** (máquina a máquina) | `POST /api/v1/auth/api-keys` (estando autenticado) | `X-API-Key: <key>` |

Medidas de seguridad:
- Contraseñas con **Argon2id**; mínimo 8 caracteres con mayúsculas, minúsculas y números.
- Refresh tokens, sesiones y API keys se guardan **solo hasheados** (SHA-256).
- Rotación de refresh tokens: reutilizar uno ya usado revoca todos los del usuario.
- Bloqueo de cuenta tras 5 intentos fallidos durante 15 minutos (configurable).
- La API key completa solo se muestra una vez al crearla.

## Endpoints

**Auth** (`/api/v1/auth`)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/register` | Registro público (rol `cliente`) |
| POST | `/login` | Login JWT |
| POST | `/refresh` | Rota el refresh token |
| POST | `/logout` | Revoca el refresh token |
| POST | `/session/login` | Login con cookie de sesión |
| POST | `/session/logout` | Cierra la sesión |
| GET | `/me` | Usuario actual |
| POST / GET | `/api-keys` | Crear / listar API keys |
| DELETE | `/api-keys/{id}` | Revocar API key |

**Clientes** (`/api/v1`) — solo `admin`

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/clientes` | Crear cliente |
| GET | `/clientes?offset=0&limit=20&buscar=` | Listar (paginado y búsqueda) |
| GET | `/clientes/{id}` | Obtener |
| PUT | `/clientes/{id}` | Actualizar (parcial) |
| DELETE | `/clientes/{id}` | Eliminar |

## Tablas

`roles`, `usuarios`, `clientes` y, para la autenticación, `refresh_tokens`, `sesiones` y `api_keys`.

## Arquitectura por capas

```
Request → api (routers) → services → models / db
                ↑               │
                └─ exception_handlers ← excepciones de dominio
```

| Capa | Responsabilidad | No debe |
|---|---|---|
| `api/` | Recibir el request, validar la entrada con schemas, inyectar dependencias, llamar al servicio y dar forma a la respuesta HTTP (status, cookies). | Hacer consultas ni contener reglas de negocio. |
| `services/` | Toda la lógica de negocio y las consultas a la BD. Lanzan excepciones de dominio (`core/exceptions.py`). | Conocer HTTP (`HTTPException`, `Request`, cookies). |
| `schemas/` | Contratos de entrada/salida de la API (Pydantic). | Mapear tablas. |
| `models/` | Tablas SQLModel. | Contener lógica. |
| `db/` | Engine, sesión por request e inicialización (tablas + datos base). | — |
| `core/` | Configuración, seguridad (hash, JWT, tokens) y excepciones de dominio. | Depender de otras capas. |

```
app/
├── main.py                     # create_app(): middlewares, handlers, routers
├── api/
│   ├── deps.py                 # Sesión BD, servicios, usuario actual, roles
│   ├── exception_handlers.py   # Excepción de dominio → código HTTP
│   └── v1/
│       ├── router.py           # Agrega los routers de la v1
│       └── endpoints/          # auth.py, api_keys.py, clientes.py
├── services/                   # auth, api_key, usuario, rol, cliente
├── schemas/                    # auth, usuario, api_key, cliente, common (Pagina)
├── models/                     # rol, usuario, cliente, refresh_token, sesion, api_key
├── db/                         # session.py, init_db.py
└── core/                       # config.py, security.py, exceptions.py
```

### Agregar un módulo nuevo (ej. `productos`)
1. `models/producto.py` → tabla.
2. `schemas/producto.py` → `ProductoCrear`, `ProductoActualizar`, `ProductoPublico`.
3. `services/producto_service.py` → lógica y consultas; lanza `NotFoundError`, `ConflictError`, etc.
4. `api/deps.py` → `ProductoServiceDep`.
5. `api/v1/endpoints/productos.py` → router que solo llama al servicio.
6. Registrarlo en `api/v1/router.py` e importarlo en `models/__init__.py`.

Los errores del servicio se traducen solos a HTTP (404, 409, 400, 401, 403, 423) y cualquier error no controlado se registra en el log y devuelve un 500 genérico, sin exponer detalles internos.
