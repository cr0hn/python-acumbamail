#!/usr/bin/env python3
"""
Ejemplo de análisis de campañas con el SDK de Acumbamail.

Muestra cómo obtener y analizar métricas de campañas:
- Listado de campañas
- Información total de una campaña (open rate, click rate, bounces)
- Clics por URL
- Aperturas por navegador y sistema operativo
"""

import os
from datetime import datetime
from acumbamail import AcumbamailClient

# ID de campaña de prueba; cámbialo por uno real de tu cuenta
# o deja None para analizar la campaña más reciente
TEST_CAMPAIGN_ID = None


def analyze_campaign(client: AcumbamailClient, campaign_id: int) -> None:
    """Analiza el rendimiento completo de una campaña."""

    print(f"Analizando campaña ID: {campaign_id}")
    print("=" * 50)

    # Estadísticas totales
    stats = client.get_campaign_total_information(campaign_id)
    total = stats.total_delivered

    if total > 0:
        open_rate = stats.opened / total * 100
        click_rate = stats.unique_clicks / total * 100
        bounce_rate = stats.hard_bounces / total * 100
        unsub_rate = stats.unsubscribes / total * 100
    else:
        open_rate = click_rate = bounce_rate = unsub_rate = 0

    print(f"Entregados:      {total:,}")
    print(f"Abiertos:        {stats.opened:,} ({open_rate:.2f}%)")
    print(f"Clics únicos:    {stats.unique_clicks:,} ({click_rate:.2f}%)")
    print(f"Clics totales:   {stats.total_clicks:,}")
    print(f"Hard bounces:    {stats.hard_bounces:,} ({bounce_rate:.2f}%)")
    print(f"Bajas:           {stats.unsubscribes:,} ({unsub_rate:.2f}%)")
    print(f"Quejas:          {stats.complaints:,}")

    # Evaluación de rendimiento
    print("\nEvaluación:")
    if open_rate >= 25:
        print("  Open rate excelente (>= 25%)")
    elif open_rate >= 15:
        print("  Open rate bueno (>= 15%)")
    elif open_rate >= 10:
        print("  Open rate medio (>= 10%)")
    else:
        print("  Open rate bajo (< 10%) — revisa el asunto del email")

    if click_rate >= 3:
        print("  Click rate excelente (>= 3%)")
    elif click_rate >= 1:
        print("  Click rate bueno (>= 1%)")
    else:
        print("  Click rate bajo (< 1%) — mejora el contenido y las CTAs")

    # Clics por URL
    print("\nURLs más clicadas:")
    clicks = client.get_campaign_clicks(campaign_id)
    if clicks:
        sorted_clicks = sorted(clicks, key=lambda c: c.clicks, reverse=True)
        for i, click in enumerate(sorted_clicks[:5], 1):
            print(f"  {i}. {click.url}")
            print(f"     Clics totales: {click.clicks:,} | Únicos: {click.unique_clicks:,}")
    else:
        print("  Sin clics registrados.")

    # Aperturas por navegador
    print("\nAperturas por navegador:")
    by_browser = client.get_campaign_openers_by_browser(campaign_id)
    if by_browser:
        # La API puede devolver una lista de objetos o un dict según la versión
        if isinstance(by_browser, list):
            for item in by_browser[:5]:
                print(f"  {item}")
        else:
            for browser, count in list(by_browser.items())[:5]:
                print(f"  {browser}: {count}")
    else:
        print("  Sin datos de navegador.")

    # Aperturas por sistema operativo
    print("\nAperturas por sistema operativo:")
    by_os = client.get_campaign_openers_by_os(campaign_id)
    if by_os:
        if isinstance(by_os, list):
            for item in by_os[:5]:
                print(f"  {item}")
        else:
            for os_name, count in list(by_os.items())[:5]:
                print(f"  {os_name}: {count}")
    else:
        print("  Sin datos de sistema operativo.")


def main():
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
        default_sender_name="Analytics SDK",
        default_sender_email="analytics@example.com"
    )

    print(f"Análisis de campañas — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Listar campañas disponibles
    campaigns = client.get_campaigns(complete_json=True)
    if not campaigns:
        print("No hay campañas en la cuenta.")
        return

    print(f"Campañas encontradas: {len(campaigns)}")
    for i, c in enumerate(campaigns[:5], 1):
        print(f"  {i}. {c.name} (ID: {c.id})")

    # Analizar campaña específica o la más reciente
    campaign_id = TEST_CAMPAIGN_ID or campaigns[0].id
    print(f"\nAnalizando: campaña ID {campaign_id}")
    print("=" * 60)
    analyze_campaign(client, campaign_id)


if __name__ == "__main__":
    main()
