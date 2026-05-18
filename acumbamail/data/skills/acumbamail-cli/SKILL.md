---
name: acumbamail-cli
description: Use when working with the Acumbamail CLI or Python SDK — managing lists, subscribers, campaigns, templates, and webhooks. Covers all CLI subcommands, SDK methods, authentication, known quirks and limitations discovered via real API testing.
---

# Acumbamail CLI & SDK

The `acumbamail` CLI and Python SDK manage Acumbamail email marketing. All CLI output is JSON on stdout; errors go to stderr with exit code 1.

## Authentication

```bash
export ACUMBAMAIL_TOKEN=your_token_here

# or per-command:
acumbamail --token YOUR_TOKEN lists list
```

```python
from acumbamail import AcumbamailClient
client = AcumbamailClient(
    auth_token="your_token",
    default_sender_email="sender@domain.com",   # required for campaigns
    default_sender_name="Mi Empresa",
)
```

---

## CLI Commands

### `lists` — Listas de suscriptores

```bash
acumbamail lists list
# → [{"id": 123, "name": "Newsletter", "subscribers_count": 500, "bounced_count": 3, ...}]

acumbamail lists create --name "My List" --sender-email sender@example.com
acumbamail lists create --name "My List" --sender-email sender@example.com --description "Weekly"
# → {"id": 456, "name": "My List", "description": ""}

acumbamail lists delete --list-id 456
# → {"deleted": true, "list_id": 456}

acumbamail lists stats --list-id 123
# → {"total_subscribers": 500, "unsubscribed_subscribers": 12, "hard_bounced_subscribers": 3, ...}
```

### `subscribers` — Suscriptores

```bash
acumbamail subscribers list --list-id 123
# → [{"email": "user@x.com", "list_id": 123, "is_active": true, "fields": {...}}, ...]

acumbamail subscribers add --list-id 123 --email user@example.com
acumbamail subscribers add --list-id 123 --email user@example.com --fields '{"nombre": "Juan"}'
# → {"email": "user@example.com", "list_id": 123}

acumbamail subscribers delete --list-id 123 --email user@example.com
# → {"deleted": true, "email": "user@example.com", "list_id": 123}

acumbamail subscribers search --query user@example.com
# → [{"email": "user@example.com", "status": "active", "list_id": 123, "id": 456}, ...]

acumbamail subscribers unsubscribe --list-id 123 --email user@example.com
# → {"unsubscribed": true, "email": "user@example.com", "list_id": 123}

# Importación masiva desde JSON: [{"email": "a@x.com"}, {"email": "b@x.com", "nombre": "Bob"}]
acumbamail subscribers batch-add --list-id 123 --file subs.json
acumbamail subscribers batch-add --list-id 123 --file subs.json --update  # actualizar si ya existen
# → [{"email": "a@x.com", "subscriber_id": 111}, ...]
```

### `campaigns` — Campañas de email

```bash
# Crear y enviar campaña (envío inmediato si no se especifica --scheduled-at)
acumbamail campaigns create \
  --name "Newsletter Mayo" \
  --subject "Novedades de este mes" \
  --html-file email.html \
  --list-id 1138335 \
  --from-email sender@domain.com \
  --from-name "Mi Empresa"
# → {"id": 3294239, "name": "...", "subject": "...", "from_email": "...", "list_ids": [...]}

# HTML inline
acumbamail campaigns create --name "Aviso" --subject "Importante" \
  --html '<h1>Hola</h1><a href="*|UNSUBSCRIBE_URL|*">Baja</a>' \
  --list-id 1138335 --from-email sender@domain.com

# Programar envío
acumbamail campaigns create --name "Newsletter" --subject "..." \
  --html-file email.html --list-id 1138335 \
  --scheduled-at "2026-06-01 09:00"

# Múltiples listas (repetir --list-id)
acumbamail campaigns create --name "Promo" --subject "Oferta" \
  --html-file promo.html --list-id 123 --list-id 456

# Listar campañas — SOLO devuelve id y name (limitación de la API)
acumbamail campaigns list
# → [{"id": 3294239, "name": "Newsletter #1", "subject": "", "from_email": "", "list_ids": []}, ...]
# Para ver subject/from_email usa: campaigns info

# Detalle completo de una campaña (subject, from_email, listas, status)
acumbamail campaigns info --campaign-id 3294239
# → {"status": "Sent", "name": "...", "subject": "...", "email_from": "...", "lists": [...]}

# Estadísticas
acumbamail campaigns stats --campaign-id 3294239
# → {"total_delivered": 490, "opened": 120, "unique_clicks": 45, "hard_bounces": 8, ...}
```

**HTML obligatorio — tag de desuscripción:**

```html
<!-- OBLIGATORIO en todo HTML de campaña -->
<a href="*|UNSUBSCRIBE_URL|*">Darse de baja</a>
```

**Merge tags disponibles:**

```
*|UNSUBSCRIBE_URL|*   → URL de baja (único validado — falla si falta)
*|FNAME|*             → nombre
*|LNAME|*             → apellido
*|EMAIL|*             → email del suscriptor
*|FULLNAME|*          → nombre completo
*|ARCHIVE_URL|*       → versión online de la campaña
*|FORWARD_URL|*       → reenviar a un amigo
```

La API acepta cualquier `*|TAG|*` sin validar — solo `*|UNSUBSCRIBE_URL|*` se comprueba.

**Errores comunes en campaigns create:**
- `el HTML no contiene el tag de desuscripción` → añade `*|UNSUBSCRIBE_URL|*`
- `el email del remitente no está verificado` → verifica en https://acumbamail.com/app/account/senders/
- `from_email or default_sender_email is required` → añade `--from-email`

**Limitaciones de la API de campañas:**
- `campaigns list` solo devuelve id+name (la API no da más en el listado)
- No se pueden **borrar** campañas por API — solo desde el panel web
- No se pueden **cancelar** campañas programadas por API — solo desde el panel web
- `pre_header` y `tracking_domain` se aceptan al crear pero NO aparecen en `campaigns info`
- `send_single_email` requiere plan SMTP (retorna 401 sin él)

### `webhooks` — Webhooks

```bash
acumbamail webhooks smtp-get
acumbamail webhooks smtp-config --url https://myapp.com/hooks/smtp --delivered --hard-bounce --active
acumbamail webhooks smtp-config --url https://... --no-active  # deshabilitar

acumbamail webhooks list-get --list-id 123
acumbamail webhooks list-config --list-id 123 --url https://myapp.com/hooks/list \
  --subscribes --unsubscribes --active
```

---

## SDK Python — métodos sin CLI

Estos métodos existen en el cliente Python pero no tienen comando CLI:

### Templates

```python
# Listar templates (incluye los auto-generados de campañas con available=False)
templates = client.get_templates()
# → [Template(id=123, name="Welcome", content="..."), ...]
# Quirk: la API no devuelve content en el listado — Template.content = "" salvo al crear

# Filtrar solo los disponibles
available = [t for t in client.get_templates() if t.id]

# Crear template
tmpl = client.create_template(
    template_name="mi-plantilla",
    html_content="<h1>Hola *|FNAME|*</h1><a href='*|UNSUBSCRIBE_URL|*'>Baja</a>",
    subject="Asunto por defecto",
)
# → Template(id=9493654, name="mi-plantilla", content="...")

# Duplicar template
copia = client.duplicate_template(
    template_name="mi-plantilla-copia",
    origin_template_id=9493654,
)
# → Template(id=9493655, name="mi-plantilla-copia", content="")
# Quirk: content="" en el objeto devuelto (no se recupera del servidor)

# get_templates_by_name() NO funciona — el servidor devuelve 404 siempre
```

### Suscriptores — métodos avanzados

```python
# Detalles completos de un suscriptor
details = client.get_subscriber_details(list_id=1138335, subscriber_email="user@x.com")
# → SubscriberDetails(id=123, email="user@x.com", status="active", create_date=..., fields={...})
# Quirk: list_id queda None en el objeto (no viene en la respuesta de la API)

# Suscriptores inactivos (bajas, bounces) en un rango de fechas
from datetime import datetime
inactive = client.get_inactive_subscribers(
    list_id=1138335,
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
)
# → [InactiveSubscriber(email="user@x.com", reason=3, reason_date=...)]

# Con full_info=False (más rápido): devuelve solo emails
emails = client.get_inactive_subscribers(
    list_id=1138335,
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
    full_info=False,
)
# → ["user1@x.com", "user2@x.com", ...]

# Campos personalizados de una lista
fields = client.get_fields(list_id=1138335)
# → {"email": "email", "nombre": "char", "-curso >opcion1,opcion2": "combobox"}
# Quirk: combobox format = "-nombre_campo >opt1,opt2,opt3"

# Campos con sus TAGs (para merge tags en HTML)
merge_fields = client.get_merge_fields(list_id=1138335)
# → {"EMAIL": "email", "NOMBRE": "char", "CURSO": "combobox"}
# Devuelve {TAG: tipo} — diferente a get_fields que devuelve {nombre: tipo}

# Añadir campo personalizado a una lista
client.add_merge_tag(list_id=1138335, field_name="telefono", field_type="char")

# Formularios de la lista
forms = client.get_forms(list_id=1138335)
# → {} si no hay formularios configurados

# Borrar todos los suscriptores de una lista (¡destructivo!)
client.delete_all_subscribers(list_id=1138335)
```

### Analytics de campañas

```python
campaign_id = 3294239

# Clics
clicks = client.get_campaign_clicks(campaign_id)
# → [CampaignClick(url="...", clicks=45, unique_clicks=38, click_rate=0.09, ...)]
# → [] si no hay clics

# Aperturas (con detalle por suscriptor)
openers = client.get_campaign_openers(campaign_id)
# → [CampaignOpener(email="...", opened_at=datetime, ip="...", browser="...", os="...")]
# → [] si no hay aperturas

# Links registrados
links = client.get_campaign_links(campaign_id)
# → [] si no hay datos

# Soft bounces
bounces = client.get_campaign_soft_bounces(campaign_id)
# → [CampaignSoftBounce(email="...", bounced_at=..., reason="...")]
# → [] si no hay datos

# Por browser/OS (devuelven [] si no hay datos — no {})
by_browser = client.get_campaign_openers_by_browser(campaign_id)
by_os = client.get_campaign_openers_by_os(campaign_id)

# Por país (devuelve {} si no hay datos — diferente a los anteriores que devuelven [])
by_country = client.get_campaign_openers_by_countries(campaign_id)
# → {} vacío, o {"ES": 120, "MX": 45, ...}

# Por ISP (siempre incluye Gmail/Hotmail/Yahoo/Others aunque sean 0)
by_isp = client.get_campaign_information_by_isp(campaign_id)
# → {"Gmail": {"opened": 45, "unopened": 120, ...}, "Hotmail": {...}, "Yahoo": {...}, "Others": {...}}

# Estadísticas por rango de fechas (para una LISTA, no una campaña)
from datetime import datetime
stats = client.get_stats_by_date(
    list_id=1138335,
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
)
# → {"total_sent": 5000, "opened": 1200, "unique_clicks": 450, "hard_bounces": 30, ...}
# NOTA: toma list_id (no campaign_id) y devuelve totales del período (no por fecha)
```

### Envío con template

```python
# Enviar una campaña usando un template existente
campaign = client.send_template_campaign(
    name="Newsletter con template",
    subject="Asunto del email",
    template_id=9493654,
    list_ids=[1138335],
    from_email="sender@domain.com",  # opcional si hay default
    from_name="Mi Empresa",           # opcional si hay default
)
```

### SMTP

```python
# Créditos SMTP disponibles
credits = client.get_smtp_credits()
# → 499923 (int)
# Quirk: la API devuelve {"Creditos": int} con C mayúscula — el SDK lo normaliza

# Los siguientes requieren plan SMTP activado (retornan 401 sin él):
# client.send_single_email(to_email, subject, content, ...)
# client.send_emails(...)
# client.send_certified_email(...)
# client.get_email_status(email_id)
```

---

## Métodos NO funcionales (bugs del servidor)

| Método | Error | Estado |
|--------|-------|--------|
| `get_list_segments(list_id)` | 404 — endpoint no existe en el servidor | Inutilizable |
| `get_list_subs_stats(list_id)` | Timeout — el servidor no responde | Inutilizable |
| `get_templates_by_name(name)` | 404 — documentado pero no implementado | Inutilizable (emite UserWarning) |
| `batch_delete_subscribers(...)` | 500 — bug del servidor | Implementado, pero falla |

---

## Output Format & jq

```bash
# IDs de todas las listas
acumbamail lists list | jq '[.[].id]'

# Buscar lista por nombre
acumbamail lists list | jq '.[] | select(.name == "Newsletter")'

# Ver solo IDs de campañas (el list solo devuelve id+name)
acumbamail campaigns list | jq '[.[].id]'

# Tasa de apertura
acumbamail campaigns stats --campaign-id 999 | \
  jq '.opened / .total_delivered * 100 | round | tostring + "%"'

# Suscriptores activos de una lista
acumbamail subscribers list --list-id 123 | jq '[.[] | select(.is_active == true)]'
```

## Common Workflows

### Importar suscriptores desde CSV

```bash
python3 -c "
import csv, json, sys
rows = list(csv.DictReader(sys.stdin))
print(json.dumps(rows))
" < subs.csv > subs.json

acumbamail subscribers batch-add --list-id 123 --file subs.json --update
```

### Newsletter completa (crear + enviar + ver stats)

```bash
# 1. Crear y enviar
acumbamail campaigns create \
  --name "Newsletter $(date +%Y-%m-%d)" \
  --subject "Novedades de esta semana" \
  --html-file newsletter.html \
  --list-id 1138335 \
  --from-email sender@domain.com \
  | jq '{id: .id, name: .name}'

# 2. Ver stats 24h después
acumbamail campaigns stats --campaign-id CAMPAIGN_ID | \
  jq '{open_rate: (.opened / .total_delivered * 100 | round | tostring + "%"),
       click_rate: (.unique_clicks / .total_delivered * 100 | round | tostring + "%")}'
```

### Instalar skills

```bash
acumbamail install-skills      # localmente
acumbamail install-skills -g   # globalmente (~/.claude/skills/)
```
