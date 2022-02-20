import logging
import threading
from collections import deque
from multiprocessing import Lock

from django.forms import ValidationError

from thewall.models import Day

# For multi-threaded version following file format is assumed:
#
# workers 5
# 21 25 28
# 17
# 17 22 17 19 17

log = logging.getLogger("django_log")


def handle_upload_data(f):
    fhand = f.read().decode("utf-8").strip()
    fhand = fhand.split("\n")
    if fhand[0].find("workers") != -1:
        multi = True
        workers_count = int(fhand[0].split(" ")[1])
        del fhand[0]
    else:
        multi = False

    for i, elem in enumerate(fhand):
        elem = elem.split(" ")
        if len(elem) > 2000:
            raise ValidationError("A profile cannot have more than 2000 segments")
        elem = list(map(lambda x: 30 - int(x), elem))
        if max(elem) > 30 or min(elem) < 0:
            raise ValidationError("A segment must have initial value between 0 and 30")
        fhand[i] = elem

    if multi:
        # Multi-threaded version
        work_queue = deque()
        ready_queue = []
        for prof_no in range(1, len(fhand) + 1):
            for sec_no, section in enumerate(fhand[prof_no - 1], start=1):
                work_queue.append([prof_no, sec_no, section])

        get_work_lock = Lock()
        profiles = {}  # profiles = {profile: {day: current_work}}

        def work(worker_no, day):
            if work_queue:
                get_work_lock.acquire()
                prof_no, sec_no, section = work_queue.popleft()
                profiles[prof_no] = profiles.get(prof_no, {day: 0})
                get_work_lock.release()
            else:
                log.info(f"Worker #{worker_no} got no job today and is relieved")
                return

            log.info(
                f"Worker #{worker_no} works on Profile {prof_no}, Section {sec_no}"
            )
            section -= 1

            get_work_lock.acquire()
            profiles[prof_no][day] = profiles[prof_no].get(day, 0) + 1
            if section > 0:
                ready_queue.append([prof_no, sec_no, section])
            get_work_lock.release()

        day = 1
        log.info(f"Avaliable workers {workers_count}.")
        while work_queue:
            log.info(f"Day: {day}")
            pool = []
            for worker_no in range(1, workers_count + 1):
                t = threading.Thread(target=work, args=(worker_no, day), daemon=True)
                t.start()
                pool.append(t)
            for t in pool:
                t.join()

            work_queue = deque(ready_queue)
            ready_queue = []
            day += 1

        data = []
        for prof_no in profiles:
            total_work = 0
            for day in profiles[prof_no]:
                current_work = profiles[prof_no][day]
                total_work += current_work
                d = Day(
                    day_no=day,
                    profile_no=prof_no,
                    current_feet_done=current_work,
                    total_feet_done=total_work,
                )
                data.append(d)

    else:
        # Single-threaded version
        data = []
        for prof_no, profile in enumerate(fhand, start=1):
            total_work = 0  # section total
            for day in range(1, max(profile) + 1):
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
    if data:
        Day.objects.all().delete()
        for d in data:
            d.save()
