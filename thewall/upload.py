from django.forms import ValidationError
from thewall.models import Day


def handle_upload_data(f):
    fhand = f.read().decode("utf-8").strip()
    fhand = fhand.split("\n")
    for i, elem in enumerate(fhand):
        elem = elem.split(" ")
        if len(elem) > 2000:
            raise ValidationError("A profile cannot have more than 2000 segments")
        elem = list(map(lambda x: 30 - int(x), elem))
        if max(elem) > 30 or min(elem) < 0:
            raise ValidationError("A segment must have initial value between 0 and 30")
        fhand[i] = elem

    data = []
    for prof_no, profile in enumerate(fhand, start=1):
        total_work = 0  # section total
        for day in range(1, 31):
            current_work = 0  # daily work completed
            for section in profile:
                if section >= day:
                    current_work += 1
            total_work += current_work
            d = Day(
                day_no=day,
                profile_no=prof_no,
                current_feet_done=current_work,
                total_feet_done=total_work,
            )
            data.append(d)

    Day.objects.all().delete()
    for d in data:
        d.save()
