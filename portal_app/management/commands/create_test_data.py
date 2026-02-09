"""
Automated Test Data Generator for Gram Panchayat Portal

This script creates test users and sample data for testing purposes.
Run this ONLY in development/testing environments!

Usage:
    python create_test_data.py
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from portal_app.models import (
    BirthCertificate, DeathCertificate, IncomeCertificate,
    TaxPayment, Complaint, Application
)
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users and sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(
            '\n⚠️  WARNING: This will create test data in your database!'
        ))
        self.stdout.write(self.style.WARNING(
            'Only run this in development/testing environments.\n'
        ))
        
        confirm = input('Continue? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Cancelled.'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n🚀 Creating test data...\n'))
        
        # Create test users
        self.create_test_users()
        
        # Create sample applications
        self.create_sample_applications()
        
        # Create sample complaints
        self.create_sample_complaints()
        
        # Create sample tax payments
        self.create_sample_tax_payments()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Test data created successfully!\n'))
        self.display_test_credentials()
    
    def create_test_users(self):
        """Create test users for different roles"""
        
        self.stdout.write('📝 Creating test users...')
        
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@grampanchayat.gov.in',
                'password': 'Admin@123',
                'role': 'admin',
                'first_name': 'System',
                'last_name': 'Administrator',
                'phone_number': '9876543210',
                'village': 'Model Gram Panchayat',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'staff1',
                'email': 'staff1@grampanchayat.gov.in',
                'password': 'Staff@123',
                'role': 'staff',
                'first_name': 'Ramesh',
                'last_name': 'Kumar',
                'phone_number': '9876543211',
                'aadhar_number': '123456789012',
                'village': 'Model Gram Panchayat',
                'is_staff': True,
            },
            {
                'username': 'citizen1',
                'email': 'rajesh.sharma@email.com',
                'password': 'Citizen@123',
                'role': 'citizen',
                'first_name': 'Rajesh',
                'last_name': 'Sharma',
                'phone_number': '9876543212',
                'aadhar_number': '234567890123',
                'date_of_birth': '1990-01-15',
                'address': 'House No. 123, Main Road',
                'village': 'Rampur',
                'pincode': '560001',
            },
            {
                'username': 'citizen2',
                'email': 'priya.singh@email.com',
                'password': 'Citizen@123',
                'role': 'citizen',
                'first_name': 'Priya',
                'last_name': 'Singh',
                'phone_number': '9876543213',
                'aadhar_number': '345678901234',
                'date_of_birth': '1995-06-20',
                'address': 'House No. 456, Station Road',
                'village': 'Shantipur',
                'pincode': '560002',
            },
            {
                'username': 'citizen3',
                'email': 'amit.patel@email.com',
                'password': 'Citizen@123',
                'role': 'citizen',
                'first_name': 'Amit',
                'last_name': 'Patel',
                'phone_number': '9876543214',
                'aadhar_number': '456789012345',
                'date_of_birth': '1985-11-10',
                'address': 'House No. 789, Market Street',
                'village': 'Navapura',
                'pincode': '560003',
            },
        ]
        
        for user_data in test_users:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  ⚠️  User {username} already exists, skipping...')
                continue
            
            user = User.objects.create_user(username=username, password=password, **user_data)
            self.stdout.write(self.style.SUCCESS(f'  ✅ Created user: {username} ({user.role})'))
        
        self.stdout.write('')
    
    def create_sample_applications(self):
        """Create sample birth/death/income certificate applications"""
        
        self.stdout.write('📄 Creating sample applications...')
        
        # Get citizen users
        citizens = User.objects.filter(role='citizen')
        
        if not citizens.exists():
            self.stdout.write(self.style.WARNING('  ⚠️  No citizen users found, skipping applications'))
            return
        
        # Birth Certificates
        for i, citizen in enumerate(citizens[:3], 1):
            if BirthCertificate.objects.filter(applicant=citizen).exists():
                continue
            
            birth_cert = BirthCertificate.objects.create(
                applicant=citizen,
                child_name=f'Baby {citizen.last_name} {i}',
                child_gender=random.choice(['male', 'female']),
                date_of_birth=datetime.now().date() - timedelta(days=random.randint(30, 365)),
                place_of_birth='District Hospital',
                father_name=f'{citizen.first_name} {citizen.last_name}',
                father_aadhar='123456789012',
                mother_name=f'Mrs. {citizen.last_name}',
                mother_aadhar='234567890123',
                permanent_address=citizen.address,
            )
            
            # Create corresponding Application
            Application.objects.create(
                applicant=citizen,
                application_type='birth_certificate',
                status=random.choice(['pending', 'under_review', 'approved']),
            )
            
            self.stdout.write(f'  ✅ Created birth certificate for {citizen.username}')
        
        # Death Certificates
        if citizens.count() >= 2:
            citizen = citizens[1]
            if not DeathCertificate.objects.filter(applicant=citizen).exists():
                death_cert = DeathCertificate.objects.create(
                    applicant=citizen,
                    deceased_name='Late Mohan Singh',
                    deceased_gender='male',
                    deceased_age=75,
                    date_of_death=datetime.now().date() - timedelta(days=10),
                    place_of_death='Home',
                    cause_of_death='Natural causes',
                    informant_name=citizen.get_full_name(),
                    informant_relation='Son',
                    informant_phone=citizen.phone_number,
                    permanent_address=citizen.address,
                )
                
                Application.objects.create(
                    applicant=citizen,
                    application_type='death_certificate',
                    status='approved',
                )
                
                self.stdout.write(f'  ✅ Created death certificate for {citizen.username}')
        
        # Income Certificates
        if citizens.count() >= 3:
            citizen = citizens[2]
            if not IncomeCertificate.objects.filter(applicant=citizen).exists():
                income_cert = IncomeCertificate.objects.create(
                    applicant=citizen,
                    applicant_name=citizen.get_full_name(),
                    annual_income=250000,
                    occupation='Business',
                    purpose='Education Loan',
                    income_source='Small Business',
                    permanent_address=citizen.address,
                )
                
                Application.objects.create(
                    applicant=citizen,
                    application_type='income_certificate',
                    status='under_review',
                )
                
                self.stdout.write(f'  ✅ Created income certificate for {citizen.username}')
        
        self.stdout.write('')
    
    def create_sample_complaints(self):
        """Create sample complaints"""
        
        self.stdout.write('📢 Creating sample complaints...')
        
        citizens = User.objects.filter(role='citizen')
        
        if not citizens.exists():
            self.stdout.write(self.style.WARNING('  ⚠️  No citizen users found, skipping complaints'))
            return
        
        complaint_data = [
            {
                'category': 'Road and Infrastructure',
                'subject': 'Pothole on Main Road',
                'description': 'Large pothole near bus stand causing accidents',
                'location': 'Main Road, Near Bus Stand',
            },
            {
                'category': 'Water Supply',
                'subject': 'No water supply for 3 days',
                'description': 'Our area has not received water supply since last 3 days',
                'location': 'Station Road Area',
            },
            {
                'category': 'Street Lights',
                'subject': 'Street light not working',
                'description': 'Street light pole #23 has been non-functional for a week',
                'location': 'Market Street, Pole #23',
            },
        ]
        
        for i, citizen in enumerate(citizens[:3]):
            if i >= len(complaint_data):
                break
            
            if Complaint.objects.filter(citizen=citizen).exists():
                continue
            
            complaint = Complaint.objects.create(
                citizen=citizen,
                **complaint_data[i],
                status=random.choice(['pending', 'in_progress', 'resolved']),
            )
            
            self.stdout.write(f'  ✅ Created complaint: {complaint.subject}')
        
        self.stdout.write('')
    
    def create_sample_tax_payments(self):
        """Create sample tax payment records"""
        
        self.stdout.write('💰 Creating sample tax payments...')
        
        citizens = User.objects.filter(role='citizen')
        
        if not citizens.exists():
            self.stdout.write(self.style.WARNING('  ⚠️  No citizen users found, skipping tax payments'))
            return
        
        tax_types = [
            ('water_tax', 500, 'WT'),
            ('house_tax', 2000, 'HT'),
        ]
        
        for i, citizen in enumerate(citizens[:2]):
            if i >= len(tax_types):
                break
            
            tax_type, amount, prefix = tax_types[i]
            
            if TaxPayment.objects.filter(citizen=citizen, tax_type=tax_type).exists():
                continue
            
            tax_payment = TaxPayment.objects.create(
                citizen=citizen,
                tax_type=tax_type,
                amount=amount,
                property_number=f'{prefix}-{random.randint(100, 999)}',
                payment_method='online',
                status='verified',
            )
            
            self.stdout.write(f'  ✅ Created tax payment: {tax_type} - ₹{amount}')
        
        self.stdout.write('')
    
    def display_test_credentials(self):
        """Display test user credentials"""
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('TEST USER CREDENTIALS'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        credentials = [
            ('Admin', 'admin', 'Admin@123', 'Full system access'),
            ('Staff', 'staff1', 'Staff@123', 'Process applications'),
            ('Citizen 1', 'citizen1', 'Citizen@123', 'Rajesh Sharma'),
            ('Citizen 2', 'citizen2', 'Citizen@123', 'Priya Singh'),
            ('Citizen 3', 'citizen3', 'Citizen@123', 'Amit Patel'),
        ]
        
        self.stdout.write('')
        for role, username, password, note in credentials:
            self.stdout.write(f'  {role}:')
            self.stdout.write(f'    Username: {username}')
            self.stdout.write(f'    Password: {password}')
            self.stdout.write(f'    Note: {note}')
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')
        self.stdout.write('🌐 Access the portal at: http://127.0.0.1:8000/')
        self.stdout.write('📚 See TESTING_GUIDE.md for complete test procedures')
        self.stdout.write('')
