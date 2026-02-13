from django.db import models


class FuelStation(models.Model):
    opis_truck_stop_id = models.IntegerField(db_index=True)
    truck_stop_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, db_index=True)
    rack_id = models.IntegerField()
    retail_price = models.DecimalField(max_digits=8, decimal_places=4)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["state", "city", "retail_price"]
        indexes = [
            models.Index(fields=["state", "retail_price"]),
        ]

    def __str__(self):
        return f"{self.truck_stop_name} ({self.city}, {self.state})"
