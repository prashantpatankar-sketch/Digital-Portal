# Premium Multi-Step Registration - Quick Start

## 🚀 Quick Access

### User Access
```
URL: /register-multi-step/
```

### Testing
```bash
# Test without OTP setup
1. Fill all 3 steps
2. Review preview
3. Submit - will attempt email OTP
```

---

## 📋 Quick Reference

### Component Files
```
Templates:   portal_app/templates/portal_app/register-multi-step.html
CSS:         portal_app/static/portal_app/css/register-multistep.css
JavaScript:  portal_app/static/portal_app/js/register-multistep.js
Views:       portal_app/views.py (register_multi_step_view function)
URLs:        portal_app/urls.py (register_multi_step route)
```

### Key Classes & Functions

**JavaScript:**
```javascript
// Main class
class RegistrationForm

// Key methods
nextStep()              // Navigate to next step
previousStep()          // Go back one step
validateCurrentStep()   // Validate before moving
saveFormData()          // Save to localStorage
loadStoredData()        // Restore from localStorage
generatePreview()       // Generate preview data
handleSubmit()          // Submit form
```

**Django:**
```python
def register_multi_step_view(request):
    # Handles GET (show form) and POST (process submission)
```

---

## 🎨 Customization Examples

### 1. Change Progress Steps
**File:** `register-multi-step.html` (line ~25)
```html
<!-- Add/remove step indicators -->
<div class="step-indicator" data-step="5">
    <div class="step-number">5</div>
    <div class="step-label">Step Name</div>
</div>
```

**JavaScript:** Update `totalSteps`:
```javascript
this.totalSteps = 5;  // Changed from 4
```

### 2. Modify Colors
**File:** `register-multistep.css` (line ~1-10)
```css
:root {
    --primary-color: #YourColor;
    --secondary-color: #YourColor;
}
```

### 3. Add New Field
**HTML:**
```html
<div class="form-group">
    <label for="newfield">New Field</label>
    <input type="text" id="newfield" class="form-control">
</div>
```

**JavaScript:**
```javascript
newfield: document.getElementById('newfield').value.trim()
```

**Django View:**
```python
new_field = request.POST.get('newfield', '').strip()
# Add validation...
```

---

## 🔍 Key Features at a Glance

| Feature | Implementation |
|---------|-----------------|
| **3-Step Form** | HTML steps with CSS hidden/visible |
| **Auto-Save** | localStorage + JSON serialization |
| **Progress Bar** | CSS width animation based on step |
| **Validation** | Real-time JS + Server-side Django |
| **Preview** | DOM manipulation of hidden fields |
| **File Upload** | FormData API + drag-drop |
| **Animations** | CSS transitions + keyframes |
| **Responsive** | CSS media queries |

---

## 🧪 Testing Quick Commands

```javascript
// Open browser console
// Check saved data
localStorage.getItem('registrationFormData')

// Clear saved data
localStorage.removeItem('registrationFormData')

// Check form object
console.log(window.registrationForm)

// Manually trigger next step
window.registrationForm.nextStep()

// Get current step
console.log(window.registrationForm.currentStep)
```

---

## ⚡ Performance Tips

✅ **Already Optimized:**
- Lazy validation (blur events)
- Efficient DOM manipulation
- CSS animations use GPU (transform)
- localStorage for fast reload
- Single AJAX POST request

**To Further Optimize:**
- Minify JS and CSS in production
- Use async/defer for script loading
- Enable browser caching headers
- Compress images for upload

---

## 🔐 Security Checklist

✅ Already Implemented:
- CSRF token in form
- Server-side validation
- Password hashing
- File type validation
- File size validation
- Age verification (18+)
- SQL injection prevention
- XSS prevention (Django templates)

---

## 📲 Mobile First Approach

Tested on:
- ✅ iPhone 12 / 13 / 14
- ✅ Samsung Galaxy S20 / S21
- ✅ iPad / iPad Pro
- ✅ Android tablets
- ✅ Desktop (all modern browsers)

---

## 🎯 Main Workflow

```
GET /register-multi-step/ 
  → Show HTML template
  → Load saved localStorage data
  → Display step 1

User fills step 1 fields
  → JS saves to localStorage
  → Real-time validation

User clicks Next
  → Validate step 1
  → Show step 2

... repeat for steps 2 & 3 ...

User clicks Next on step 3
  → Generate preview
  → Show step 4 (preview)

User clicks Submit
  → Send POST with all data + file
  → Server validates
  → Create PendingRegistration
  → Send OTP email
  → Clear localStorage
  → Redirect to OTP verification

User enters OTP
  → Verify OTP
  → Create CustomUser account
  → Login user
  → Redirect to dashboard
```

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Data not saving | Check localStorage quota |
| Image not showing | Verify MIME type in upload |
| OTP not sending | Check EMAIL settings in settings.py |
| Validation failing | Check Django view regex patterns |
| CSS not loading | Verify static files in Django |
| JS not running | Check browser console for errors |

---

## 📞 Support Points

**Frontend Issues:**
- JavaScript console (browser DevTools)
- CSS styling (inspect element)
- localStorage (console commands)

**Backend Issues:**
- Django logs in terminal
- Database queries in shell_plus
- Email configuration in settings.py

---

**Last Updated:** April 2026
**Status:** ✅ Production Ready
**Tested on:** Chrome, Firefox, Safari, Edge (all modern versions)
