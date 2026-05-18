#!/usr/bin/env python3
"""
Ejemplo de operaciones en masa con el SDK de Acumbamail.

Muestra cómo:
- Añadir múltiples suscriptores de golpe con batch_add_subscribers
- Buscar suscriptores con search_subscriber
- Obtener suscriptores inactivos con get_inactive_subscribers

AVISO: batch_add_subscribers modifica datos en tu cuenta.
"""

import os
from datetime import date
from acumbamail import AcumbamailClient

# ID de lista de prueba; cámbialo por el tuyo
TEST_LIST_ID = 1138335


def demo_batch_add(client: AcumbamailClient) -> None:
    """
    Añade varios suscriptores en una sola llamada a la API.
    Más eficiente que llamar add_subscriber en bucle.

    AVISO: Esta operación añade suscriptores a la lista indicada.
    """
    print("Añadiendo suscriptores en lote (batch_add_subscribers)...")

    # Cada elemento es un dict con 'email' y opcionalmente campos extra
    subscribers_data = [
        {"email": "batch001@example.com", "name": "Batch User 1", "company": "Acme Corp"},
        {"email": "batch002@example.com", "name": "Batch User 2", "company": "Tech Solutions"},
        {"email": "batch003@example.com", "name": "Batch User 3", "company": "Global Inc"},
        {"email": "batch004@example.com", "name": "Batch User 4", "company": "Startup Ltd"},
        {"email": "batch005@example.com", "name": "Batch User 5", "company": "Enterprise Co"},
    ]

    results = client.batch_add_subscribers(
        list_id=TEST_LIST_ID,
        subscribers_data=subscribers_data,
        update_subscriber=True  # Actualiza si el suscriptor ya existe
    )

    print(f"  Suscriptores procesados: {len(results)}")
    for result in results:
        print(f"  - {result.email} (subscriber_id: {result.subscriber_id})")


def demo_search_subscriber(client: AcumbamailClient) -> None:
    """Busca un suscriptor por email en toda la cuenta."""
    print("\nBuscando suscriptor (search_subscriber)...")

    # Busca en todas las listas de la cuenta
    results = client.search_subscriber("batch001@example.com")
    if results:
        if isinstance(results, list):
            for sub in results:
                print(f"  Encontrado: {sub.email} | Estado: {sub.status}")
        else:
            print(f"  Encontrado: {results.email} | Estado: {results.status}")
    else:
        print("  Suscriptor no encontrado.")


def demo_inactive_subscribers(client: AcumbamailClient) -> None:
    """
    Obtiene suscriptores inactivos en un rango de fechas.
    Con full_info=True devuelve razón y fecha de inactividad.
    """
    print("\nObteniendo suscriptores inactivos (get_inactive_subscribers)...")

    date_from = "2024-01-01"
    date_to = date.today().isoformat()

    inactive = client.get_inactive_subscribers(
        date_from=date_from,
        date_to=date_to,
        full_info=True  # Incluye razón e fecha de inactividad
    )

    if inactive:
        print(f"  Inactivos encontrados: {len(inactive)}")
        for sub in inactive[:5]:  # Mostrar solo los primeros 5
            reason = getattr(sub, "reason", "N/A")
            reason_date = getattr(sub, "reason_date", "N/A")
            print(f"  - {sub.email} | Razón: {reason} | Fecha: {reason_date}")
        if len(inactive) > 5:
            print(f"  ... y {len(inactive) - 5} más")
    else:
        print(f"  No hay inactivos entre {date_from} y {date_to}.")


def main():
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Bulk Operations SDK",
        default_sender_email="bulk@example.com"
    )

    print("Operaciones en masa con Acumbamail SDK")
    print("=" * 50)

    demo_batch_add(client)
    demo_search_subscriber(client)
    demo_inactive_subscribers(client)

    print("\nEjemplo completado.")


if __name__ == "__main__":
    main()
