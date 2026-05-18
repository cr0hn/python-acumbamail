#!/usr/bin/env python3
"""
Ejemplo de uso del cliente asíncrono de Acumbamail.

Equivalente al sync_example.py pero usando async/await con AsyncAcumbamailClient.
El cliente se puede usar como context manager (recomendado) o cerrarlo manualmente.
"""

import asyncio
import os
from acumbamail import AsyncAcumbamailClient

# ID de lista de prueba; cámbialo por el tuyo
TEST_LIST_ID = 1138335


async def main():
    """Uso recomendado: context manager que cierra el cliente al salir."""
    async with AsyncAcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Acumbamail SDK",
        default_sender_email="sdk@example.com"
    ) as client:

        # --- Listar listas ---
        print("Obteniendo listas de correo...")
        lists = await client.get_lists()
        print(f"Total de listas: {len(lists)}")
        for mail_list in lists:
            print(f"  - {mail_list.name} (ID: {mail_list.id})")

        # --- Añadir suscriptor ---
        # AVISO: esta operación modifica datos en tu cuenta
        print("\nAñadiendo suscriptor de prueba...")
        subscriber = await client.add_subscriber(
            email="async-test@example.com",
            list_id=TEST_LIST_ID,
            fields={"name": "Async Test User"}
        )
        print(f"Suscriptor añadido: {subscriber.email}")

        # --- Obtener suscriptores ---
        print("\nObteniendo suscriptores de la lista...")
        subscribers = await client.get_subscribers(TEST_LIST_ID)
        print(f"Total de suscriptores: {len(subscribers)}")

        # --- Crear campaña ---
        # AVISO: esta operación crea una campaña en tu cuenta
        # El contenido DEBE incluir *|UNSUBSCRIBE_URL|* o la API rechazará la petición
        print("\nCreando campaña de prueba...")
        campaign = await client.create_campaign(
            name="Campaña Async de Prueba SDK",
            subject="Hola desde Acumbamail SDK (async)",
            content=(
                "<h1>Hola!</h1>"
                "<p>Este email fue creado con el cliente asíncrono del SDK de Acumbamail.</p>"
                "<p><a href='*|UNSUBSCRIBE_URL|*'>Darse de baja</a></p>"
            ),
            list_ids=[TEST_LIST_ID],
            from_name="Acumbamail SDK",
            from_email="sdk@example.com"
        )
        print(f"Campaña creada: {campaign.name} (ID: {campaign.id})")

        # --- Estadísticas de campaña ---
        print("\nObteniendo estadísticas de la campaña...")
        stats = await client.get_campaign_total_information(campaign.id)
        total = stats.total_delivered
        if total > 0:
            open_rate = stats.opened / total * 100
            click_rate = stats.unique_clicks / total * 100
            print(f"  Entregados: {total}")
            print(f"  Abiertos:   {stats.opened} ({open_rate:.1f}%)")
            print(f"  Clics:      {stats.unique_clicks} ({click_rate:.1f}%)")
        else:
            print("  La campaña aún no tiene estadísticas disponibles.")


async def usage_without_context_manager():
    """
    Alternativa sin context manager: hay que cerrar el cliente manualmente.
    Útil cuando el ciclo de vida del cliente lo gestiona el llamador.
    """
    client = AsyncAcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Acumbamail SDK",
        default_sender_email="sdk@example.com"
    )

    try:
        templates = await client.get_templates()
        print(f"Templates disponibles: {len(templates)}")
        for tmpl in templates:
            print(f"  - {tmpl.name} (ID: {tmpl.id})")
    finally:
        # Siempre cerrar el cliente al terminar
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

    print("\n" + "=" * 50)
    print("Ejemplo alternativo sin context manager:")
    asyncio.run(usage_without_context_manager())
