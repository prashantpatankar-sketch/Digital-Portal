# OTP System - Step-by-Step Testing Guide

## 🚀 Quick Test (10 Minutes)

### Part 1: Setup (2 minutes)

#### Option A: Gmail Setup (Recommended)
```
1. Open: https://myaccount.google.com/apppasswords
2. Select: App = "Mail", Device = "Windows/Linux/Mac"
3. Google generates 16-character password
4. Copy it (remove spaces)
5. Create file: .env in project root

.env contents:
────────────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=yyyyyyxxxxxxzzzzzz
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
────────────────────────────────────────

6. Restart Django server
   - Press Ctrl+C
   - python manage.py runserver
```

#### Option B: Console Output (Easiest for Testing)
```
No setup needed!
Django already uses console backend by default.
Check Django server console for OTP output.
```

---

### Part 2: Test Registration (8 minutes)

#### Step 1: Navigate to Registration
```
1. Open: http://localhost:8000/register-multi-step/
2. Should see:
   ✓ "Premium Registration" heading
   ✓ Step 1: Basic Info
   ✓ Username, Email, Mobile, Password fields
   ✓ Auto-save notification
```

#### Step 2: Fill Step 1 Form
```
Username:        testuser123
Email:           your-email@gmail.com (use REAL email)
Mobile:          9876543210
Password:        Test@1234
Confirm:         Test@1234
Gender:          Male
Date of Birth:   1995-05-15
```

Check: 
- [x] Real-time validation shows
- [x] No red error icons
- [x] "Preview" button enabled

#### Step 3: Fill Step 2 Form
```
(Click "Next" or scroll)

Full Name:       John Doe
Address:         123 Gram Panchayat Road
State:           Maharashtra
District:        Pune  
Pincode:         411001
```

Check:
- [x] All fields populated
- [x] No validation errors
- [x] "Verify & Submit" button visible

#### Step 4: Submit Form
```
1. Click "Submit for Verification"
2. Wait for response (1-2 seconds)
3. Should see one of:

SUCCESS CASE:
✓ JSON response shows success
✓ Redirects to /register/verify-otp/
✓ OTP page loads with countdown timer

FAILURE CASE (Email error):
✗ Error message shown
✗ Check .env file configuration
✗ Check Gmail app password
✗ Restart Django server
```

---

### Part 3: OTP Verification (5 minutes)

#### Check Email for OTP

**If using Gmail SMTP:**
```
1. Open your email inbox
2. Subject: "Registration OTP - Digital Gram Panchayat Portal"
3. Body contains: 6-digit OTP code
4. Copy the code: 123456 (example)
```

**If using Console Backend:**
```
1. Look at Django server console
2. Should see:

---MESSAGE---
Dear John Doe,

Thank you for registering with Digital Gram Panchayat Portal.
Your One-Time Password (OTP) is: 482651

This OTP is valid for 10 minutes. Do not share it with anyone.

Regards,
Digital Gram Panchayat Portal
---END MESSAGE---

3. Copy OTP code: 482651
```

#### Enter OTP on Page

```
1. On OTP verification page, you should see:
   ✓ 6 empty digit boxes: [0] [0] [0] [0] [0] [0]
   ✓ Timer: 10:00 counting down
   ✓ Email shown: user@example.com

2. Click first box and type: 4
   Expected: Auto-focus to box 2

3. Type: 8
   Expected: Auto-focus to box 3

4. Continue typing remaining digits: 2651
   Expected: Auto-focus moves, all 6 boxes filled

5. Observe:
   ✓ All 6 boxes blue with values
   ✓ Verify button now ENABLED (blue, clickable)
   ✓ Timer still counting down
```

#### Click Verify Button

```
1. Click "Verify OTP" button
2. Wait for response (1-2 seconds)
3. Expected response:

SUCCESS:
✓ Button shows loading spinner
✓ Toast notification: "OTP verified successfully!"
✓ Button turns green with checkmark: "✓ OTP Verified!"
✓ Redirects to login page
✓ Account is now active!

FAILURE (wrong OTP):
✗ Boxes turn RED with shake animation
✗ Error message: "Invalid OTP code. 2 attempt(s) remaining."
✗ Previous values cleared from boxes (ready to retry)
✗ Timer continues counting
✗ Verify button disabled (until 6 digits entered again)
```

---

## 🎯 Detailed Test Scenarios

### Test 1: Happy Path (Complete Success)

```
Goal: Register successfully with valid data

Step 1: Register
├─ Fill all fields correctly
├─ Submit form
├─ Receive OTP email
└─ Verify no errors

Step 2: Verify OTP
├─ Get OTP from email: 482651
├─ Click first digit box  
├─ Type all 6 digits
├─ Wait for auto-focus
└─ All 6 boxes should be filled

Step 3: Submit OTP
├─ Click "Verify OTP"
├─ Wait for response
├─ See success animation
├─ See "OTP verified!" toast
└─ Redirect to login

Step 4: Verify Account
├─ On login page
├─ Enter username: testuser123
├─ Enter password: Test@1234
├─ Click Login
├─ See dashboard

EXPECTED RESULT: ✅ SUCCESS
├─ User created in database
├─ email_verified = True
├─ is_active = True
└─ Can login normally
```

---

### Test 2: Paste OTP Auto-Fill

```
Goal: Test automatic paste detection

Step 1: Get OTP Email
├─ Receive registration OTP
├─ Copy code: 482651 (including any spaces)
└─ Ready to paste

Step 2: On OTP Page
├─ Click first digit box
├─ Right-click → Paste (or Ctrl+V)
├─ Should see:
│  ✓ Boxes 1-6 filled: [4] [8] [2] [6] [5] [1]
│  ✓ Toast: "OTP pasted successfully!"
│  ✓ Verify button: ENABLED
└─ Ready to submit

Step 3: Verify
├─ Click "Verify OTP"
├─ See success message
└─ Account created

EXPECTED RESULT: ✅ SUCCESS
├─ All 6 boxes filled from paste
├─ Toast notification appeared
└─ Verification completed
```

---

### Test 3: Invalid OTP Error

```
Goal: Test error handling for wrong OTP

Step 1: On OTP Page
├─ Timer showing 09:45
└─ All boxes empty [0] [0] [0] [0] [0] [0]

Step 2: Enter Wrong OTP
├─ Click box 1, type: 0
├─ Auto-focus, type: 0
├─ Auto-focus, type: 0
├─ Auto-focus, type: 0
├─ Auto-focus, type: 0
├─ Auto-focus, type: 0
└─ All boxes show: [0] [0] [0] [0] [0] [0]

Step 3: Click Verify with Wrong OTP
├─ Toast appears: Loading (spinner)
├─ Server validates: Not matching
├─ Response: 400 Bad Request
└─ Expected error:

IMMEDIATE FEEDBACK:
✓ Boxes turn RED border
✓ Shake animation: boxes wiggle left-right
✓ Error message appears in red:
  "Invalid OTP code. 2 attempt(s) remaining."
✓ Boxes are NOT cleared
✓ Verify button disabled until re-entry
✓ Timer still counting

EXPECTED RESULT: ✅ CORRECT BEHAVIOR
├─ Error clearly displayed
├─ Shake animation seen
├─ 2 attempts remaining shown
├─ Can retry with different OTP
└─ Toast notification appeared
```

---

### Test 4: Max Attempts Exceeded

```
Goal: Enforce 3-attempt limit

Step 1: Enter Wrong OTP (Attempt 1)
├─ Enter: 000000
├─ Click Verify
├─ Error: "Invalid OTP code. 2 attempt(s) remaining."
└─ Shake animation shows

Step 2: Enter Wrong OTP (Attempt 2)
├─ Clear boxes mentally
├─ Enter: 111111
├─ Click Verify
├─ Error: "Invalid OTP code. 1 attempt(s) remaining."
└─ Shake animation shows

Step 3: Enter Wrong OTP (Attempt 3 - Last)
├─ Enter: 222222
├─ Click Verify
├─ Error: "Maximum OTP attempts reached. Please resend OTP."
└─ Shake animation shows

IMMEDIATE FEEDBACK:
✓ All 6 input boxes turn GRAY (disabled)
✓ They appear grayed out/faded
✓ Click on them: No cursor visible
✓ Typing in them: Nothing happens
✓ "Verify OTP" button: Still visible but disabled
✓ "Resend OTP" button: ENABLED (blue, clickable)
✓ Error message stays visible

EXPECTED RESULT: ✅ CORRECT BEHAVIOR
├─ 3 attempts strictly enforced
├─ Inputs locked
├─ Can only resend OTP now
└─ No way to bypass attempt limit
```

---

### Test 5: OTP Expiry Timeout

```
Goal: Enforce 10-minute expiry

Method 1: Manual Wait
├─ Start registration
├─ Don't do anything
├─ Wait 10 minutes
├─ Observe timer reaches 00:00
└─ Proceed to step 2

Method 2: Clear Browser Cache (Simulate)
├─ Register and get OTP
├─ Let timer count down (optional)
├─ Browser DevTools → Application → LocalStorage
├─ Delete timer-related data
└─ Open application, it thinks expired

EXPECTED FEEDBACK AT 00:00:
✓ Timer shows: 00:00
✓ Timer color: RED (warning color)
✓ Error message: "OTP has expired. Please request a new one."
✓ All 6 input boxes: GRAY/DISABLED
✓ Typing in boxes: No effect
✓ "Verify OTP" button: DISABLED
✓ "Resend OTP" button: ENABLED (only active button)
✓ Toast notification: "OTP expired!"

USER ACTION:
1. Click "Resend OTP" button
2. Animation: Spinner shows "Sending..."
3. Server generates new OTP
4. Email sent with new OTP
5. Toast: "OTP sent successfully!"
6. Timer reset to: 10:00
7. Input boxes: Re-enabled (no longer gray)
8. All inputs: Cleared (ready for new OTP)
9. Timer: Counting down again

EXPECTED RESULT: ✅ CORRECT BEHAVIOR
├─ Expiry enforced at 10:00
├─ Inputs locked after expiry
├─ Resend works
├─ New timer starts
└─ Can enter new OTP
```

---

### Test 6: Resend OTP with Cooldown

```
Goal: Test 60-second rate limiting

Step 1: On OTP Page
├─ See: "Didn't receive OTP?"
├─ Button: "Resend OTP" (ENABLED, blue)
└─ Text: "Resend available after 60s" (grayed)

Step 2: Click Resend Button
├─ Button changes: Shows spinner icon
├─ Text: "Sending..." or similar
├─ Wait 1-2 seconds
├─ Server sends email
└─ New OTP generated

Step 3: Resend Success
├─ Toast appears: "OTP sent successfully!"
├─ Button returns to: "↻ Resend OTP"
├─ Button is now: DISABLED (grayed)
├─ Text updates to: "Resend available after 60s"
├─ Timer starts: 60, 59, 58, 57...
└─ Counting down

Step 4: Try to Click Again (Before 60s)
├─ Click "Resend OTP" button
├─ Nothing happens (disabled)
├─ Message still shows: "Resend available after 45s"
├─ Button still appears grayed
└─ Can't click

Step 5: Wait 60 Seconds
├─ Counter: 10, 9, 8...
├─ Counter: 3, 2, 1
├─ Counter reaches: 0
├─ Button re-enables: Blue, clickable
├─ Text updates: "↻ Resend OTP"
├─ Ready to resend again

EXPECTED RESULT: ✅ CORRECT BEHAVIOR
├─ Rate limiting enforced
├─ 60-second cooldown between resends
├─ Countdown clearly shown
├─ Button disabled while waiting
├─ Can resend after cooldown expires
└─ New OTP successfully sent
```

---

### Test 7: Keyboard Navigation

```
Goal: Test keyboard-only input (no mouse needed)

Step 1: Open OTP Page
└─ Tab focus to first input box

Step 2: Type Digits with Auto-Focus
├─ Press: 1 → Focus moves to box 2
├─ Press: 2 → Focus moves to box 3
├─ Press: 3 → Focus moves to box 4
├─ Press: 4 → Focus moves to box 5
├─ Press: 5 → Focus moves to box 6
├─ Press: 6 → Focus stays on box 6
└─ Result: [1] [2] [3] [4] [5] [6]

Step 3: Navigate with Arrow Keys
├─ Currently in box 6
├─ Press LEFT arrow → Focus goes to box 5
├─ Press RIGHT arrow → Focus goes to box 6
├─ Press LEFT x5 → Focus goes to box 1
└─ Testing navigation works

Step 4: Delete with Backspace
├─ In box 3, have value: 3
├─ Press Backspace → Value cleared
├─ Expected: Focus goes to box 2
├─ Result: [1] [2] [] [4] [5] [6]

Step 5: Submit with Enter
├─ All 6 boxes filled: [1] [2] [3] [4] [5] [6]
├─ Press Enter key
├─ Expected: Form submits (OTP verification happens)
├─ Toast shows: Loading/verifying
└─ Response follows

EXPECTED RESULT: ✅ CORRECT BEHAVIOR
├─ All keyboard navigation works
├─ Arrow keys move left/right
├─ Backspace deletes and goes back
├─ Enter key submits form
├─ No mouse/touch needed
└─ Fully keyboard accessible
```

---

### Test 8: Mobile Responsiveness

```
Goal: Test on mobile device or mobile view

Step 1: Desktop Chrome
├─ Open: http://localhost:8000/register-multi-step/
├─ Press F12 (DevTools)
├─ Click phone icon (Device Toolbar)
├─ Select: iPhone X or similar
├─ See page at ~375px width
└─ Observe:

EXPECTED MOBILE VIEW:
✓ Single column layout
✓ OTP boxes: Smaller but still readable
✓ Gaps between boxes: Still visible
✓ Buttons: Full width or stacked
✓ Text: Readable (font size adequate)
✓ No horizontal scroll
✓ Tap targets: Large enough (>44x44dp)
✓ Timer: Still visible
✓ Input focus: Still works on touch

Step 2: Actual Mobile Phone
├─ Get phone (iPhone or Android)
├─ Open: http://your-server/register-multi-step/
├─ Complete registration
├─ Navigate to OTP page
└─ Observe:

EXPECTATIONS:
✓ Page loads quickly
✓ Layout adapts to screen
✓ Boxes touch-friendly (not too small)
✓ Keyboard appears on input click
✓ Can paste OTP from email app
✓ Swipe left/right works
✓ No layout break at any zoom level
✓ Inputs remain in focus
✓ Toast notification visible
✓ Timer readable

EXPECTED RESULT: ✅ CORRECT BEHAVIOR
├─ Fully responsive design
├─ Works on all screen sizes
├─ Touch-friendly interface
└─ No horizontal scrolling needed
```

---

## 🔍 Final Verification

### Checklist 1: Before Testing
- [ ] Django server running: http://localhost:8000/
- [ ] .env file created with email config
- [ ] Browser can open registration page
- [ ] Email account ready (Gmail or check console)
- [ ] Test email addresses available

### Checklist 2: Registration Step
- [ ] Form loads without errors
- [ ] All fields present (username, email, mobile, etc.)
- [ ] Form validates in real-time
- [ ] Submit button works
- [ ] Redirects to OTP page

### Checklist 3: OTP Step
- [ ] Page loads with 6 empty boxes
- [ ] Timer shows 10:00
- [ ] Email received with OTP
- [ ] OTP code visible in email
- [ ] Can click and type in boxes

### Checklist 4: Verification
- [ ] Valid OTP accepted
- [ ] Success message shown
- [ ] Account created (check database)
- [ ] Redirects to login
- [ ] Can login with new account

### Checklist 5: Error Handling
- [ ] Invalid OTP rejected with error
- [ ] Max attempts enforced
- [ ] Resend works with cooldown
- [ ] Timer counts down correctly
- [ ] Keyboard navigation works

---

## 🐛 Troubleshooting During Testing

### Issue: "OTP not sending"
```
1. Check console backend:
   - Look at Django server console
   - Should show EMAIL output
   - Copy OTP code from console

2. Check SMTP backend:
   - .env file has correct Gmail address
   - .env file has correct app password
   - Gmail account has 2FA enabled
   - Restart Django after .env change

3. Check email inbox:
   - Check Spam/Junk folder
   - Check sender: noreply@grampanchayat.gov.in
   - Check subject: "Registration OTP"
```

### Issue: "Invalid OTP when using correct OTP"
```
1. Use MOST RECENT OTP from email
   - Not old OTP from previous resend

2. Check OTP format:
   - 6 digits only: 482651
   - Not with spaces: 482 651 (WRONG)
   - Not with dashes: 482-651 (WRONG)

3. Check timer not expired:
   - Is timer showing 00:00?
   - If yes, need to resend

4. Check console output:
   - Did OTP code match what you entered?
```

### Issue: "Inputs frozen or not responding"
```
1. Refresh page: F5
   - Reloads JavaScript
   - Clears any stuck state

2. Check browser console:
   - F12 → Console tab
   - Look for red error messages
   - Report any errors you see

3. Check timer:
   - If 00:00, inputs intentionally disabled
   - Click "Resend OTP" to fix

4. Try different browser:
   - Chrome, Firefox, Safari, Edge
   - See if issue persists
```

### Issue: "Resend button not working"
```
1. Check if button is disabled:
   - Is it grayed out?
   - Shows "Resend in 45s"?
   - Wait for cooldown to expire

2. Check network:
   - Is internet connection stable?
   - Try again after a few seconds
   - Check browser network tab (F12 → Network)

3. Check server:
   - Is Django still running?
   - Any error messages in console?
   - Restart if needed: Ctrl+C, python manage.py runserver
```

---

## ✅ Sign-Off

After completing all tests above:

- [ ] Registration form works
- [ ] OTP email sending works
- [ ] OTP verification works
- [ ] Account creation works
- [ ] Login works
- [ ] Error handling works
- [ ] Resend works
- [ ] Mobile responsive works
- [ ] Keyboard navigation works
- [ ] All animations work

**Status:** ✅ **READY FOR DEPLOYMENT**

---

**Good luck with testing! 🎉**

If any issues, refer to `OTP_VERIFICATION_COMPLETE_GUIDE.md` for detailed troubleshooting.
