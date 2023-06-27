import logging
import threading
from collections import deque
from multiprocessing import Lock
from typing import List

from django.forms import ValidationError
from django.core.files.uploadedfile import UploadedFile
from thewall.models import Day

log = logging.getLogger("django_log")


def handle_upload_data(uploaded_file, workers) -> None:
    """Entry point for handling an uploaded file."""
    read_data = parse_data(uploaded_file)

    if workers == -1:
        # Single-threaded version
        work_single_thread(read_data)
    else:
        # Multi-threaded version
        work_multi_thread(read_data, workers)


def parse_data(uploaded_file: UploadedFile) -> List[List[int]]:
    """Parse the uploaded file and return a list of profiles, each profile being a list of segments."""
    raw_data = uploaded_file.read().decode("utf-8").strip().split("\n")

    # Subtract the initial value from 30 to get the remaining height of the segment that must be build.
    read_data = [[30 - int(x) for x in line.split()] for line in raw_data]
    for lst in read_data:
        if len(lst) > 2000:
            raise ValidationError("A profile cannot have more than 2000 segments")
        for elem in lst:
            if not 0 <= elem <= 30:
                raise ValidationError("A segment must have initial value between 0 and 30")
    return read_data


def work_multi_thread(read_data: List[List[int]], workers: int) -> None:
    """Multi-threaded version of the work function.
    Each thread is a worker that works on a segment of a profile.
    """
    work_queue = deque()
    ready_queue = []
    for prof_no in range(1, len(read_data) + 1):
        for sec_no, section in enumerate(read_data[prof_no - 1], start=1):
            work_queue.append([prof_no, sec_no, section])

    get_work_lock = Lock()
    profiles = {}  # profiles = {profile: {day: current_work}}

    def work(worker_no, day):
        """Worker function."""

        # Get work
        if work_queue:
            with get_work_lock:
                prof_no, sec_no, section = work_queue.popleft()
                profiles[prof_no] = profiles.get(prof_no, {day: 0})
        else:
            log.info(f"Worker #{worker_no} got no job today and is relieved")
            return

        log.info(f"Worker #{worker_no} works on Profile {prof_no}, Section {sec_no}")
        section -= 1

        # Do work
        with get_work_lock:
            profiles[prof_no][day] = profiles[prof_no].get(day, 0) + 1
            if section > 0:
                ready_queue.append([prof_no, sec_no, section])

    day = 1
    log.info(f"Avaliable workers {workers}.")
    while work_queue:
        log.info(f"Day: {day}")
        pool = []
        for worker_no in range(1, workers + 1):
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
    if data:
        Day.objects.all().delete()
        for d in data:
            d.save()


def work_single_thread(read_data: List[List[int]]):
    """Single-threaded version of the work function."""
    data = []
    for prof_no, profile in enumerate(read_data, start=1):
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
