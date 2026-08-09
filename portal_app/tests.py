from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
import re
from unittest.mock import patch
from datetime import date

from portal_app.models import CustomUser, PendingRegistration


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class AdminLoginTests(TestCase):
	def setUp(self):
		self.password = 'admin123'
		self.admin_user = CustomUser.objects.create_user(
			username='admin_test',
			password=self.password,
			role='admin',
			is_active=True,
			is_staff=True,
			is_superuser=True,
			email_verified=True,
			first_name='Admin',
			last_name='User',
			phone_number='9876543210',
			address='Test Address',
			pincode='411001',
			email='admin_test@example.com',
		)

	def test_admin_can_login_and_reach_dashboard(self):
		response = self.client.post(
			reverse('admin_login'),
			data={
				'username': self.admin_user.username,
				'password': self.password,
			},
			follow=False,
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('admin_dashboard'))

		# Confirm auth state without forcing template rendering.
		self.assertIn('_auth_user_id', self.client.session)
		self.assertEqual(
			int(self.client.session['_auth_user_id']),
			self.admin_user.id,
		)

	def test_staff_can_login_and_reach_staff_dashboard(self):
		staff_user = CustomUser.objects.create_user(
			username='staff_test',
			password='staff12345',
			role='staff',
			is_active=True,
			is_staff=True,
			is_superuser=False,
			email_verified=True,
			first_name='Staff',
			last_name='User',
			phone_number='9876543211',
			address='Test Address',
			pincode='411001',
			email='staff_test@example.com',
		)

		response = self.client.post(
			reverse('login'),
			data={
				'username': staff_user.username,
				'password': 'staff12345',
			},
			follow=False,
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('staff_dashboard'))


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationTests(TestCase):
	def _create_pending_registration(self, **overrides):
		defaults = {
			'name': 'Test Citizen',
			'first_name': 'Test',
			'last_name': 'Citizen',
			'username': 'citizen_test_2',
			'email': 'citizen2@example.com',
			'phone_number': '9766501235',
			'gender': 'male',
			'date_of_birth': date(1995, 4, 8),
			'address': 'Citizen Nagar, Main Road',
			'state': 'Maharashtra',
			'district': 'Pune',
			'pincode': '411001',
			'aadhar_number': '',
		}
		defaults.update(overrides)
		pending = PendingRegistration(**defaults)
		pending.set_password('StrongPass123!')
		pending.set_otp('123456')
		pending.save()
		return pending

	def test_citizen_can_register(self):
		response = self.client.post(
			reverse('register'),
			data={
				'username': 'citizen_test',
				'name': 'Test Citizen',
				'gender': 'male',
				'date_of_birth': '1995-04-08',
				'email': 'citizen@example.com',
				'phone_number': '9876501234',
				'address': 'Citizen Nagar, Main Road',
				'state': 'Maharashtra',
				'district': 'Pune',
				'pincode': '411001',
				'password1': 'StrongPass123!',
				'password2': 'StrongPass123!',
			},
			follow=False,
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('register_verify_otp'))
		self.assertFalse(CustomUser.objects.filter(email='citizen@example.com').exists())

		pending = PendingRegistration.objects.get(email='citizen@example.com')
		self.assertEqual(pending.phone_number, '9876501234')
		self.assertEqual(len(mail.outbox), 1)

		otp_match = re.search(r'OTP[^\d]*(\d{6})', mail.outbox[0].body, re.IGNORECASE)
		self.assertIsNotNone(otp_match)
		otp_code = otp_match.group(1)

		verify_response = self.client.post(
			reverse('register_verify_otp'),
			data={'otp_code': otp_code},
			follow=False,
		)

		self.assertEqual(verify_response.status_code, 302)
		self.assertEqual(verify_response.url, reverse('login'))
		self.assertTrue(CustomUser.objects.filter(email='citizen@example.com').exists())

		user = CustomUser.objects.get(email='citizen@example.com')
		self.assertEqual(user.name, 'Test Citizen')
		self.assertEqual(user.phone_number, '9876501234')
		self.assertTrue(user.is_active)
		self.assertTrue(user.email_verified)
		self.assertTrue(user.check_password('StrongPass123!'))

	def test_register_verify_otp_redirects_on_create_exception(self):
		pending = self._create_pending_registration()
		session = self.client.session
		session['pending_registration_id'] = pending.id
		session['pending_registration_email'] = pending.email
		session['pending_registration_username'] = pending.username
		session['pending_registration_phone_number'] = pending.phone_number
		session['pending_registration_otp'] = '123456'
		session.save()

		with patch('portal_app.views.CustomUser.save', side_effect=Exception('boom')):
			response = self.client.post(
				reverse('register_verify_otp'),
				data={'otp_code': '123456'},
				follow=False,
			)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('register_verify_otp'))
		self.assertTrue(PendingRegistration.objects.filter(id=pending.id).exists())
		self.assertFalse(CustomUser.objects.filter(email=pending.email).exists())

	def test_register_verify_otp_creates_user_with_correct_otp(self):
		pending = self._create_pending_registration(
			username='citizen_test_3',
			email='citizen3@example.com',
			phone_number='9766501236',
		)
		session = self.client.session
		session['pending_registration_id'] = pending.id
		session['pending_registration_email'] = pending.email
		session['pending_registration_username'] = pending.username
		session['pending_registration_phone_number'] = pending.phone_number
		session['pending_registration_otp'] = '123456'
		session.save()

		response = self.client.post(
			reverse('register_verify_otp'),
			data={'otp_code': '123456'},
			follow=False,
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login'))
		self.assertTrue(CustomUser.objects.filter(email='citizen3@example.com').exists())
		self.assertFalse(PendingRegistration.objects.filter(id=pending.id).exists())
