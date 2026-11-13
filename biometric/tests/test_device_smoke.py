"""Biometric device model / validator smoke tests."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from biometric.models import validate_schedule_time_format
from biometric.views import _get_zk_user_id


class ScheduleTimeFormatTests(TestCase):
    def test_valid_hhmm(self):
        validate_schedule_time_format("01:30")  # no raise

    def test_rejects_zero_duration(self):
        with self.assertRaises(ValidationError):
            validate_schedule_time_format("00:00")

    def test_rejects_bad_format(self):
        with self.assertRaises(ValidationError):
            validate_schedule_time_format("not-a-time")

    def test_rejects_invalid_minute(self):
        with self.assertRaises(ValidationError):
            validate_schedule_time_format("01:60")


class ZkUserIdTests(TestCase):
    def test_uses_badge_id_without_reformatting(self):
        self.assertEqual(_get_zk_user_id("3"), "3")
        self.assertEqual(_get_zk_user_id("003"), "003")

    def test_rejects_missing_or_non_numeric_badge_id(self):
        for badge_id in (None, "", "EMP3"):
            with self.subTest(badge_id=badge_id):
                with self.assertRaises(ValueError):
                    _get_zk_user_id(badge_id)
