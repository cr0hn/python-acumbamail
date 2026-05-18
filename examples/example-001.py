#!/usr/bin/env python3
"""
Hello World — ejemplo mínimo del SDK de Acumbamail.

Muestra cómo inicializar el cliente, listar tus listas de correo
y añadir un suscriptor, con el mínimo código posible.

Requisito:
    export ACUMBAMAIL_TOKEN=tu_token_aqui
"""

import os
from acumbamail import AcumbamailClient

# ID de lista de prueba; cámbialo por el tuyo
TEST_LIST_ID = 1138335

# Inicializar el cliente con el token de la variable de entorno
client = AcumbamailClient(
    auth_token=os.getenv("ACUMBAMAIL_TOKEN"),
    default_sender_name="Dani",
    default_sender_email="cr0hn@cr0hn.com"
)

# Listar todas las listas de correo de la cuenta
lists = client.get_lists()
print(f"Tienes {len(lists)} lista(s) de correo:")
for mail_list in lists:
    print(f"  - {mail_list.name} (ID: {mail_list.id}, suscriptores: {mail_list.subscribers_count})")

# Añadir un suscriptor a la lista de prueba
# AVISO: modifica datos reales en tu cuenta
subscriber = client.add_subscriber(
    email="helloworld@example.com",
    list_id=TEST_LIST_ID,
    fields={"name": "Hello World"}
)
print(f"\nSuscriptor añadido: {subscriber.email}")
