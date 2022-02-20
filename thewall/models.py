from django.db import models


class Day(models.Model):
    day_no = models.PositiveSmallIntegerField()
    profile_no = models.PositiveSmallIntegerField()
    current_feet_done = models.PositiveSmallIntegerField()
    total_feet_done = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"Profile {self.profile_no}; Day {self.day_no}"
