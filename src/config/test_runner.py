from django.core.management import call_command
from django.test.runner import DiscoverRunner


class AuraTestRunner(DiscoverRunner):
    """
    DatabaseCache tablosunu test veritabanı kurulumundan hemen sonra oluşturur.
    `createcachetable` komutu migration sisteminin dışında çalıştığından
    Django'nun standart test runner'ı bunu otomatik yapmaz.
    """

    def setup_databases(self, **kwargs):
        result = super().setup_databases(**kwargs)
        call_command("createcachetable", "aura_rate_limit_cache", verbosity=0)
        return result
