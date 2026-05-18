# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
