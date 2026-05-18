#!/usr/bin/env python3
"""
Ejemplo de A/B testing con el SDK de Acumbamail.

Muestra cómo crear dos campañas con distintos subjects para la misma lista
y comparar sus estadísticas para determinar el ganador.

AVISO: Este ejemplo crea campañas reales en tu cuenta.
Las campañas se crean pero NO se envían automáticamente.
"""

import os
from typing import Optional
from acumbamail import AcumbamailClient
from acumbamail.models import CampaignTotalInformation

# ID de lista de prueba; cámbialo por el tuyo
TEST_LIST_ID = 1138335

# Contenido compartido para ambas variantes
# OBLIGATORIO: debe incluir *|UNSUBSCRIBE_URL|* o la API rechazará la petición
SHARED_CONTENT = """
<h1>Nuevas funcionalidades disponibles</h1>
<p>Nos complace anunciar el lanzamiento de varias mejoras en nuestra plataforma:</p>
<ul>
    <li><strong>Dashboard mejorado</strong> — más rápido y personalizable</li>
    <li><strong>Analytics avanzados</strong> — toma decisiones basadas en datos</li>
    <li><strong>Mejor experiencia móvil</strong> — diseño responsive optimizado</li>
</ul>
<p>Prueba las novedades y cuéntanos qué te parecen.</p>
<p style="margin-top:24px; font-size:12px; color:#888;">
    <a href="*|UNSUBSCRIBE_URL|*">Darse de baja</a>
</p>
"""


def create_ab_campaigns(client: AcumbamailClient):
    """Crea dos campañas con subjects distintos para A/B testing."""

    print("Creando variante A...")
    campaign_a = client.create_campaign(
        name="AB Test — Variante A",
        subject="¡Nuevas funcionalidades ya disponibles!",
        content=SHARED_CONTENT,
        list_ids=[TEST_LIST_ID],
        from_name="Acumbamail SDK",
        from_email="sdk@example.com"
    )
    print(f"  Variante A creada (ID: {campaign_a.id}): {campaign_a.subject}")

    print("Creando variante B...")
    campaign_b = client.create_campaign(
        name="AB Test — Variante B",
        subject="¿Quieres ver qué hay de nuevo?",
        content=SHARED_CONTENT,
        list_ids=[TEST_LIST_ID],
        from_name="Acumbamail SDK",
        from_email="sdk@example.com"
    )
    print(f"  Variante B creada (ID: {campaign_b.id}): {campaign_b.subject}")

    return campaign_a, campaign_b


def get_variant_metrics(client: AcumbamailClient, campaign_id: int) -> Optional[CampaignTotalInformation]:
    """Obtiene las métricas de una campaña."""
    try:
        return client.get_campaign_total_information(campaign_id)
    except Exception as e:
        print(f"  Error obteniendo métricas para campaña {campaign_id}: {e}")
        return None


def compare_variants(
    stats_a: Optional[CampaignTotalInformation],
    stats_b: Optional[CampaignTotalInformation],
    name_a: str = "Variante A",
    name_b: str = "Variante B"
) -> None:
    """Compara las estadísticas de dos variantes y determina el ganador."""

    print("\nComparación A/B:")
    print("=" * 50)

    for name, stats in [(name_a, stats_a), (name_b, stats_b)]:
        if stats is None:
            print(f"{name}: sin datos disponibles")
            continue

        total = stats.total_delivered
        if total > 0:
            open_rate = stats.opened / total * 100
            click_rate = stats.unique_clicks / total * 100
        else:
            open_rate = click_rate = 0

        print(f"{name}:")
        print(f"  Subject ID referencia: campaign stats")
        print(f"  Entregados:  {total:,}")
        print(f"  Open rate:   {open_rate:.2f}%")
        print(f"  Click rate:  {click_rate:.2f}%")
        print(f"  Bajas:       {stats.unsubscribes:,}")

    # Determinar ganador por open rate
    if stats_a and stats_b and stats_a.total_delivered > 0 and stats_b.total_delivered > 0:
        or_a = stats_a.opened / stats_a.total_delivered
        or_b = stats_b.opened / stats_b.total_delivered

        if or_a > or_b:
            print(f"\nGanador por open rate: {name_a} ({or_a*100:.2f}% vs {or_b*100:.2f}%)")
        elif or_b > or_a:
            print(f"\nGanador por open rate: {name_b} ({or_b*100:.2f}% vs {or_a*100:.2f}%)")
        else:
            print("\nEmpate en open rate.")
    else:
        print("\nNo hay suficientes datos para determinar un ganador.")
        print("Nota: las campañas deben enviarse y tener actividad antes de comparar.")


def main():
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="AB Test SDK",
        default_sender_email="abtest@example.com"
    )

    print("A/B Testing con Acumbamail SDK")
    print("=" * 50)
    print("AVISO: Este ejemplo crea campañas reales en tu cuenta.\n")

    # Crear las dos variantes
    campaign_a, campaign_b = create_ab_campaigns(client)

    # Obtener estadísticas (en producción habría que esperar a que se envíen y se acumulen datos)
    print("\nObteniendo estadísticas...")
    print("Nota: en este momento las campañas aún no se han enviado, los datos estarán a 0.")
    stats_a = get_variant_metrics(client, campaign_a.id)
    stats_b = get_variant_metrics(client, campaign_b.id)

    compare_variants(
        stats_a, stats_b,
        name_a=f"Variante A (ID {campaign_a.id})",
        name_b=f"Variante B (ID {campaign_b.id})"
    )

    print("\nEjemplo completado.")
    print("En un test real, enviarías las campañas a segmentos distintos")
    print("y esperarías 24-48h antes de comparar resultados.")


if __name__ == "__main__":
    main()
