#!/usr/bin/env python3
"""
Ejemplo de workflows automatizados con el SDK de Acumbamail.

Muestra cómo:
- Crear una lista y añadir suscriptores en lote
- Crear una campaña asociada a esa lista
- Consultar estadísticas de la campaña
- Configurar un webhook para recibir eventos de la lista

AVISO: Este ejemplo crea listas, suscriptores y campañas reales en tu cuenta.
"""

import os
from acumbamail import AcumbamailClient

# Contenido de campaña — DEBE incluir *|UNSUBSCRIBE_URL|* o la API lo rechazará
WELCOME_CONTENT = """
<h1>Bienvenido/a a nuestra comunidad</h1>
<p>Gracias por suscribirte. En los próximos días recibirás:</p>
<ul>
    <li>Novedades y actualizaciones del producto</li>
    <li>Contenido exclusivo para suscriptores</li>
    <li>Acceso anticipado a nuevas funcionalidades</li>
</ul>
<p>Si tienes cualquier pregunta, responde a este correo.</p>
<p style="margin-top:24px; font-size:12px; color:#888;">
    <a href="*|UNSUBSCRIBE_URL|*">Darse de baja</a>
</p>
"""


def create_list_with_subscribers(client: AcumbamailClient):
    """
    Crea una lista nueva y añade suscriptores en lote.
    AVISO: operación destructiva — crea datos en la cuenta.
    """
    print("Creando lista de bienvenida...")
    mail_list = client.create_list(
        name="Workflow — Lista de Bienvenida",
        description="Lista creada por el ejemplo de automated_workflows.py"
    )
    print(f"  Lista creada: {mail_list.name} (ID: {mail_list.id})")

    # Añadir suscriptores en lote
    subscribers_data = [
        {"email": "workflow001@example.com", "name": "Workflow User 1"},
        {"email": "workflow002@example.com", "name": "Workflow User 2"},
        {"email": "workflow003@example.com", "name": "Workflow User 3"},
    ]

    print(f"Añadiendo {len(subscribers_data)} suscriptores en lote...")
    results = client.batch_add_subscribers(
        list_id=mail_list.id,
        subscribers_data=subscribers_data
    )
    print(f"  Procesados: {len(results)} suscriptores")

    return mail_list


def create_welcome_campaign(client: AcumbamailClient, list_id: int):
    """
    Crea una campaña de bienvenida para la lista indicada.
    AVISO: operación destructiva — crea una campaña en la cuenta.
    """
    print("\nCreando campaña de bienvenida...")
    campaign = client.create_campaign(
        name="Workflow — Email de Bienvenida",
        subject="Bienvenido/a a nuestra comunidad",
        content=WELCOME_CONTENT,
        list_ids=[list_id],
        from_name="Acumbamail SDK",
        from_email="sdk@example.com"
    )
    print(f"  Campaña creada: {campaign.name} (ID: {campaign.id})")
    return campaign


def check_campaign_stats(client: AcumbamailClient, campaign_id: int) -> None:
    """Muestra las estadísticas de la campaña."""
    print(f"\nEstadísticas de campaña ID {campaign_id}:")
    stats = client.get_campaign_total_information(campaign_id)
    print(f"  Entregados:   {stats.total_delivered:,}")
    print(f"  Abiertos:     {stats.opened:,}")
    print(f"  Clics únicos: {stats.unique_clicks:,}")
    print(f"  Hard bounces: {stats.hard_bounces:,}")
    print(f"  Bajas:        {stats.unsubscribes:,}")


def configure_list_webhook(client: AcumbamailClient, list_id: int) -> None:
    """
    Configura un webhook para recibir eventos de la lista (suscripciones, bajas, etc.).
    Cambia WEBHOOK_URL por la URL real de tu servidor antes de ejecutar.
    """
    WEBHOOK_URL = "https://tu-servidor.com/acumbamail/webhook"

    print(f"\nConfigurando webhook para lista ID {list_id}...")
    print(f"  URL: {WEBHOOK_URL}")
    print("  Nota: cambia WEBHOOK_URL por la URL real de tu servidor.")

    # Descomentar para configurar el webhook realmente:
    # webhook = client.config_list_webhook(
    #     list_id=list_id,
    #     callback_url=WEBHOOK_URL,
    #     subscribes=True,       # notificar nuevas suscripciones
    #     unsubscribes=True,     # notificar bajas
    #     hard_bounce=True,      # notificar hard bounces
    #     soft_bounce=False,
    #     complain=False,
    #     opens=False,
    #     click=False,
    #     active=True
    # )
    # print(f"  Webhook configurado (ID: {webhook.id})")

    # Leer webhook actual de la lista
    try:
        current = client.get_list_webhook(list_id)
        if current:
            print(f"  Webhook actual: {current.url} (activo: {current.active})")
        else:
            print("  No hay webhook configurado en esta lista.")
    except Exception as e:
        print(f"  No se pudo leer el webhook: {e}")


def main():
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Acumbamail SDK",
        default_sender_email="sdk@example.com"
    )

    print("Workflows automatizados con Acumbamail SDK")
    print("=" * 50)
    print("AVISO: Este ejemplo crea listas, suscriptores y campañas en tu cuenta.\n")

    # 1. Crear lista y añadir suscriptores
    mail_list = create_list_with_subscribers(client)

    # 2. Crear campaña de bienvenida
    campaign = create_welcome_campaign(client, mail_list.id)

    # 3. Ver estadísticas (estarán a 0 hasta que la campaña se envíe)
    check_campaign_stats(client, campaign.id)

    # 4. Configurar webhook (comentado por defecto)
    configure_list_webhook(client, mail_list.id)

    print("\nEjemplo completado.")


if __name__ == "__main__":
    main()
