"""Biometric device model / validator smoke tests."""

from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import TestCase

from biometric.cbv.biometric import BiometricSheduleForm
from biometric.forms import BiometricDeviceSchedulerForm
from biometric.models import BiometricDevices, validate_schedule_time_format
from biometric.views import (
    _get_zk_user_id,
    _start_zk_live_capture,
    poll_biometric_devices,
)


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


class BiometricScheduleViewTests(TestCase):
    @patch("biometric.cbv.biometric.HorillaRedirect", return_value=HttpResponse())
    def test_schedule_enables_dahua_for_registered_polling(self, _redirect):
        device = BiometricDevices.objects.create(
            name="Dahua",
            machine_type="dahua",
            machine_ip="192.0.2.1",
            port=37777,
        )
        form = BiometricDeviceSchedulerForm(
            data={"scheduler_duration": "01:00"}, instance=device
        )
        self.assertTrue(form.is_valid())

        view = BiometricSheduleForm()
        view.request = Mock()
        view.form_valid(form)
        _redirect.assert_called_once_with(view.request)

        device.refresh_from_db()
        self.assertTrue(device.is_scheduler)
        self.assertFalse(device.is_live)
        self.assertEqual(device.scheduler_duration, "01:00")
        dahua_handler = Mock()
        with patch.dict(
            "biometric.views._BIOMETRIC_SCHEDULERS", {"dahua": dahua_handler}
        ):
            poll_biometric_devices()
        dahua_handler.assert_called_once_with(device.pk)


class BiometricLiveCaptureTests(TestCase):
    @patch("biometric.views.ZKBioAttendance")
    @patch("biometric.views.ZK")
    def test_zk_live_capture_does_not_require_speaker_test(
        self, zk_class, attendance_thread
    ):
        device = BiometricDevices.objects.create(
            name="ZKTeco",
            machine_type="zk",
            machine_ip="192.0.2.2",
            port=4370,
            zk_password="123",
        )
        connection = Mock()
        connection.test_voice.side_effect = RuntimeError("unsupported voice index")
        zk_class.return_value.connect.return_value = connection

        _start_zk_live_capture(device)

        device.refresh_from_db()
        self.assertTrue(device.is_live)
        self.assertFalse(device.is_scheduler)
        connection.test_voice.assert_not_called()
        connection.disconnect.assert_called_once()
        attendance_thread.return_value.start.assert_called_once()
