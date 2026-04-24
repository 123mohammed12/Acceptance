from django.apps import AppConfig


class MyAcceptanceConfig(AppConfig):
    name = 'my_acceptance'

    def ready(self):
        import my_acceptance.signals  # noqa
