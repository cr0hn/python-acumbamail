#!/usr/bin/env python3
"""
Ejemplo básico de uso del cliente síncrono de Acumbamail.

Muestra las operaciones más comunes:
- Obtener listas
- Añadir suscriptores
- Obtener suscriptores
- Crear campañas (con UNSUBSCRIBE_URL obligatorio)
- Obtener estadísticas de una campaña
"""

import os
from acumbamail import AcumbamailClient

# ID de lista de prueba; cámbialo por el tuyo
TEST_LIST_ID = 1138335

def main():
    # El token se lee de la variable de entorno ACUMBAMAIL_TOKEN
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Acumbamail SDK",
        default_sender_email="sdk@example.com"
    )

    # --- Listar listas ---
    print("Obteniendo listas de correo...")
    lists = client.get_lists()
    print(f"Total de listas: {len(lists)}")
    for mail_list in lists:
        print(f"  - {mail_list.name} (ID: {mail_list.id})")

    # --- Añadir suscriptor ---
    # AVISO: esta operación modifica datos en tu cuenta
    print("\nAñadiendo suscriptor de prueba...")
    subscriber = client.add_subscriber(
        email="test@example.com",
        list_id=TEST_LIST_ID,
        fields={"name": "Test User"}
    )
    print(f"Suscriptor añadido: {subscriber.email}")

    # --- Obtener suscriptores ---
    print("\nObteniendo suscriptores de la lista...")
    subscribers = client.get_subscribers(TEST_LIST_ID)
    print(f"Total de suscriptores: {len(subscribers)}")

    # --- Crear campaña ---
    # AVISO: esta operación crea una campaña en tu cuenta
    # El contenido DEBE incluir *|UNSUBSCRIBE_URL|* o la API rechazará la petición
    print("\nCreando campaña de prueba...")
    campaign = client.create_campaign(
        name="Campaña de Prueba SDK",
        subject="Hola desde Acumbamail SDK",
        content=(
            "<h1>Hola!</h1>"
            "<p>Este es un email de prueba enviado con el SDK de Acumbamail.</p>"
            "<p><a href='*|UNSUBSCRIBE_URL|*'>Darse de baja</a></p>"
        ),
        list_ids=[TEST_LIST_ID],
        from_name="Acumbamail SDK",
        from_email="sdk@example.com"
    )
    print(f"Campaña creada: {campaign.name} (ID: {campaign.id})")

    # --- Estadísticas de campaña ---
    print("\nObteniendo estadísticas de la campaña...")
    stats = client.get_campaign_total_information(campaign.id)
    total = stats.total_delivered
    if total > 0:
        open_rate = stats.opened / total * 100
        click_rate = stats.unique_clicks / total * 100
        print(f"  Entregados: {total}")
        print(f"  Abiertos:   {stats.opened} ({open_rate:.1f}%)")
        print(f"  Clics:      {stats.unique_clicks} ({click_rate:.1f}%)")
    else:
        print("  La campaña aún no tiene estadísticas disponibles.")


if __name__ == "__main__":
    main()
