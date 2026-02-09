# 🧪 Portal Testing Guide

## Complete Testing Documentation for Digital Gram Panchayat Portal

**Version**: 1.0  
**Last Updated**: February 6, 2026  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test User Accounts](#test-user-accounts)
3. [Manual Testing Procedures](#manual-testing-procedures)
4. [Test Cases by Feature](#test-cases-by-feature)
5. [Real-World Scenarios](#real-world-scenarios)
6. [Error Handling Tests](#error-handling-tests)
7. [Security Testing](#security-testing)
8. [Performance Testing](#performance-testing)
9. [Browser Compatibility](#browser-compatibility)
10. [Automated Testing](#automated-testing)

---

## 🎯 Testing Overview

### Testing Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                      │
│                                                         │
│                    /─────────\                          │
│                   /  Manual   \                         │
│                  /   Testing   \                        │
│                 /───────────────\                       │
│                / Integration     \                      │
│               /     Testing       \                     │
│              /─────────────────────\                    │
│             /    Functional         \                   │
│            /       Testing           \                  │
│           /─────────────────────────────\               │
│          /        Unit Testing          \              │
│         /─────────────────────────────────\             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Testing Levels

1. **Unit Testing** - Individual functions and methods
2. **Functional Testing** - Features and user flows
3. **Integration Testing** - Component interactions
4. **Manual Testing** - Real-world usage scenarios
5. **Security Testing** - Vulnerability assessment
6. **Performance Testing** - Load and stress testing

---

## 👥 Test User Accounts

### Creating Test Users

#### Step 1: Start the Development Server
```powershell
cd d:\portal
.venv\Scripts\activate
python manage.py runserver
```

#### Step 2: Create Admin User
```powershell
python manage.py createsuperuser
```

**Admin Account Details:**
- Username: `admin`
- Email: `admin@grampanchayat.gov.in`
- Password: `Admin@123` (change in production!)
- Role: Admin (set via Django admin)

#### Step 3: Create Test Users via Registration

Go to: `http://127.0.0.1:8000/register/`

### Recommended Test User Accounts

#### 1. **Admin User**
```
Username: admin
Email: admin@grampanchayat.gov.in
Password: Admin@123
Role: admin
First Name: System
Last Name: Administrator
Phone: 9876543210
Village: Model Gram Panchayat
```

**Purpose**: Full system access, test admin dashboard, user management

---

#### 2. **Panchayat Staff User**
```
Username: staff1
Email: staff1@grampanchayat.gov.in
Password: Staff@123
Role: staff
First Name: Ramesh
Last Name: Kumar
Phone: 9876543211
Aadhar: 123456789012
Village: Model Gram Panchayat
```

**Purpose**: Test application processing, complaint handling

---

#### 3. **Citizen User 1 (Active User)**
```
Username: citizen1
Email: rajesh.sharma@email.com
Password: Citizen@123
Role: citizen
First Name: Rajesh
Last Name: Sharma
Phone: 9876543212
Aadhar: 234567890123
Date of Birth: 1990-01-15
Address: House No. 123, Main Road
Village: Rampur
Pincode: 560001
```

**Purpose**: Submit applications, file complaints, pay taxes

---

#### 4. **Citizen User 2 (New User)**
```
Username: citizen2
Email: priya.singh@email.com
Password: Citizen@123
Role: citizen
First Name: Priya
Last Name: Singh
Phone: 9876543213
Aadhar: 345678901234
Date of Birth: 1995-06-20
Address: House No. 456, Station Road
Village: Shantipur
Pincode: 560002
```

**Purpose**: Test first-time user experience, registration flow

---

#### 5. **Citizen User 3 (Multiple Applications)**
```
Username: citizen3
Email: amit.patel@email.com
Password: Citizen@123
Role: citizen
First Name: Amit
Last Name: Patel
Phone: 9876543214
Aadhar: 456789012345
Date of Birth: 1985-11-10
Address: House No. 789, Market Street
Village: Navapura
Pincode: 560003
```

**Purpose**: Test multiple concurrent applications, tracking

---

### Setting User Roles

**Via Django Admin:**
1. Go to: `http://127.0.0.1:8000/admin/`
2. Login with admin credentials
3. Click on **Users**
4. Select a user
5. Change **Role** field to: `admin`, `staff`, or `citizen`
6. Click **Save**

---

## 🧪 Manual Testing Procedures

### Test Environment Setup

```powershell
# 1. Activate virtual environment
cd d:\portal
.venv\Scripts\activate

# 2. Ensure database is up to date
python manage.py migrate

# 3. Create test users (if not exists)
python manage.py createsuperuser

# 4. Start server
python manage.py runserver

# 5. Open browser
# Navigate to: http://127.0.0.1:8000/
```

---

## 📝 Test Cases by Feature

### 1. User Registration Tests

#### Test Case 1.1: Successful Registration
**Steps:**
1. Go to `/register/`
2. Fill all required fields with valid data
3. Click "Create My Account"

**Expected Result:**
- ✅ Account created successfully
- ✅ Redirected to login page
- ✅ Success message displayed
- ✅ User appears in database

**Test Data:**
```
Username: testuser001
Email: test001@email.com
Password: TestPass@123
Phone: 9876543215
```

---

#### Test Case 1.2: Duplicate Email
**Steps:**
1. Go to `/register/`
2. Enter email that already exists
3. Submit form

**Expected Result:**
- ❌ Form validation error
- ❌ Message: "This email is already registered"
- ✅ No new user created

---

#### Test Case 1.3: Invalid Phone Number
**Steps:**
1. Go to `/register/`
2. Enter phone: `1234567890` (invalid prefix)
3. Submit form

**Expected Result:**
- ❌ Validation error
- ❌ Message: "Phone number must start with 6, 7, 8, or 9"

---

#### Test Case 1.4: Weak Password
**Steps:**
1. Go to `/register/`
2. Enter password: `weak` (too short)
3. Submit form

**Expected Result:**
- ❌ Validation error
- ❌ Message: "Password must be at least 8 characters"

---

#### Test Case 1.5: Invalid Aadhar
**Steps:**
1. Go to `/register/`
2. Enter Aadhar: `123` (less than 12 digits)
3. Submit form

**Expected Result:**
- ❌ Validation error
- ❌ Message: "Aadhar number must be exactly 12 digits"

---

### 2. User Login Tests

#### Test Case 2.1: Successful Login (Citizen)
**Steps:**
1. Go to `/login/`
2. Username: `citizen1`
3. Password: `Citizen@123`
4. Click "Login"

**Expected Result:**
- ✅ Login successful
- ✅ Redirected to `/citizen-dashboard/`
- ✅ Welcome message displayed
- ✅ User name shown in navbar

---

#### Test Case 2.2: Successful Login (Staff)
**Steps:**
1. Go to `/login/`
2. Username: `staff1`
3. Password: `Staff@123`
4. Click "Login"

**Expected Result:**
- ✅ Login successful
- ✅ Redirected to `/staff-dashboard/`
- ✅ Staff interface displayed

---

#### Test Case 2.3: Successful Login (Admin)
**Steps:**
1. Go to `/login/`
2. Username: `admin`
3. Password: `Admin@123`
4. Click "Login"

**Expected Result:**
- ✅ Login successful
- ✅ Redirected to `/admin-dashboard/`
- ✅ Admin interface with analytics

---

#### Test Case 2.4: Invalid Credentials
**Steps:**
1. Go to `/login/`
2. Username: `citizen1`
3. Password: `WrongPassword`
4. Click "Login"

**Expected Result:**
- ❌ Login failed
- ❌ Error message displayed
- ✅ User remains on login page
- ✅ No session created

---

#### Test Case 2.5: Empty Fields
**Steps:**
1. Go to `/login/`
2. Leave username and password empty
3. Click "Login"

**Expected Result:**
- ❌ HTML5 validation prevents submission
- ❌ "Please fill out this field" message

---

### 3. Birth Certificate Application Tests

#### Test Case 3.1: Successful Application
**Steps:**
1. Login as `citizen1`
2. Go to `/apply/birth-certificate/`
3. Fill all required fields:
   - Child Name: `Baby Sharma`
   - Gender: `Male`
   - Date of Birth: `2025-01-15`
   - Place of Birth: `District Hospital, Rampur`
   - Father Name: `Rajesh Sharma`
   - Father Aadhar: `234567890123`
   - Mother Name: `Anjali Sharma`
   - Mother Aadhar: `345678901234`
   - Address: `House No. 123, Main Road, Rampur`
4. Upload hospital certificate (PDF, <5MB)
5. Upload parent ID proof (PDF, <5MB)
6. Click "Submit Application"

**Expected Result:**
- ✅ Application submitted successfully
- ✅ Application number generated
- ✅ Status: Pending
- ✅ Redirected to application detail page
- ✅ Confirmation message displayed

---

#### Test Case 3.2: Missing Required Fields
**Steps:**
1. Login as `citizen1`
2. Go to `/apply/birth-certificate/`
3. Leave "Child Name" empty
4. Click "Submit Application"

**Expected Result:**
- ❌ Form validation error
- ❌ "This field is required" message
- ✅ Form data retained

---

#### Test Case 3.3: Invalid Aadhar Number
**Steps:**
1. Login as `citizen1`
2. Go to `/apply/birth-certificate/`
3. Enter Father Aadhar: `123` (invalid)
4. Submit form

**Expected Result:**
- ❌ Validation error
- ❌ Message: "Father's Aadhar must be exactly 12 digits"

---

#### Test Case 3.4: File Too Large
**Steps:**
1. Login as `citizen1`
2. Go to `/apply/birth-certificate/`
3. Upload file larger than 5MB
4. Submit form

**Expected Result:**
- ❌ Validation error
- ❌ Message: "File size must be less than 5MB"

---

#### Test Case 3.5: Invalid File Type
**Steps:**
1. Login as `citizen1`
2. Go to `/apply/birth-certificate/`
3. Upload `.exe` or `.zip` file
4. Submit form

**Expected Result:**
- ❌ Validation error
- ❌ Message: "Only PDF, JPG, JPEG, and PNG files are allowed"

---

### 4. Death Certificate Application Tests

#### Test Case 4.1: Successful Application
**Steps:**
1. Login as `citizen2`
2. Go to `/apply/death-certificate/`
3. Fill all fields:
   - Deceased Name: `Mohan Singh`
   - Gender: `Male`
   - Age: `75`
   - Date of Death: `2025-02-01`
   - Place of Death: `Home`
   - Cause of Death: `Natural causes`
   - Informant Name: `Priya Singh`
   - Informant Relation: `Daughter`
   - Informant Phone: `9876543213`
   - Address: `House No. 456, Station Road, Shantipur`
4. Upload hospital certificate
5. Upload deceased ID proof
6. Submit

**Expected Result:**
- ✅ Application submitted
- ✅ Application number assigned
- ✅ Email notification sent (if configured)

---

### 5. Income Certificate Application Tests

#### Test Case 5.1: Successful Application
**Steps:**
1. Login as `citizen3`
2. Go to `/apply/income-certificate/`
3. Fill all fields:
   - Applicant Name: `Amit Patel`
   - Annual Income: `250000`
   - Occupation: `Business`
   - Purpose: `Education loan`
   - Income Source: `Small Business`
   - Address: `House No. 789, Market Street`
4. Upload income proof (salary slip/business documents)
5. Upload ID proof
6. Submit

**Expected Result:**
- ✅ Application created
- ✅ Status: Pending verification

---

### 6. Tax Payment Tests

#### Test Case 6.1: Water Tax Payment
**Steps:**
1. Login as `citizen1`
2. Go to `/pay-tax/`
3. Select Tax Type: `Water Tax`
4. Amount: `500`
5. Property Number: `WT-123`
6. Payment Method: `Online`
7. Submit

**Expected Result:**
- ✅ Payment recorded
- ✅ Receipt number generated
- ✅ Status: Pending verification
- ✅ Amount and date displayed

---

#### Test Case 6.2: House Tax Payment
**Steps:**
1. Login as `citizen2`
2. Go to `/pay-tax/`
3. Select Tax Type: `House Tax`
4. Amount: `2000`
5. Property Number: `HT-456`
6. Submit

**Expected Result:**
- ✅ Payment submitted
- ✅ Unique receipt number

---

### 7. Complaint Filing Tests

#### Test Case 7.1: Road Complaint
**Steps:**
1. Login as `citizen1`
2. Go to `/file-complaint/`
3. Fill form:
   - Category: `Road and Infrastructure`
   - Subject: `Pothole on Main Road`
   - Description: `Large pothole near house 123 causing accidents`
   - Location: `Main Road, near Bus Stand`
4. Upload photo (optional)
5. Submit

**Expected Result:**
- ✅ Complaint filed
- ✅ Complaint ID generated (e.g., `CMP-2025-001`)
- ✅ Status: Pending
- ✅ Visible in citizen dashboard

---

#### Test Case 7.2: Water Supply Complaint
**Steps:**
1. Login as `citizen2`
2. Go to `/file-complaint/`
3. Category: `Water Supply`
4. Subject: `No water supply for 3 days`
5. Description: `Our area has not received water supply since Feb 3`
6. Submit

**Expected Result:**
- ✅ Complaint registered
- ✅ Timestamp recorded

---

### 8. Staff Application Processing Tests

#### Test Case 8.1: Approve Application
**Steps:**
1. Login as `staff1`
2. Go to `/staff-dashboard/`
3. Click on pending birth certificate application
4. Review details
5. Select Action: `Approve`
6. Add admin remarks: `All documents verified. Approved.`
7. Click "Update Status"

**Expected Result:**
- ✅ Status changed to: Approved
- ✅ Remarks saved
- ✅ Citizen notified (if email configured)
- ✅ Application moves to approved list

---

#### Test Case 8.2: Reject Application
**Steps:**
1. Login as `staff1`
2. Select an application
3. Action: `Reject`
4. Remarks: `Missing hospital certificate`
5. Submit

**Expected Result:**
- ✅ Status: Rejected
- ✅ Reason visible to citizen
- ✅ Citizen can reapply

---

#### Test Case 8.3: Request More Information
**Steps:**
1. Login as `staff1`
2. Select application
3. Action: `Under Review`
4. Remarks: `Please provide additional proof of address`
5. Submit

**Expected Result:**
- ✅ Status: Under Review
- ✅ Citizen sees remarks
- ✅ Can update application

---

### 9. Staff Complaint Management Tests

#### Test Case 9.1: Assign Complaint
**Steps:**
1. Login as `staff1`
2. Go to complaints list
3. Select unassigned complaint
4. Assign to self or another staff member
5. Save

**Expected Result:**
- ✅ Complaint assigned
- ✅ Status updated to: In Progress

---

#### Test Case 9.2: Resolve Complaint
**Steps:**
1. Login as `staff1`
2. Open assigned complaint
3. Add resolution notes: `Pothole repaired on Feb 5`
4. Status: `Resolved`
5. Submit

**Expected Result:**
- ✅ Status: Resolved
- ✅ Resolution visible to citizen
- ✅ Timestamp recorded

---

### 10. Admin Dashboard Tests

#### Test Case 10.1: View Analytics
**Steps:**
1. Login as `admin`
2. Go to `/admin-dashboard/`
3. View statistics

**Expected Result:**
- ✅ Total users displayed (count by role)
- ✅ Application statistics (total, pending, approved, rejected)
- ✅ Service statistics (birth, death, income certs)
- ✅ Charts loaded (doughnut and bar charts)

---

#### Test Case 10.2: Manage Users
**Steps:**
1. Login as `admin`
2. View user list
3. Edit user role
4. Change citizen to staff
5. Save

**Expected Result:**
- ✅ Role updated
- ✅ User access changed accordingly

---

### 11. Role-Based Access Control Tests

#### Test Case 11.1: Citizen Accessing Staff Area
**Steps:**
1. Login as `citizen1`
2. Manually navigate to `/staff-dashboard/`

**Expected Result:**
- ❌ Access denied
- ❌ Redirected to home
- ❌ Error message: "Access denied. Staff privileges required"

---

#### Test Case 11.2: Staff Accessing Admin Area
**Steps:**
1. Login as `staff1`
2. Navigate to `/admin-dashboard/`

**Expected Result:**
- ❌ Access denied
- ❌ Redirected to home
- ❌ Error message: "Access denied. Admin privileges required"

---

#### Test Case 11.3: Unauthenticated Access
**Steps:**
1. Logout (or use incognito mode)
2. Try to access `/citizen-dashboard/`

**Expected Result:**
- ❌ Redirected to `/login/`
- ❌ Login required message

---

### 12. Session & Security Tests

#### Test Case 12.1: Session Timeout
**Steps:**
1. Login as any user
2. Wait for 1 hour (or change SESSION_COOKIE_AGE for testing)
3. Try to access a protected page

**Expected Result:**
- ❌ Session expired
- ❌ Redirected to login
- ❌ Message: "Please login again"

---

#### Test Case 12.2: CSRF Token Validation
**Steps:**
1. Login as citizen
2. Open form (birth certificate)
3. Using browser dev tools, remove CSRF token
4. Submit form

**Expected Result:**
- ❌ Form submission blocked
- ❌ "CSRF verification failed" error

---

#### Test Case 12.3: Password Strength
**Steps:**
1. Go to `/register/`
2. Try password: `12345678` (all numeric)

**Expected Result:**
- ❌ Validation error
- ❌ "Password cannot be entirely numeric"

---

---

## 🌍 Real-World Scenarios

### Scenario 1: New Citizen Registration & Birth Certificate

**Story:**
Rajesh and Anjali Sharma just had a baby boy. They need to register on the portal and apply for a birth certificate.

**Test Flow:**
1. **Registration**
   - Go to portal homepage
   - Click "Register"
   - Fill Rajesh's details:
     - Username: `rajesh_sharma`
     - Email: `rajesh@email.com`
     - Phone: `9876543220`
     - Aadhar: `567890123456`
   - Create account

2. **First Login**
   - Login with new credentials
   - See citizen dashboard for first time
   - Notice empty state (no applications yet)

3. **Apply for Birth Certificate**
   - Click "Birth Certificate" from dashboard
   - Fill baby's details:
     - Child Name: `Aarav Sharma`
     - DOB: `2025-02-05`
     - Place: `District Hospital`
   - Fill parent details
   - Upload hospital certificate (scan)
   - Upload ID proofs
   - Submit application

4. **Track Application**
   - Receive application number: `BC-2025-001`
   - Check status: Pending
   - Wait for processing

5. **Staff Processing**
   - Staff member `staff1` logs in
   - Reviews application
   - Verifies documents
   - Approves application
   - Adds remark: "Verified and approved"

6. **Citizen Notification**
   - Rajesh logs in
   - Sees application status: Approved
   - Can download certificate (if implemented)
   - Happy citizen! ✅

**Expected Duration:** 15-20 minutes (manual testing)

---

### Scenario 2: Multiple Service Requests

**Story:**
Priya Singh needs multiple certificates - death certificate for her father and income certificate for herself.

**Test Flow:**
1. Login as `citizen2` (Priya)

2. **File Death Certificate**
   - Navigate to Death Certificate application
   - Fill deceased details (father)
   - Upload required documents
   - Submit (Application: DC-2025-001)

3. **File Income Certificate**
   - Navigate to Income Certificate
   - Fill income details
   - Upload salary slips
   - Submit (Application: IC-2025-001)

4. **Track Multiple Applications**
   - Go to "My Applications"
   - See both applications listed
   - Track status of each
   - Different statuses possible:
     - Death Cert: Approved
     - Income Cert: Under Review

5. **Respond to Review**
   - Staff asks for additional documents on income cert
   - Priya uploads more documents
   - Resubmits
   - Eventually approved

**Expected Outcome:**
- Both applications processed successfully
- Different timelines for different certificates
- Clear status tracking

---

### Scenario 3: Complaint Resolution Workflow

**Story:**
Amit Patel notices a broken street light near his house. He files a complaint and follows up until resolution.

**Test Flow:**
1. **File Complaint**
   - Login as `citizen3` (Amit)
   - Go to "File Complaint"
   - Category: Street Lights
   - Subject: "Broken street light on Market Street"
   - Description: "Street light pole #23 not working for 5 days"
   - Location: "Market Street, Pole #23"
   - Upload photo of broken light
   - Submit

2. **Complaint Registered**
   - Complaint ID: CMP-2025-005
   - Status: Pending
   - Timestamp recorded

3. **Staff Assignment**
   - Staff logs in
   - Reviews new complaints
   - Assigns to appropriate department
   - Status: In Progress
   - Adds note: "Forwarded to electricity department"

4. **Citizen Follows Up**
   - Amit checks complaint status
   - Sees "In Progress" status
   - Sees staff comment
   - Adds additional comment: "Still not fixed"

5. **Resolution**
   - Staff updates after repair
   - Status: Resolved
   - Resolution note: "Street light repaired on Feb 7"
   - Attaches photo of working light

6. **Citizen Satisfied**
   - Amit sees resolution
   - Can view history of complaint
   - Issue resolved! ✅

**Expected Duration:** Multiple days (real-world)

---

### Scenario 4: Tax Payment Tracking

**Story:**
Village resident needs to pay annual house tax and water tax.

**Test Flow:**
1. Login as citizen
2. Navigate to "Pay Tax"
3. **Pay House Tax:**
   - Tax Type: House Tax
   - Amount: ₹5,000
   - Property Number: HT-789
   - Payment Method: Online
   - Submit
   - Receipt: TX-2025-001

4. **Pay Water Tax:**
   - Tax Type: Water Tax
   - Amount: ₹1,200
   - Property Number: WT-789
   - Submit
   - Receipt: TX-2025-002

5. **View Payment History:**
   - Go to "My Payments"
   - See all tax payments
   - Can download receipts
   - Track verification status

6. **Staff Verification:**
   - Staff verifies payment
   - Updates status to "Verified"
   - Citizen gets confirmation

**Expected Outcome:**
- Both taxes recorded
- Receipts generated
- Payment history maintained

---

### Scenario 5: Admin Analytics Review

**Story:**
Gram Panchayat admin needs to review monthly performance.

**Test Flow:**
1. Login as `admin`
2. Open admin dashboard

3. **Review User Statistics:**
   - Total citizens: 150
   - Active staff: 5
   - New registrations this month: 20

4. **Review Application Stats:**
   - Total applications: 500
   - Pending: 45
   - Approved: 420
   - Rejected: 35
   - Average processing time: 3 days

5. **Review Service Breakdown:**
   - Birth Certificates: 180
   - Death Certificates: 50
   - Income Certificates: 120
   - Tax Payments: 150

6. **View Charts:**
   - Doughnut chart: Status distribution
   - Bar chart: Application types
   - Identify bottlenecks

7. **Take Action:**
   - Notice high pending count
   - Assign more staff to processing
   - Set priority for older applications

**Expected Outcome:**
- Clear insights into portal performance
- Data-driven decision making
- Identify areas for improvement

---

## ❌ Error Handling Tests

### 1. Database Errors

#### Test Case E1: Database Connection Lost
**Simulation:**
```powershell
# Stop MySQL service
net stop MySQL80

# Try to access portal
```

**Expected Result:**
- ❌ Graceful error page
- ❌ Message: "Database temporarily unavailable"
- ❌ No stack trace shown to users (if DEBUG=False)

---

### 2. File Upload Errors

#### Test Case E2: Disk Full
**Steps:**
1. Simulate full disk (test environment)
2. Try to upload file in application

**Expected Result:**
- ❌ Error message: "Unable to save file. Please try again"
- ✅ Application not saved in incomplete state
- ✅ User data retained in form

---

#### Test Case E3: Corrupt File Upload
**Steps:**
1. Upload corrupted PDF file
2. Submit application

**Expected Result:**
- ❌ Validation catches corrupt file
- ❌ Error: "Invalid file format"

---

### 3. Form Validation Errors

#### Test Case E4: XSS Attempt
**Steps:**
1. In registration form, username field enter:
   ```
   <script>alert('XSS')</script>
   ```
2. Submit

**Expected Result:**
- ❌ Validation error
- ❌ Message: "Username can only contain letters, numbers, and underscores"
- ✅ Script not executed
- ✅ Input sanitized

---

#### Test Case E5: SQL Injection Attempt
**Steps:**
1. Login form username:
   ```
   admin' OR '1'='1
   ```
2. Submit

**Expected Result:**
- ❌ Login fails
- ✅ No SQL injection occurs (Django ORM protects)
- ✅ Suspicious activity logged

---

### 4. Network Errors

#### Test Case E6: Timeout
**Steps:**
1. Simulate slow network
2. Submit large form with files
3. Request times out

**Expected Result:**
- ❌ User-friendly timeout message
- ✅ Option to retry
- ✅ Partial data not saved

---

### 5. Concurrent Access Errors

#### Test Case E7: Double Submission
**Steps:**
1. Fill birth certificate form
2. Click submit button twice quickly

**Expected Result:**
- ✅ Only one application created
- ✅ Duplicate prevented by unique constraints
- ✅ User notified of successful submission

---

### 6. Permission Errors

#### Test Case E8: Deleted User Access
**Steps:**
1. Admin deletes a citizen user
2. That user tries to login (session still active)

**Expected Result:**
- ❌ Login fails
- ❌ Session invalidated
- ❌ Error: "Account not found"

---

### 7. Data Integrity Errors

#### Test Case E9: Missing Related Data
**Steps:**
1. Application exists but applicant deleted
2. Staff tries to view application

**Expected Result:**
- ✅ Graceful handling
- ✅ Show "Applicant data unavailable"
- ✅ Application data still accessible

---

---

## 🔒 Security Testing

### 1. Authentication Tests

#### Security Test S1: Brute Force Attack
**Steps:**
1. Write script to attempt login 100 times with wrong password
2. Run against login endpoint

**Expected Result:**
- ✅ Rate limiting kicks in after 5 attempts
- ✅ Temporary account lock
- ✅ Admin notified of suspicious activity

---

#### Security Test S2: Session Hijacking
**Steps:**
1. Login as citizen1
2. Copy session cookie
3. Try to use cookie from different browser/IP

**Expected Result:**
- ✅ Session validation
- ✅ HttpOnly cookies prevent JavaScript access
- ✅ Suspicious activity logged

---

### 2. Authorization Tests

#### Security Test S3: Privilege Escalation
**Steps:**
1. Login as citizen
2. Manually change URL to access staff dashboard
3. Try to access admin functions

**Expected Result:**
- ❌ All access denied
- ❌ Redirected to appropriate page
- ✅ Middleware blocks unauthorized access

---

### 3. Input Validation Tests

#### Security Test S4: File Upload Attack
**Steps:**
1. Rename malicious file: `virus.exe` → `document.pdf`
2. Try to upload in application

**Expected Result:**
- ❌ Content-type validation catches it
- ❌ Upload rejected
- ✅ File not saved to server

---

### 4. Data Protection Tests

#### Security Test S5: Password Storage
**Steps:**
1. Create user with password: `TestPass123`
2. Check database directly

**Expected Result:**
- ✅ Password stored as Argon2 hash
- ✅ No plain text password anywhere
- ✅ Hash format: `argon2$argon2id$v=19$...`

---

---

## ⚡ Performance Testing

### Load Test 1: Concurrent Users
**Scenario:**
- 50 users browsing simultaneously
- 20 users submitting applications
- 10 staff processing applications

**Tools:**
```bash
# Install Apache Bench
# Test home page
ab -n 1000 -c 50 http://127.0.0.1:8000/

# Test login endpoint
ab -n 500 -c 25 -p login.txt http://127.0.0.1:8000/login/
```

**Expected Results:**
- ✅ Response time < 200ms for pages
- ✅ Response time < 500ms for forms
- ✅ No 500 errors
- ✅ Database connections managed properly

---

### Load Test 2: Large File Uploads
**Scenario:**
- 10 users uploading 5MB files simultaneously

**Expected Results:**
- ✅ All uploads complete successfully
- ✅ Server memory usage acceptable
- ✅ File validation doesn't slow down significantly

---

---

## 🌐 Browser Compatibility

### Browsers to Test

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | ✅ Primary |
| Firefox | Latest | ✅ Primary |
| Edge | Latest | ✅ Primary |
| Safari | Latest | ✅ Test |
| Mobile Chrome | Latest | ✅ Test |
| Mobile Safari | Latest | ✅ Test |

### Key Tests per Browser:
1. ✅ Registration form
2. ✅ Login
3. ✅ File uploads
4. ✅ Dashboard display
5. ✅ Responsive design
6. ✅ Form validation
7. ✅ CSRF tokens

---

## 🤖 Automated Testing

### Django Unit Tests

Create file: `portal_app/tests/test_security.py`

```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from portal_app.models import Application, BirthCertificate

User = get_user_model()

class SecurityTests(TestCase):
    
    def setUp(self):
        """Create test users"""
        self.citizen = User.objects.create_user(
            username='testcitizen',
            password='Test@123',
            role='citizen'
        )
        self.staff = User.objects.create_user(
            username='teststaff',
            password='Test@123',
            role='staff'
        )
        self.client = Client()
    
    def test_citizen_cannot_access_staff_dashboard(self):
        """Test RBAC - citizen blocked from staff area"""
        self.client.login(username='testcitizen', password='Test@123')
        response = self.client.get('/staff-dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirected
    
    def test_csrf_protection(self):
        """Test CSRF token required"""
        response = self.client.post('/login/', {
            'username': 'test',
            'password': 'test'
        })
        # Should fail without CSRF token
        self.assertNotEqual(response.status_code, 200)
    
    def test_password_hashing(self):
        """Test passwords are hashed"""
        user = User.objects.get(username='testcitizen')
        # Password should be hashed, not plain text
        self.assertNotEqual(user.password, 'Test@123')
        self.assertTrue(user.password.startswith('argon2'))
```

### Run Tests
```powershell
# Run all tests
python manage.py test

# Run specific test class
python manage.py test portal_app.tests.test_security

# Run with verbosity
python manage.py test --verbosity=2

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report
```

---

## 📊 Test Results Tracking

### Test Execution Log Template

```
Date: _______________
Tester: _______________
Environment: Development / Staging / Production

Test Summary:
- Total Test Cases: _____
- Passed: _____
- Failed: _____
- Blocked: _____
- Not Executed: _____

Critical Issues Found:
1. _______________
2. _______________

Minor Issues:
1. _______________
2. _______________

Overall Status: Pass / Fail / Partial
```

---

## 🎯 Test Coverage Checklist

### Functional Coverage

- [ ] User Registration (all fields, validations)
- [ ] User Login (all roles)
- [ ] Birth Certificate Application
- [ ] Death Certificate Application
- [ ] Income Certificate Application
- [ ] Tax Payments (water, house)
- [ ] Complaint Filing
- [ ] Complaint Tracking
- [ ] Application Processing (staff)
- [ ] Application Approval/Rejection
- [ ] Admin Dashboard Analytics
- [ ] User Management (admin)
- [ ] Role-Based Access Control
- [ ] File Uploads (all types)
- [ ] Status Tracking
- [ ] Search Functionality
- [ ] Logout

### Security Coverage

- [ ] CSRF Protection
- [ ] Password Hashing (Argon2)
- [ ] SQL Injection Prevention
- [ ] XSS Prevention
- [ ] File Upload Validation
- [ ] Session Management
- [ ] Role-Based Authorization
- [ ] HTTPS (production)
- [ ] Security Headers

### Usability Coverage

- [ ] Mobile Responsive
- [ ] Tablet Responsive
- [ ] Desktop Display
- [ ] Form Labels Clear
- [ ] Error Messages Helpful
- [ ] Success Messages
- [ ] Loading States
- [ ] Empty States
- [ ] Navigation Intuitive
- [ ] Accessibility (basic)

---

## 🚀 Quick Test Command

```powershell
# Complete test suite
Write-Host "Running Complete Test Suite..." -ForegroundColor Cyan

# 1. Start server
Start-Process powershell -ArgumentList "python manage.py runserver"

# 2. Wait for server
Start-Sleep -Seconds 3

# 3. Open browser with test URLs
Start-Process "http://127.0.0.1:8000/"
Start-Process "http://127.0.0.1:8000/register/"
Start-Process "http://127.0.0.1:8000/login/"

Write-Host "Test environment ready!" -ForegroundColor Green
Write-Host "Follow manual test cases from TESTING_GUIDE.md" -ForegroundColor Yellow
```

---

## 📞 Reporting Issues

### Bug Report Template

```markdown
**Bug Title:** Brief description

**Severity:** Critical / High / Medium / Low

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Result:**
What should happen

**Actual Result:**
What actually happened

**Screenshots:**
[Attach if applicable]

**Environment:**
- Browser: Chrome 120
- OS: Windows 11
- User Role: Citizen
- Date: 2025-02-06

**Additional Notes:**
Any other relevant information
```

---

## ✅ Sign-Off Criteria

### Ready for Production When:

1. ✅ All critical test cases passed
2. ✅ No critical bugs open
3. ✅ Security tests passed
4. ✅ Performance acceptable
5. ✅ Browser compatibility verified
6. ✅ Mobile responsive tested
7. ✅ Data backup tested
8. ✅ Error handling verified
9. ✅ Documentation complete
10. ✅ Admin training complete

---

**Testing Status**: 🧪 Ready for Comprehensive Testing

**Test Coverage**: All major features covered  
**Test Users**: Configured and ready  
**Test Data**: Sample data available  

**Last Updated**: February 6, 2026
