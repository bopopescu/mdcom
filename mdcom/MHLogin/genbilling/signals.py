import django.dispatch

credit_card_error = django.dispatch.Signal(providing_args=["invoice", "charge","owner"])
invoice_sent = django.dispatch.Signal(providing_args=["invoice","charge","owner"])

