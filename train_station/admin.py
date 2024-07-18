from django.contrib import admin
from train_station.models import (
    Station,
    Route,
    Ticket,
    Order,
    TrainType,
    Train,
    Crew,
    Journey,
)

admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Ticket)
admin.site.register(Order)
admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Crew)
admin.site.register(Journey)
