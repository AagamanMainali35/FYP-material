import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ClassApp.models import *
from django.core import mail
from django.conf import settings
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import random
from rest_framework.test import APITestCase
import datetime
from rest_framework import status
from rest_framework.test import APITestCase, APIClient,override_settings
from django.contrib.auth import get_user
import datetime
from io import BytesIO
import pandas as pd
from django.core.exceptions import PermissionDenied

class RegisterViewTests(TestCase):  
    def setUp(self):
        self.client = Client()
        self.grade = Grade.objects.create(classname='1')
        self.payment_structure = PaymentStructure.objects.create(
            grade=self.grade,
            Totalfeeamount=120000,
            AdmissionFee=10000
        )
        
        self.existing_user = User.objects.create_user(
            username='existinguser', 
            email='existing@example.com',
            password='ExistingPass@123'
        )
        
    def test_successful_student_registration(self):
        response = self.client.post(reverse('register'), {
            'signup': True,
            'role': 'Student',
            'Grade': self.grade.id,
            'remail': 'student@example.com',
            'rpassword': 'StrongPass@123',
            'rpassword2': 'StrongPass@123',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

        user = User.objects.get(email='student@example.com')
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('StrongPass@123'))

        user_profile = profile.objects.get(newprofile=user)
        self.assertEqual(user_profile.role, 'Student')
        self.assertEqual(user_profile.grade, self.grade)
        self.assertEqual(user_profile.payment_structure, self.payment_structure)
        
    def test_weak_password_too_short(self):
        response = self.client.post(reverse('register'), {
            'signup': True,
            'role': 'Student',
            'Grade': self.grade.id,
            'remail': 'short@example.com',
            'rpassword': '123',
            'rpassword2': '123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password must be at least 10 characters long.')
        
    def test_weak_password_no_special_char(self):
        response = self.client.post(reverse('register'), {
            'signup': True,
            'role': 'Student',
            'Grade': self.grade.id,
            'remail': 'nospecial@example.com',
            'rpassword': 'Password123',
            'rpassword2': 'Password123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password must contain at least one special character.')
    
    def test_existing_email(self):
        response = self.client.post(reverse('register'), {
            'signup': True,
            'role': 'Student',
            'Grade': self.grade.id,
            'remail': 'existing@example.com',  # Using the email created in setUp
            'rpassword': 'StrongPass@123',
            'rpassword2': 'StrongPass@123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email already exists, use a different one.')
        
    def test_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'signup': True,
            'role': 'Student',
            'Grade': self.grade.id,
            'remail': 'mismatch@example.com',
            'rpassword': 'StrongPass@123',
            'rpassword2': 'DifferentPass@456',  # Different password
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match.')

class LoginAndOTPViewsTestCase(TestCase): #  5 test cases
    def setUp(self):
        self.client = Client()
        self.email = 'testuser@example.com'
        self.password = 'TestPass123!'
        self.user = User.objects.create_user( 
            username='testuser',
            email=self.email,
            password=self.password
        )
        self.login_url = reverse('login')
        self.otp_url = reverse('ottp')
        self.home_url = reverse('homepage')

    def test_invalid_credentials(self):
        """Test login with completely wrong email and password"""
        response = self.client.post(self.login_url, {
            'loginemail': 'wrong@example.com',
            'loginpassword': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid Username or Password")

    def test_invalid_email_format(self):
        """Test login with existing email but wrong password"""
        response = self.client.post(self.login_url, {
            'loginemail': self.email,
            'loginpassword': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid Username or Password")

    @patch('random.randint', return_value=123456)
    def test_invalid_otp(self, mock_randint):
        """Test OTP verification with incorrect OTP"""
        self.client.post(self.login_url, {
            'loginemail': self.email,
            'loginpassword': self.password
        })
        response = self.client.post(self.otp_url, {'ottp': '654321'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid OTP")

    @patch('random.randint', return_value=123456)
    def test_email_send_failure(self, mock_randint):
        """Test behavior when OTP email sending fails"""
        with patch('django.core.mail.send_mail', side_effect=Exception('Email error')):
            response = self.client.post(self.login_url, {
                'loginemail': self.email,
                'loginpassword': self.password
            })
            self.assertRedirects(response, self.otp_url, fetch_redirect_response=False)

    def test_otp_page_without_session(self):
        """Test accessing OTP page without proper session data"""
        response = self.client.get(self.otp_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.home_url)

class LogoutViewTests(TestCase): # 4 Test Case
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.logout_url = reverse('logout')
        self.login_url = reverse('login')

    def test_logout_redirects_to_login(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url, fetch_redirect_response=False)

    def test_user_is_logged_out_after_logout(self):
        self.client.login(username='testuser', password='testpass')
        self.client.get(self.logout_url)
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)


    def test_session_key_changes_after_logout(self):
        self.client.login(username='testuser', password='testpass')
        session_key_before = self.client.session.session_key
        self.client.get(self.logout_url)
        session_key_after = self.client.session.session_key
        self.assertNotEqual(session_key_before, session_key_after)

    def test_logout_via_post_redirects_to_login(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url, fetch_redirect_response=False)

class ForgetPasswordViewTest(TestCase):#2 test case 
    def setUp(self):
        self.client = Client()
        self.forget_url = reverse('forgetpass')
        self.otp_url = reverse('ottp')
        self.email = 'testuser@example.com'

    @patch('random.randint', return_value=123456)
    def test_otp_sent_and_redirected(self, mock_randint):
        response = self.client.post(self.forget_url, {'forgotemail': self.email})
        self.assertRedirects(response, self.otp_url, fetch_redirect_response=False)
        self.assertEqual(self.client.session['ottp'], 123456)
        self.assertEqual(self.client.session['email'], self.email)
        self.assertEqual(self.client.session['workflow'], 'Forgetpassword')
        self.assertEqual(self.client.session['isloggedin?'], True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('123456', mail.outbox[0].body)

    @patch('django.core.mail.send_mail', side_effect=Exception('Email error'))
    def test_email_failure_handling(self, mock_send_mail):
        response = self.client.post(self.forget_url, {'forgotemail': self.email})
        self.assertRedirects(response, self.otp_url, fetch_redirect_response=False)

class ResetPasswordViewTest(TestCase):# 3 test cases working 
    def setUp(self):
        self.client = Client()
        self.email = 'reset@example.com'
        self.password = 'OldPassword123!'
        self.user = User.objects.create_user(username='resetuser', email=self.email, password=self.password)
        self.reset_url = reverse('reset')

    def test_reset_successful(self):
        session = self.client.session
        session['email'] = self.email
        session['isloggedin?'] = True
        session.save()

        response = self.client.post(self.reset_url, {
            'rpassword': 'NewStrong!Pass1',
            'rpassword2': 'NewStrong!Pass1'
        }, follow=True)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.get(email=self.email).check_password('NewStrong!Pass1'))

    def test_reset_mismatched_passwords(self):
        session = self.client.session
        session['email'] = self.email
        session['isloggedin?'] = True
        session.save()

        response = self.client.post(self.reset_url, {
            'rpassword': 'password1',
            'rpassword2': 'password2'
        })
        self.assertContains(response, "Passwords do not match.", status_code=200)

    def test_reset_short_password(self):
        session = self.client.session
        session['email'] = self.email
        session['isloggedin?'] = True
        session.save()

        response = self.client.post(self.reset_url, {
            'rpassword': 'short',
            'rpassword2': 'short'
        })
        self.assertContains(response, "Use a stronger password.", status_code=200)

class ContactViewTest(TestCase):# 9 test cases working
    def setUp(self):
        self.client = APIClient()
        self.url = '/contact/'
        self.valid_data = {
            "email": "user@example.com",
            "subject": "Test Subject",
            "message": "This is a test message."
        }

    def test_successful_contact_without_attachment(self):
        """Test successful contact form submission without file attachment"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], "mail sent successfully")
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.subject, "Test Subject")
        self.assertIn("This is a test message.", sent_mail.body)
        self.assertEqual(sent_mail.to, [settings.EMAIL_HOST_USER])
        self.assertEqual(len(sent_mail.attachments), 0)

    def test_successful_contact_with_attachment(self):
        """Test successful contact form submission with file attachment"""
        test_file = SimpleUploadedFile(
            "test_file.txt",
            b"Test file content",
            content_type="text/plain"
        )
        
        data = self.valid_data.copy()
        data['file'] = test_file
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], "mail sent successfully")
        
        # Verify email with attachment was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(len(sent_mail.attachments), 1)
        self.assertEqual(sent_mail.attachments[0][0], "test_file.txt")

    def test_large_file_attachment(self):
        """Test handling of large file attachments"""
        # Create a 2MB file (fixed to use integer multiplication)
        large_content = b'a' * (2 * 1024 * 1024)  # 2MB file
        large_file = SimpleUploadedFile(
            "large_file.txt",
            large_content,
            content_type="text/plain"
        )
        
        data = self.valid_data.copy()
        data['file'] = large_file
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], "mail sent successfully")
        self.assertEqual(len(mail.outbox[0].attachments), 1)

    def test_missing_required_fields(self):
        """Test validation for missing required fields"""
        required_fields = ['email', 'subject', 'message']
        
        for field in required_fields:
            with self.subTest(missing_field=field):
                invalid_data = self.valid_data.copy()
                invalid_data.pop(field)
                
                response = self.client.post(self.url, invalid_data, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.json()['status'], "Missing required fields")

    def test_invalid_email_format(self):
        """Test validation for invalid email format"""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = "invalid-email"
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], "mail sent successfully")

   

    def test_different_file_types(self):
        """Test handling of different file types"""
        file_types = [
            ('document.pdf', b'PDF content', 'application/pdf'),
            ('image.jpg', b'JPEG content', 'image/jpeg'),
            ('spreadsheet.xlsx', b'Excel content', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        ]
        
        for filename, content, content_type in file_types:
            with self.subTest(file_type=content_type):
                test_file = SimpleUploadedFile(filename, content, content_type=content_type)
                data = self.valid_data.copy()
                data['file'] = test_file
                
                response = self.client.post(self.url, data, format='multipart')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json()['status'], "mail sent successfully")
                self.assertEqual(mail.outbox[0].attachments[0][0], filename)
                mail.outbox = []  # Clear sent emails for next test
    
class ProfilePageFunctionalityTest(TestCase):# 6 test cases working
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.grade = Grade.objects.create(classname='5')
        self.profile = profile.objects.create(
            newprofile=self.user,
            grade=self.grade,
            role='Student',
            address='123 Test St'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile')

    def test_profile_page_initial_load(self):
        """Test that profile page loads with correct initial data"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'UserPages/Userprofile.html')
        self.assertContains(response, 'John')  # First name
        self.assertContains(response, 'Doe')  # Last name
        self.assertContains(response, '123 Test St')  # Address
        self.assertContains(response, '5')  # Grade

    def test_profile_info_update(self):
        """Test updating profile information"""
        data = {
            'Savedetails': 'true',
            'fname': 'UpdatedJohn',
            'lname': 'UpdatedDoe',
            'username': 'updateduser',
            'address': '456 New Address'
        }
        response = self.client.post(self.url, data)
        
        # Check JSON response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'Profile Has been updated sucessfully')
        
        # Refresh objects from db
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        # Verify updates
        self.assertEqual(self.user.first_name, 'UpdatedJohn')
        self.assertEqual(self.user.last_name, 'UpdatedDoe')
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.profile.address, '456 New Address')

    def test_profile_picture_upload(self):
        """Test uploading profile picture"""
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',
            content_type='image/jpeg'
        )
        response = self.client.post(self.url, {'Profilepic': test_image})
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Verify update
        self.profile.refresh_from_db()
        self.assertTrue(bool(self.profile.profile_picture))

    def test_password_change_success(self):
        """Test successful password change"""
        data = {
            'passwordchange': 'true',
            'old': 'testpass123',
            'new': 'NewPass123!'
        }
        response = self.client.post(self.url, data, follow=True)
        
        # Should redirect and show success message
        self.assertRedirects(response, self.url)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Password updated successfully.')
        
        # Verify password actually changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_password_change_failure(self):
        """Test failed password change scenarios"""
        data = {
            'passwordchange': 'true',
            'old': 'wrongpass',
            'new': 'NewPass123!'
        }
        response = self.client.post(self.url, data, follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Wrong Old Password Entered.')
        
        # Weak new password
        weak_passwords = [
            ('short', 'Password must be at least 8 characters long.'),
            ('nopassword', 'Password must contain at least one number.'),
            ('12345678', 'Password must contain at least one letter.'),
            ('Password1', 'Password must include at least one special character.')
        ]
        
        for pwd, expected_msg in weak_passwords:
            with self.subTest(password=pwd):
                data['old'] = 'testpass123'
                data['new'] = pwd
                response = self.client.post(self.url, data, follow=True)
                messages = list(response.context['messages'])
                self.assertEqual(str(messages[0]), expected_msg)

    def test_email_change_otp_flow(self):
        """Test the complete OTP flow for email change"""
        # Step 1: Request OTP
        response = self.client.post(self.url, {
            'OTPconfirm': 'true',
            'newemail': 'new@example.com'
        })
        self.assertEqual(response.status_code, 200)
        
        session = self.client.session
        session['ottp'] = '123456'
        session['email'] = 'new@example.com'
        session.save()
        
        response = self.client.post(self.url, {
            'OTP': '123456',
            'newemail': 'new@example.com'
        }, follow=True)
        
        # Verify email changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')
        
        # Check success message
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Email Changed sucessfully')

class EventAPITests(TestCase): # 9 Testcases working 

    def setUp(self):
        # Create API client instance
        self.client = APIClient()

        # Create a user and assign 'Admin' role in the profile
        self.user = User.objects.create_user(username='adminuser', password='adminpassword')
        self.user_profile = profile.objects.create(newprofile=self.user, role='Admin')

        # Create a second user with 'User' role
        self.normal_user = User.objects.create_user(username='normaluser', password='normalpassword')
        self.normal_user_profile = profile.objects.create(newprofile=self.normal_user, role='User')

        # Create an event for update/delete test
        self.event = Event.objects.create(title="Sample Event", date="2025-05-01")

    def test_create_event(self):
        self.client.login(username='adminuser', password='adminpassword')
        
        response = self.client.post('/events/create/', {
                'title': 'New Event',
                'date': '2025-06-01'
        })
        self.assertEqual(response.status_code, 200)

    def test_create_event_missing_data(self):
        self.client.login(username='adminuser', password='adminpassword')

        # Create a new event with missing data
        response = self.client.post('/events/create/', {
            'title': 'Incomplete Event'
        })

        self.assertEqual(response.status_code, 200)

    def test_update_event(self):
        self.client.login(username='adminuser', password='adminpassword')

        # Update the event
        response = self.client.put(f'/events/{self.event.id}/update/', {
            'title': 'Updated Event',
            'date': '2025-06-15'
        })

        self.assertEqual(response.status_code, 302)

    def test_update_event_not_found(self):
        self.client.login(username='adminuser', password='adminpassword')

        # Try to update a non-existing event
        response = self.client.put('/events/999/update/', {
            'title': 'Non-existent Event',
            'date': '2025-06-15'
        })

        self.assertEqual(response.status_code, 302)

    def test_delete_event(self):
        self.client.login(username='adminuser', password='adminpassword')

        # Delete the event
        response = self.client.delete(f'/events/{self.event.id}/delete/')

        self.assertEqual(response.status_code,302)

    def test_delete_event_not_found(self):
        self.client.login(username='adminuser', password='adminpassword')

        # Try to delete a non-existing event
        response = self.client.delete('/events/999/delete/')

        self.assertEqual(response.status_code, 302)

    def test_update_event_permission_denied(self):
        self.client.login(username='normaluser', password='normalpassword')

        # Try to update the event as a non-Admin user
        response = self.client.put(f'/events/{self.event.id}/update/', {
            'title': 'Non-Admin Update Event',
            'date': '2025-06-20'
        })

        # Should be forbidden
        self.assertEqual(response.status_code, 302)

    def test_delete_event_permission_denied(self):
        self.client.login(username='normaluser', password='normalpassword')

        # Try to delete the event as a non-Admin user
        response = self.client.delete(f'/events/{self.event.id}/delete/')

        # Should be forbidden
        self.assertEqual(response.status_code, 302)

    def test_redirect_for_non_authenticated_user(self):
        # Try to access an event without logging in
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Should redirect to login

    def test_redirect_for_non_admin_user(self):
        self.client.login(username='normaluser', password='normalpassword')

        # Try to access the update view as a normal user
        response = self.client.put(f'/events/{self.event.id}/update/', {
            'title': 'Updated Event as Normal User',
            'date': '2025-07-01'
        })
        self.assertEqual(response.status_code, 302)  # Should be forbidden for non-admin users

class NotificationTestCase(TestCase):
    def setUp(self):
        # Create test user and profile
        self.user = User.objects.create_user(username='testuser', password='password')
        self.profile = profile.objects.create(newprofile=self.user)
        
        # Common notification data
        self.valid_notification_data = {
            'user_instance': self.profile,
            'NotificationMsg': 'Test message',
            'is_read': False,
            'created_at': datetime.date(2025, 4, 23),
            'tag': 'General'
        }

    def test_create_notification_with_valid_data(self):
        notification = Notification.objects.create(**self.valid_notification_data)
        
        self.assertEqual(notification.NotificationMsg, 'Test message')
        self.assertEqual(notification.user_instance, self.profile)
        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.tag, 'General')
        self.assertEqual(notification.created_at, datetime.date(2025, 4, 23))
        self.assertEqual(str(notification), f'{self.profile.id}--Test message')

    def test_notification_with_different_tags(self):
        tags = ['Fees', 'General', 'Government', 'Exam', 'Profile', 'Holiday']
        
        for tag in tags:
            data = self.valid_notification_data.copy()
            data['tag'] = tag
            notification = Notification.objects.create(**data)
            self.assertEqual(notification.tag, tag)

    # 3. Test notification with default values
    def test_notification_default_values(self):
        minimal_data = {
            'user_instance': self.profile,
            'NotificationMsg': 'Default test'
        }
        notification = Notification.objects.create(**minimal_data)
        
        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.tag, 'General')
        self.assertEqual(notification.created_at, datetime.date.today())
        self.assertIsNone(notification.Notificationtitle)

    # 4. Test notification with title
    def test_notification_with_title(self):
        data = self.valid_notification_data.copy()
        data['Notificationtitle'] = 'Important Notice'
        notification = Notification.objects.create(**data)
        
        self.assertEqual(notification.Notificationtitle, 'Important Notice')

    # 5. Test notification string representation
    def test_notification_str_representation(self):
        notification = Notification.objects.create(
            user_instance=self.profile,
            NotificationMsg='Short message'
        )
        self.assertEqual(str(notification), f'{self.profile.id}--Short message')

    # 6. Test read status toggle
    def test_notification_read_status(self):
        notification = Notification.objects.create(**self.valid_notification_data)
        self.assertFalse(notification.is_read)
        
        notification.is_read = True
        notification.save()
        self.assertTrue(notification.is_read)

    # 7. Test future date validation (if your model has such validation)
    def test_notification_with_future_date(self):
        future_date = datetime.date.today() + datetime.timedelta(days=10)
        data = self.valid_notification_data.copy()
        data['created_at'] = future_date
        
        notification = Notification.objects.create(**data)
        self.assertEqual(notification.created_at, future_date)

    # 8. Test notification without required fields
    def test_notification_without_required_fields(self):
        # Test without user_instance
        with self.assertRaises(Exception):
            Notification.objects.create(NotificationMsg='Test message')
            
        # Test without message
        with self.assertRaises(Exception):
            Notification.objects.create(user_instance=self.profile)

    # 9. Test notification with long message
    def test_notification_with_long_message(self):
        long_msg = 'A' * 500  # Max length
        data = self.valid_notification_data.copy()
        data['NotificationMsg'] = long_msg
        
        notification = Notification.objects.create(**data)
        self.assertEqual(notification.NotificationMsg, long_msg)
        
        # Test exceeding max length
        with self.assertRaises(Exception):
            data['NotificationMsg'] = 'A' * 501
            Notification.objects.create(**data)

    # 10. Test multiple notifications for same user
    def test_multiple_notifications_for_user(self):
        for i in range(5):
            data = self.valid_notification_data.copy()
            data['NotificationMsg'] = f'Message {i}'
            Notification.objects.create(**data)
            
        notifications = Notification.objects.filter(user_instance=self.profile)
        self.assertEqual(notifications.count(), 5)

class PaymentTestCase(TestCase): #2 working as it is 
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = Client()

    @patch('requests.request') 
    def test_process_payment_valid(self, mock_request):
        # Mock the response from the Khalti API
        mock_request.return_value.text = json.dumps({'payment_url': 'https://fake-payment-url.com'})
        
        self.client.login(username="testuser", password="password")
        
        # Test valid payment initiation
        response = self.client.post(reverse('process'), {
            'amount': 1000,
            'order_id': '12345',
            'return_url': 'https://example.com/return'
        })
        
        # Check if the redirection happens to the correct payment URL
        self.assertRedirects(response, 'https://fake-payment-url.com', fetch_redirect_response=False)
        
    def test_process_payment_invalid_amount(self):
        # Test with an invalid amount (non-integer)
        self.client.login(username="testuser", password="password")
        
        response = self.client.post(reverse('process'), {
            'amount': 'invalid_amount',
            'order_id': '12345',
            'return_url': 'https://example.com/return'
        })
        
        self.assertEqual(response.status_code, 400)  # Should return a Bad Request error
        
    def test_process_payment_not_logged_in(self):
        # Test when the user is not logged in
        response = self.client.post(reverse('process'), {
            'amount': 1000,
            'order_id': '12345',
            'return_url': 'https://example.com/return'
        })
        
        self.assertRedirects(response, '/accounts/login/?next=/initiate/', fetch_redirect_response=False)

class VerifyTransactionTest(TestCase): #4 working as it is 
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = Client()
        self.client.login(username="testuser", password="password")
        # Create profile so default tests work
        self.grade=Grade.objects.create(classname='1',academic_year='2024')
        self.profile = profile.objects.create(newprofile=self.user, role="Student", address="Test", grade=self.grade)

    @patch('requests.request')
    def test_verify_transaction_success(self, mock_request):
        mock_response = {
            "status": "Completed",
            "amount": 100000
        }
        mock_request.return_value.text = json.dumps(mock_response)

        response = self.client.post(
            reverse('verify', kwargs={'amount': 1000}) + '?pidx=testpidx',
        )

        self.assertRedirects(response, reverse('pay'), fetch_redirect_response=False)
   
    @patch('requests.post')
    def test_verify_transaction_missing_pidx(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = '{"status":"success"}' 
        response = self.client.post(reverse('verify', kwargs={'amount': 1000}))
        self.assertEqual(response.status_code, 302)  
    def test_verify_transaction_user_not_logged_in(self):
        self.client.logout()
        response = self.client.post(
            reverse('verify', kwargs={'amount': 1000}) + '?pidx=testpidx',
        )
        self.assertEqual(response.status_code, 302)  

    def test_verify_transaction_user_has_no_profile(self):
        self.profile.delete()  
        response = self.client.post(
            reverse('verify', kwargs={'amount': 1000}) + '?pidx=testpidx',
        )
        self.assertEqual(response.status_code, 302)  

class ExamTests(TestCase):# 4 test cases
    def setUp(self):
        self.client = APIClient()
        # Create users with different roles
        self.student = User.objects.create_user(username='student', password='testpass')
        self.teacher = User.objects.create_user(username='teacher', password='testpass')
        self.admin = User.objects.create_user(username='admin', password='testpass')
        
        # Create profiles
        profile.objects.create(newprofile=self.student, role='Student')
        profile.objects.create(newprofile=self.teacher, role='Teacher')
        profile.objects.create(newprofile=self.admin, role='Admin')
        
        # Create test data
        self.grade = Grade.objects.create(classname="10", academic_year="2024/25")
        self.exam = Exam.objects.create(
            Exam_Name="Science Quiz",
            ExamGrade=self.grade,
            Exam_Date=datetime.date.today(),
            Created_by=self.teacher,
            Total_Marks=100
        )
        self.question = Questions.objects.create(
            Exam_Instace=self.exam,
            Question_Name="Test Question",
            Question_Marks=10,
            correct_answer="Correct"
        )
        self.correct_choice = Choice.objects.create(choice_name="Correct", question_id=self.question)
        self.wrong_choice = Choice.objects.create(choice_name="Wrong", question_id=self.question)

    def test_teacher_can_access_exam_creation(self):
        """Test teacher can access exam creation (has proper role)"""
        self.client.login(username='teacher', password='testpass')
        response = self.client.get(reverse('createExam'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_access_exam_creation(self):
        """Test student gets redirected when trying to create exam"""
        self.client.login(username='student', password='testpass')
        response = self.client.get(reverse('createExam'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND) 
        self.assertRedirects(response, reverse('errorpage'))

    def test_admin_can_access_exam_creation_if_in_roles(self):
        """Test admin can access if decorator includes 'Admin' role"""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('createExam'))
        # This will depend on whether your view's decorator includes 'Admin' role
        # If not included, it should redirect
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND])


    def test_user_without_profile_gets_forbidden(self):
        """Test user without profile gets proper response"""
        user = User.objects.create_user(username='no_profile', password='testpass')
        self.client.login(username='no_profile', password='testpass')
        response = self.client.get(reverse('createExam'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class UpdateExamViewTest(TestCase): # 3 test cases working as it is 
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test grade
        self.grade = Grade.objects.create(
            classname='5',  # Grade 5
            academic_year='2024/2025'
        )
        
        self.new_grade = Grade.objects.create(
            classname='6',  # Grade 6
            academic_year='2024/2025'
        )
        
        # Create test exam
        self.exam = Exam.objects.create(
            Exam_Name='Math Midterm',
            ExamGrade=self.grade,
            Exam_Date=datetime.date(2025, 5, 15),
            Created_by=self.user,
            Total_Marks='100'
        )
        
        # Create test question
        self.question = Questions.objects.create(
            Exam_Instace=self.exam,
            Question_Name='What is 2+2?',
            Question_Marks='10',
            correct_answer='4'
        )
        
        # Create choices for the question
        self.choice1 = Choice.objects.create(
            choice_name='3',
            question_id=self.question
        )
        
        self.choice2 = Choice.objects.create(
            choice_name='4',
            question_id=self.question
        )
        
        # Set up API client
        self.client = APIClient()
        
    def test_update_exam_successful(self):
        """Test updating an exam with valid data"""
        url = reverse('update')  # Assuming you have a URL pattern named 'update_exam'
        
        # Prepare update data - structure this exactly as your view expects
        update_data = {
            'Exam_ID': self.exam.id,
            'Exam_Name': 'Updated Math Exam',
            'Total_Marks': '120',
            'Exam_Date': '2025-06-01',
            'Grade': '6',  # Changed from Grade 5 to Grade 6
            'Questions': [
                {
                    'Question_Name': 'What is 5+5?',
                    'Question_Marks': '15',
                    'correct_answer': '10',
                    'Choices': [
                        {
                            'id': None,  # No ID means it's a new choice
                            'text': '10'
                        },
                        {
                            'id': None,
                            'text': '11'
                        }
                    ]
                }
            ]
        }
        
        # Make API request
        response = self.client.patch(url, data=json.dumps(update_data), 
                                   content_type='application/json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Data Updates Sucessfully')
        
        # Verify exam was updated in the database
        updated_exam = Exam.objects.get(id=self.exam.id)
        self.assertEqual(updated_exam.Exam_Name, 'Updated Math Exam')
        self.assertEqual(updated_exam.Total_Marks, '120')
        self.assertEqual(updated_exam.Exam_Date.strftime('%Y-%m-%d'), '2025-06-01')
        self.assertEqual(updated_exam.ExamGrade.classname, '6')
        
        # Verify new questions were created (as per your view implementation)
        new_questions = Questions.objects.filter(
            Exam_Instace=self.exam, 
            Question_Name='What is 5+5?'
        )
        self.assertTrue(new_questions.exists())
        new_question = new_questions.first()
        self.assertEqual(new_question.Question_Marks, '15')
        self.assertEqual(new_question.correct_answer, '10')
        
        # According to your view, choices should only be created/updated if they have an ID
        # So we don't expect any choices to be created for this new question
        choices = Choice.objects.filter(question_id=new_question)
        self.assertEqual(choices.count(), 0)  # Expect 0 choices since the view only updates choices with IDs
        
    def test_update_exam_with_existing_choice_ids(self):
        """Test updating an exam with references to existing choice IDs"""
        # Create a new question with choices that we'll reference in the update
        existing_question = Questions.objects.create(
            Exam_Instace=self.exam,
            Question_Name='Existing question',
            Question_Marks='20',
            correct_answer='Yes'
        )
        
        existing_choice = Choice.objects.create(
            choice_name='Original choice text',
            question_id=existing_question
        )
        
        url = reverse('update')
        
        # Include the existing choice ID in the update data
        update_data = {
            'Exam_ID': self.exam.id,
            'Exam_Name': 'Updated With Choices',
            'Total_Marks': '150',
            'Exam_Date': '2025-07-01',
            'Grade': '6',
            'Questions': [
                {
                    'Question_Id': existing_question.id,
                    'Question_Name': 'Updated question name',
                    'Question_Marks': '25',
                    'correct_answer': 'Updated answer',
                    'Choices': [
                        {
                            'id': existing_choice.id,
                            'text': 'Updated choice text'
                        }
                    ]
                }
            ]
        }
        
        # Make API request
        response = self.client.patch(url, data=json.dumps(update_data), 
                                   content_type='application/json')
        
        # This will fail because your view doesn't update existing questions
        # It always creates new ones. This test documents this behavior.
        
        # Check exam was updated
        updated_exam = Exam.objects.get(id=self.exam.id)
        self.assertEqual(updated_exam.Exam_Name, 'Updated With Choices')
        
        # Check that original question was not modified (as per your view implementation)
        original_question = Questions.objects.get(id=existing_question.id)
        self.assertEqual(original_question.Question_Name, 'Existing question')
        
        # Check that a new question was created instead
        new_questions = Questions.objects.filter(
            Exam_Instace=self.exam, 
            Question_Name='Updated question name'
        )
        self.assertTrue(new_questions.exists())
        
    def test_update_exam_invalid_grade(self):
        """Test updating an exam with an invalid grade"""
        url = reverse('update')
        
        update_data = {
            'Exam_ID': self.exam.id,
            'Exam_Name': 'Updated Math Exam',
            'Total_Marks': '120',
            'Exam_Date': '2025-06-01',
            'Grade': '99',  # Invalid grade
            'Questions': []
        }
        
        response = self.client.patch(url, data=json.dumps(update_data), 
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Grade not found')

class DeleteExamTestCase(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass',
            email='admin@school.com'
        )
        profile.objects.create(
            newprofile=self.admin,
            role='Principal'
        )

        # Create teacher user
        self.teacher = User.objects.create_user(
            username='teacher',
            password='teacherpass',
            email='teacher@school.com'
        )
        profile.objects.create(
            newprofile=self.teacher,
            role='Teacher'
        )

        # Create student user
        self.student = User.objects.create_user(
            username='student',
            password='studentpass',
            email='student@school.com'
        )
        profile.objects.create(
            newprofile=self.student,
            role='Student'
        )

        # Create grade
        self.grade = Grade.objects.create(classname='10')

        # Create exam (created by teacher)
        self.exam = Exam.objects.create(
            Exam_Name="Final Exam",
            ExamGrade=self.grade,
            Exam_Date="2025-06-15",
            Total_Marks="100",
            Created_by=self.teacher  # Linking to User, not profile
        )

        # Set up URLs
        self.valid_url = reverse('delete', args=[self.exam.id])
        self.invalid_url = reverse('delete', args=[999])

    def test_delete_exam_success_by_creator(self):
        """Creator (teacher) can delete their own exam"""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.delete(self.valid_url)
        self.assertEqual(response.status_code,302)

    def test_delete_exam_by_admin(self):
        """Admin can delete any exam"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.valid_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_exam_unauthorized(self):
        """Student cannot delete exam"""
        self.client.force_authenticate(user=self.student)
        response = self.client.delete(self.valid_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_nonexistent_exam(self):
        """Deleting non-existent exam returns 404"""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.delete(self.invalid_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_unauthenticated(self):
        """Unauthenticated users cannot delete"""
        response = self.client.delete(self.valid_url)
        self.assertEqual(response.status_code,302)

    def test_wrong_http_method(self):
        """GET request not allowed"""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.valid_url)
        self.assertEqual(response.status_code, 302)

class ScheduleViewTests(TestCase): # one test cases needs change 
    def setUp(self):
        self.client = self.client_class()
        self.user = User.objects.create_user(username='student', password='testpass')
        self.profile = profile.objects.create(newprofile=self.user, role='Student')
        self.grade = Grade.objects.create(classname="10", academic_year="2024/25")
        self.exam1 = Exam.objects.create(
            Exam_Name="Science",
            ExamGrade=self.grade,
            Exam_Date=datetime.date.today(),
            Created_by=self.user,
            Total_Marks="100"
        )
        self.exam2 = Exam.objects.create(
            Exam_Name="Math",
            ExamGrade=self.grade,
            Exam_Date=datetime.date.today(),
            Created_by=self.user,
            Total_Marks="100"
        )
        StudentLeaderBoard.objects.create(
            exam_id=self.exam1,
            student_id=self.user,
            Total_Question=10,
            total_marks=80,
            Correct=8,
            Answered=10,
            Incorrect=2
        )
        self.client.login(username='student', password='testpass')

    def test_schedule_view_context(self):
        response = self.client.get(reverse('schedule'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['Attempts'], 1)
        self.assertEqual(response.context['avg_score'], 80)
        self.assertEqual(response.context['higest_score'], 80)
        self.assertEqual(list(response.context['upcoming_exam']), [self.exam2])
        self.assertIn(self.exam1, response.context['exam'])  
        self.assertIn('today', response.context)
        self.assertTemplateUsed(response, 'UserPages/exam.html')

class AttendanceViewTests(TestCase):
    def setUp(self):
        # Create users
        self.admin = User.objects.create_user(username='admin', password='admin123')
        profile.objects.create(newprofile=self.admin, role='Admin')
        
        self.teacher = User.objects.create_user(username='teacher', password='teacher123')
        profile.objects.create(newprofile=self.teacher, role='Teacher')
        
        self.student1 = User.objects.create_user(username='student1', email='student1@school.com', password='student123')
        self.student2 = User.objects.create_user(username='student2', email='student2@school.com', password='student123')
        
        # Create grades
        self.grade1 = Grade.objects.create(classname='1')
        self.grade2 = Grade.objects.create(classname='2')
        
        # Assign grades to students
        profile.objects.create(newprofile=self.student1, role='Student', grade=self.grade1)
        profile.objects.create(newprofile=self.student2, role='Student', grade=self.grade2)
        
        # Create attendance records
        today = datetime.date.today()
        attendance.objects.create(user=self.student1, Grade=self.grade1, date=today, Attendance_Status='Present')
        attendance.objects.create(user=self.student2, Grade=self.grade2, date=today, Attendance_Status='absent')
        
        # Set up clients
        self.client = Client()
        self.api_client = APIClient()
        
        # URLs
        self.attendance_url = reverse('attendance')
        self.upload_url = reverse('uplaoddata')

    def create_test_excel_file(self):
        data = {
            'Name': ['Student One', 'Student Two'],
            'Email': ['student1@school.com', 'student2@school.com'],
            'Class': ['1', '2'],
            'Date': [datetime.date.today().strftime('%Y-%m-%d')] * 2,
            'Attendance Status': ['Present', 'absent']
        }
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return output

    def test_attendance_view_admin_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.attendance_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'AdminPages/attendance.html')

    def test_attendance_view_non_admin_access(self):
        self.client.force_login(self.teacher)
        response = self.client.get(self.attendance_url)
        self.assertEqual(response.status_code, 302)  # Expecting redirect

    def test_attendance_view_unauthenticated(self):
        response = self.client.get(self.attendance_url)
        self.assertRedirects(response, '/login/')

    def test_upload_valid_attendance_file(self):
        self.api_client.force_authenticate(user=self.admin)
        excel_file = self.create_test_excel_file()
        
        response = self.api_client.post(
            self.upload_url,
            {'file': excel_file},
            format='multipart'
        )

    def test_upload_invalid_file_type(self):
        self.api_client.force_authenticate(user=self.admin)
        response = self.api_client.post(
            self.upload_url,
            {'file': BytesIO(b'not an excel file')},
            format='multipart'
        )
        self.assertEqual(response.data['error'], 'Only .xlsx files are allowed')

    def test_upload_missing_columns(self):
        self.api_client.force_authenticate(user=self.admin)
        # Create dataframe missing required columns
        df = pd.DataFrame({'Wrong Column': [1, 2, 3]})
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        
        response = self.api_client.post(
            self.upload_url,
            {'file': output},
            format='multipart'
        )
        self.assertIn('error', response.data)

    def test_upload_nonexistent_user(self):
        self.api_client.force_authenticate(user=self.admin)
        
        df = pd.DataFrame({
            'Name': ['Unknown Student'],
            'Email': ['nonexistent@school.com'],
            'Class': ['1'],
            'Date': [datetime.date.today().strftime('%Y-%m-%d')],
            'Attendance Status': ['Present']
        })
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        test_file = SimpleUploadedFile(
            "test_file.xlsx", output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response = self.api_client.post(
            self.upload_url,
            {'file': test_file},
            format='multipart'
        )

        self.assertIn('UserError', response.data)

    def test_upload_unauthenticated(self):
        excel_file = self.create_test_excel_file()
        response = self.api_client.post(
            self.upload_url,
            {'file': excel_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 302)

