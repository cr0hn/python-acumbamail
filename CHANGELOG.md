# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2026-05-18] - Migrar CI/CD de Poetry a uv con Trusted Publishing; actualizar README

### Changed

- `.github/workflows/publish-to-pypi.yaml`: reescrito para usar `uv` en lugar de Poetry
  - Separado en dos jobs: `test` y `publish`; Trusted Publishing (OIDC) vía `pypa/gh-action-pypi-publish@release/v1`
  - Python actualizado de 3.11 a 3.13; uv vía `astral-sh/setup-uv@v4`
- `README.md`: nueva sección CLI, Features ampliada, Core Methods con 25+ métodos nuevos, sección OpenAPI/Postman

## [2026-05-18] - SDK improvements: nuevos parámetros y eliminación de dead code

### Added

- `add_subscriber`: `double_optin: bool = False`, `update_subscriber: bool = False`
- `get_subscribers`: `block_index: int = 0`, `all_fields: bool = False`, `complete_json: bool = False`
- `get_list_subs_stats`: `block_index: int = 0`
- 22 tests nuevos cubriendo los nuevos parámetros (sync + async)

### Removed

- `utils.py`: eliminadas 8 funciones dead code

## [2026-05-18] - Tests para métodos originales del SDK (pre-sesión)

### Added

- `tests/test_client_original.py`: 85 tests del cliente síncrono (get_lists, create_list, get_subscribers, add_subscriber, delete_subscriber, create_campaign, send_single_email, get_templates, create_template, y más)
- `tests/test_aclient_original.py`: 80 tests del cliente asíncrono (espejo del síncrono)

## [2026-05-18] - Tests de calidad y contract testing del OpenAPI spec

### Added

- `tests/test_openapi_structure.py`: 16 tests de validación estructural del YAML (sin red)
  - Validación oficial OpenAPI 3.0.3, tags, paths, schemas, $ref internos, conteos
- `tests/test_openapi_coverage.py`: 7 tests de cobertura spec vs SDK (sin red)
  - Verifica que todos los endpoints del SDK están en el spec y viceversa
  - Documenta endpoints SDK pendientes de spec (`getTemplatesByName`)
- `tests/test_contracts.py`: 27 tests de contract testing real contra la API
  - Listas, suscriptores, campañas, templates, webhooks, SMTP
  - Marcados con `@pytest.mark.contract`, excluidos por defecto del `uv run pytest`
- Configuración `pyproject.toml`: marker `contract` + `addopts = "-m 'not contract'"`

### Fixed

- `acumbamail-openapi.yaml`: corregido schema `ListStatsResponse`
  - Eliminado campo `campaigns_sent` (la API real no lo devuelve)
  - Añadidos campos reales: `spam_subscribers`, `name`, `create_date`
  - `campaigns_sent` era requerido en el spec pero nunca aparece en respuestas reales

### Discovered (API quirks documentados por contract testing)

- `getCampaigns`: devuelve lista de dicts `{campaign_id_str: campaign_name}`, NO una lista de objetos con campo `id`
- `getCampaignOpenersByBrowser` / `getCampaignOpenersByOs`: devuelven `[]` (lista vacía) cuando no hay openers, no `{}` (dict vacío)
- `getTemplatesByName`: presente en el SDK pero sin documentar en el spec (pendiente)

## [2026-05-18] - OpenAPI spec completo de la API Acumbamail

### Added

- Creado `acumbamail-openapi.yaml`: especificación OpenAPI 3.0.3 completa de la API de Acumbamail
- 47 endpoints documentados agrupados en 6 tags: Lists, Subscribers, Campaigns, Templates, SMTP, Webhooks
- Schemas reutilizables: `AuthFields`, `ListInfo`, `SubscriberDetails`, `InactiveSubscriberFull`, `CampaignTotalInfo`, `CampaignClick`, `CampaignOpener`, `SMTPWebhookInfo`, `ListWebhookInfo`, etc.
- Ejemplos reales en los schemas y respuestas
- Documentación de comportamientos especiales: bug conocido en `batchDeleteSubscribers` (HTTP 500), clave `Creditos` con mayúscula en `getCreditsSMTP`, `template_id` como string en `duplicateTemplate`, requerimiento de SMTP activo para endpoints de envío
- Extension `x-rate-limit: "10 requests/minute"` en cada operación
- Descripciones completas de todos los códigos HTTP de respuesta (200, 201, 400, 401, 404, 429, 500)

## [2026-05-18] - Postman collection completa con todos los endpoints

### Added

- Actualizada `Acumbamail.postman_collection.json` con todos los endpoints de la API:
  - **Subscribers** (21 endpoints): getLists, createList, deleteList, getListStats, getListFields, getFields, getForms, getListSegments, getListSubsStats, getMergeFields, getSubscribers, addSubscriber, deleteSubscriber, batchAddSubscribers, batchDeleteSubscribers, deleteAllSubscribers, unsubscribeSubscriber, getSubscriberDetails, searchSubscriber, getInactiveSubscribers, addMergeTag, getCreditsSMTP
  - **Campaigns** (17 endpoints): createCampaign, sendTemplateCampaign, getCampaigns, getCampaignBasicInformation, getCampaignTotalInformation, getCampaignClicks, getCampaignOpeners, getCampaignOpenersByBrowser, getCampaignOpenersByOs, getCampaignOpenersByCountries, getCampaignInformationByISP, getCampaignLinks, getCampaignSoftBounces, getStatsByDate, getTemplates, createTemplate, duplicateTemplate
  - **SMTP** (4 endpoints, nuevo folder): sendOne, send, sendCertifiedEmail, getEmailStatus
  - **Webhooks** (4 endpoints, nuevo folder): getSMTPWebhook, configSMTPWebhook, getListWebhook, configListWebhook
- Añadida variable `template_id` a las variables de la collection
- Todos los requests incluyen `response_type: "json"` en el body
- Corregidas URLs incorrectas en requests existentes (getListSegments, getListSubsStats apuntaban a endpoints equivocados)

## [2026-05-18] - CLI: comandos de suscriptores, campañas y webhooks

### Added

- Implementado `acumbamail/cli/commands/subscribers.py` con comandos: `list`, `add`, `delete`, `search`, `unsubscribe`, `batch-add`
- Implementado `acumbamail/cli/commands/campaigns.py` con comandos: `list`, `info`, `stats`
- Implementado `acumbamail/cli/commands/webhooks.py` con comandos: `smtp-get`, `smtp-config`, `list-get`, `list-config`
- Añadidos 13 tests TDD en `tests/test_cli.py` (clases `TestSubscribersCommands`, `TestCampaignsCommands`, `TestWebhooksCommands`) — total 118 tests pasando

## [2026-05-18] - CLI: comandos de listas y main.py inicial

### Added

- Creado `acumbamail/cli/main.py` con la aplicación Typer principal y soporte para opción global `--token`
- Creado `acumbamail/cli/commands/lists.py` con comandos: `list`, `create`, `delete`, `stats`
- Creados placeholders `acumbamail/cli/commands/subscribers.py`, `campaigns.py`, `webhooks.py`
- Añadidos 4 tests en `tests/test_cli.py` (clase `TestListsCommands`) — total 105 tests pasando

## [2026-05-18] - nuevos métodos en AsyncAcumbamailClient y tests async

### Added

- Añadidos 22 nuevos métodos al cliente asíncrono `AsyncAcumbamailClient` en `acumbamail/aclient.py`, equivalentes a los del cliente síncrono:
  - **Suscriptores**: `add_merge_tag`, `batch_add_subscribers`, `batch_delete_subscribers`, `delete_all_subscribers`, `delete_list`, `get_smtp_credits`, `get_fields`, `get_forms`, `get_inactive_subscribers`, `get_subscriber_details`, `search_subscriber`, `unsubscribe_subscriber`
  - **Campañas**: `send_template_campaign`, `duplicate_template`, `get_campaign_openers_by_countries`, `get_templates_by_name`
  - **SMTP**: `send_emails`, `send_certified_email`, `get_email_status`
  - **Webhooks**: `get_smtp_webhook`, `get_list_webhook`, `config_smtp_webhook`, `config_list_webhook`
- Añadidos imports de `BatchSubscriberResult`, `SubscriberDetails`, `InactiveSubscriber`, `SMTPWebhook`, `ListWebhook` al bloque de imports de `.models` en `aclient.py`
- Creado `tests/test_aclient_new_methods.py` con 43 tests async cubriendo todos los nuevos métodos

## [2026-05-18] - nuevos métodos en AcumbamailClient

### Added

- Añadidos 28 nuevos métodos al cliente síncrono `AcumbamailClient` en `acumbamail/client.py`:
  - **Suscriptores**: `add_merge_tag`, `batch_add_subscribers`, `batch_delete_subscribers`, `delete_all_subscribers`, `delete_list`, `get_smtp_credits`, `get_fields`, `get_forms`, `get_inactive_subscribers`, `get_subscriber_details`, `search_subscriber`, `unsubscribe_subscriber`
  - **Campañas**: `send_template_campaign`, `duplicate_template`, `get_campaign_openers_by_countries`, `get_templates_by_name`
  - **SMTP**: `send_emails`, `send_certified_email`, `get_email_status`
  - **Webhooks**: `get_smtp_webhook`, `get_list_webhook`, `config_smtp_webhook`, `config_list_webhook`
- Añadidos imports de `BatchSubscriberResult`, `SubscriberDetails`, `InactiveSubscriber`, `SMTPWebhook`, `ListWebhook` al bloque de imports de `.models` en `client.py`

## [2026-05-18] - models nuevos

### Added

- Añadidos 5 nuevos dataclasses en `acumbamail/models.py`:
  - `SubscriberDetails`: datos completos de un suscriptor (de `getSubscriberDetails` y `searchSubscriber`), con campos extra en `fields`
  - `InactiveSubscriber`: suscriptor inactivo (de `getInactiveSubscribers`), con `reason` y `reason_date` opcionales
  - `SMTPWebhook`: configuración de webhook SMTP (de `getSMTPWebhook`)
  - `ListWebhook`: configuración de webhook de lista (de `getListWebhook`), con `subscribes` y `unsubscribes`
  - `BatchSubscriberResult`: resultado de alta por lotes (de `batchAddSubscribers`)
- Actualizados `__all__` con los nuevos modelos

## [2026-05-18]

### Changed

- Migrado el sistema de gestión de dependencias de Poetry a uv
- Versión mínima de Python elevada de 3.11 a 3.13
- Cambiado build backend de `poetry-core` a `hatchling`
- Eliminado `poetry.lock`, generado `uv.lock`

## [0.1.0] - 2024-03-21

### Added

- Initial release
- Basic plugin system
- OpenAPI importer plugin
- JWT tester plugin
- HTML reporter plugin
- Configuration system
- Progress tracking
- Storage backend system
