#!/usr/bin/env python3
"""
Ejemplo de manejo de errores con el SDK de Acumbamail.

Muestra cómo capturar y gestionar los distintos tipos de excepción:
- AcumbamailValidationError  — datos de entrada inválidos (email malformado, etc.)
- AcumbamailAPIError         — error devuelto por la API de Acumbamail
- AcumbamailRateLimitError   — límite de peticiones excedido (429)
- AcumbamailError            — clase base para todos los errores del SDK

También muestra degradación elegante y separación de errores en operaciones en lote.
"""

import os
import logging
from acumbamail import (
    AcumbamailClient,
    AcumbamailError,
    AcumbamailRateLimitError,
    AcumbamailAPIError,
    AcumbamailValidationError,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ID de lista de prueba; cámbialo por el tuyo
TEST_LIST_ID = 1138335


def demo_invalid_email(client: AcumbamailClient) -> None:
    """
    Intenta añadir un email inválido.
    El SDK lanza AcumbamailValidationError antes de llamar a la API.
    """
    print("\n--- Email inválido ---")
    try:
        client.add_subscriber(
            email="esto-no-es-un-email",
            list_id=TEST_LIST_ID
        )
    except AcumbamailValidationError as e:
        print(f"  ValidationError (esperado): {e}")
    except AcumbamailAPIError as e:
        # La API también puede rechazarlo si el SDK no lo filtra
        print(f"  APIError: {e}")


def demo_campaign_without_unsubscribe(client: AcumbamailClient) -> None:
    """
    Intenta crear una campaña sin *|UNSUBSCRIBE_URL|* en el contenido.
    La API de Acumbamail requiere este tag; el SDK lo valida antes de enviar.
    """
    print("\n--- Campaña sin UNSUBSCRIBE_URL ---")
    try:
        client.create_campaign(
            name="Campaña sin unsubscribe",
            subject="Test",
            content="<h1>Hola</h1><p>Sin enlace de baja.</p>",  # Falta *|UNSUBSCRIBE_URL|*
            list_ids=[TEST_LIST_ID],
            from_name="SDK",
            from_email="sdk@example.com"
        )
        print("  ATENCIÓN: la campaña se creó sin UNSUBSCRIBE_URL (el SDK no validó este caso)")
    except AcumbamailValidationError as e:
        print(f"  ValidationError (esperado): {e}")
    except AcumbamailAPIError as e:
        print(f"  APIError desde la API: {e}")


def demo_specific_exception_types(client: AcumbamailClient) -> None:
    """
    Muestra el orden correcto de captura de excepciones del SDK.
    Las más específicas deben ir antes que la clase base.
    """
    print("\n--- Orden de captura de excepciones ---")
    try:
        lists = client.get_lists()
        print(f"  Listas obtenidas: {len(lists)}")

    except AcumbamailValidationError as e:
        # Error de validación de entrada (p.ej. token vacío, parámetros inválidos)
        logger.error("Validación fallida: %s", e)

    except AcumbamailRateLimitError as e:
        # HTTP 429 — el SDK ya incluye reintentos automáticos (3x con backoff de 10s)
        logger.warning("Rate limit superado: %s", e)

    except AcumbamailAPIError as e:
        # Cualquier otro error HTTP de la API
        logger.error("Error de API: %s", e)

    except AcumbamailError as e:
        # Clase base — captura lo que no cubran los anteriores
        logger.error("Error del SDK: %s", e)

    except Exception as e:
        # Errores inesperados (red, timeout, etc.)
        logger.exception("Error inesperado: %s", e)


def demo_graceful_degradation(client: AcumbamailClient) -> None:
    """
    Muestra degradación elegante: si la operación principal falla,
    intenta una alternativa antes de rendirse.
    """
    print("\n--- Degradación elegante ---")

    # Intentar crear campaña con lista inexistente
    try:
        campaign = client.create_campaign(
            name="Campaña degradación",
            subject="Prueba",
            content="<p>Prueba.</p><p><a href='*|UNSUBSCRIBE_URL|*'>Baja</a></p>",
            list_ids=[999999999],  # Lista que probablemente no existe
            from_name="SDK",
            from_email="sdk@example.com"
        )
        print(f"  Campaña creada (ID: {campaign.id})")

    except (AcumbamailValidationError, AcumbamailAPIError) as e:
        print(f"  Fallo principal: {e}")
        print("  Ejecutando estrategia alternativa: enviar email individual...")

        try:
            email_id = client.send_single_email(
                to_email="fallback@example.com",
                subject="Email de prueba (fallback)",
                content="<p>Email enviado como alternativa.</p>"
            )
            print(f"  Email individual enviado (ID: {email_id})")
        except Exception as fallback_error:
            print(f"  El fallback también falló: {fallback_error}")


def demo_bulk_with_partial_errors(client: AcumbamailClient) -> None:
    """
    Operación en lote con entradas válidas e inválidas mezcladas.
    Muestra cómo continuar procesando aunque algunos elementos fallen.
    """
    print("\n--- Lote con errores parciales ---")

    emails = [
        ("user1@example.com", {"name": "User 1"}),
        ("no-es-email",       {"name": "Inválido"}),   # falla
        ("user2@example.com", {"name": "User 2"}),
        ("",                  {"name": "Vacío"}),        # falla
        ("user3@example.com", {"name": "User 3"}),
    ]

    ok = 0
    ko = 0

    for email, fields in emails:
        try:
            client.add_subscriber(email=email, list_id=TEST_LIST_ID, fields=fields)
            print(f"  OK: {email}")
            ok += 1
        except AcumbamailValidationError as e:
            print(f"  ValidationError: {email!r} — {e}")
            ko += 1
        except AcumbamailAPIError as e:
            print(f"  APIError: {email!r} — {e}")
            ko += 1

    print(f"\n  Resultado: {ok} correctos, {ko} errores de {len(emails)} entradas")


def main():
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Error Handling SDK",
        default_sender_email="errors@example.com"
    )

    print("Manejo de errores con Acumbamail SDK")
    print("=" * 50)

    demo_invalid_email(client)
    demo_campaign_without_unsubscribe(client)
    demo_specific_exception_types(client)
    demo_graceful_degradation(client)
    demo_bulk_with_partial_errors(client)

    print("\n" + "=" * 50)
    print("Resumen de buenas prácticas:")
    print("  1. Captura excepciones específicas antes de la clase base.")
    print("  2. AcumbamailRateLimitError: el SDK reintenta automáticamente (3x).")
    print("  3. Incluye siempre *|UNSUBSCRIBE_URL|* en el contenido de campañas.")
    print("  4. En operaciones en lote, continúa procesando tras errores parciales.")
    print("  5. Usa degradación elegante para mantener la disponibilidad.")


if __name__ == "__main__":
    main()
