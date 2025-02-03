from faker import Faker
from .models import Event
faker=Faker()
def event(num):
    for i in range(num):
        title=faker.catch_phrase()
        description=faker.paragraph()
        date=faker.date_time()
        location=faker.city()
        Event.objects.create(title=title,description=description,date=date,location=location)

event(10)