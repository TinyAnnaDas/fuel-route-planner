
from django.core.management import BaseCommand
from routes.models import FuelStation
from django.db.models import Count

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
}


class Command(BaseCommand):
    help = "Delete non-US states"

    def handle(self, *args, **options):
        FuelStation.objects.exclude(state__in=US_STATES).delete()
        all = FuelStation.objects.all().count()
        print(all)
        unique_addresses = (
            FuelStation.objects
            .values("address", "city", "state")
            .distinct()
        )
        first_item = unique_addresses.first()
        print(first_item)
        count = unique_addresses.count()
        print(count)

        duplicates = (
            FuelStation.objects
            .values("address", "city", "state")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .order_by("-count")   # biggest duplicates first
        )

        first = duplicates.first()
        print(first)




