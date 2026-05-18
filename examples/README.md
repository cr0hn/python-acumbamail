# Acumbamail SDK — Ejemplos

Ejemplos listos para ejecutar que demuestran las funcionalidades principales del SDK.

## Requisitos

```bash
pip install acumbamail
export ACUMBAMAIL_TOKEN="tu_token_aqui"
```

> El token se obtiene en tu cuenta de Acumbamail → Configuración → API.

## Ejemplos disponibles

### `example-001.py` — Hello World

El ejemplo más sencillo posible: listar tus listas de correo y añadir un suscriptor.
Punto de entrada recomendado para familiarizarse con el SDK.

```bash
python examples/example-001.py
```

---

### `sync_example.py` — Cliente síncrono básico

Muestra las operaciones más habituales con `AcumbamailClient`:

- Listar listas (`get_lists`)
- Añadir suscriptor (`add_subscriber`)
- Obtener suscriptores (`get_subscribers`)
- Crear campaña con `*|UNSUBSCRIBE_URL|*` (`create_campaign`)
- Ver estadísticas de campaña (`get_campaign_total_information`)

```bash
python examples/sync_example.py
```

---

### `async_example.py` — Cliente asíncrono

Equivalente a `sync_example.py` usando `AsyncAcumbamailClient` con `async/await`.
Incluye ejemplo con context manager (recomendado) y sin él.

```bash
python examples/async_example.py
```

---

### `campaign_analytics.py` — Análisis de campañas

Análisis de rendimiento de campañas:

- Listado de campañas (`get_campaigns`)
- Métricas totales: open rate, click rate, bounces (`get_campaign_total_information`)
- URLs más clicadas (`get_campaign_clicks`)
- Aperturas por navegador (`get_campaign_openers_by_browser`)
- Aperturas por sistema operativo (`get_campaign_openers_by_os`)

```bash
python examples/campaign_analytics.py
```

---

### `bulk_operations.py` — Operaciones en masa

Gestión eficiente de grandes volúmenes de datos:

- Alta de suscriptores en lote (`batch_add_subscribers`)
- Búsqueda de suscriptores (`search_subscriber`)
- Suscriptores inactivos con detalle (`get_inactive_subscribers` con `full_info=True`)

```bash
python examples/bulk_operations.py
```

---

### `ab_testing.py` — A/B Testing

Crea dos campañas con distintos subjects para la misma lista y compara sus estadísticas
(`get_campaign_total_information`) para determinar qué variante funciona mejor.

**AVISO:** crea campañas reales en tu cuenta.

```bash
python examples/ab_testing.py
```

---

### `automated_workflows.py` — Workflows automatizados

Flujo completo de automatización:

1. Crear lista (`create_list`)
2. Alta masiva de suscriptores (`batch_add_subscribers`)
3. Crear campaña de bienvenida (`create_campaign`)
4. Consultar estadísticas (`get_campaign_total_information`)
5. Configurar webhook de lista (`config_list_webhook` — comentado por defecto)

**AVISO:** crea listas, suscriptores y campañas reales en tu cuenta.

```bash
python examples/automated_workflows.py
```

---

### `error_handling.py` — Manejo de errores

Patrones de gestión de errores del SDK:

- `AcumbamailValidationError` — email inválido, campaña sin `*|UNSUBSCRIBE_URL|*`
- `AcumbamailAPIError` — errores devueltos por la API
- `AcumbamailRateLimitError` — límite de peticiones superado (el SDK reintenta automáticamente)
- Degradación elegante con estrategia de fallback
- Operaciones en lote con errores parciales

```bash
python examples/error_handling.py
```

---

## Notas importantes

- **Token:** usa siempre `ACUMBAMAIL_TOKEN` (no `ACUMBAMAIL_AUTH_TOKEN`).
- **UNSUBSCRIBE_URL:** todo contenido de campaña debe incluir `*|UNSUBSCRIBE_URL|*` o la API lo rechazará.
- **List ID de prueba:** los ejemplos usan `1138335` por defecto; cámbialo por el ID de una lista real de tu cuenta.
- **Operaciones destructivas:** los ejemplos que crean o borran datos están marcados con el aviso `AVISO`.
- **Rate limiting:** el SDK reintenta automáticamente las peticiones con HTTP 429 (3 intentos con backoff de 10s).
