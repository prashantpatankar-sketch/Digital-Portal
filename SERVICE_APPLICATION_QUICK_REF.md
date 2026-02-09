# Service Application System - Quick Reference

## 🚀 Quick Start

### For Citizens

```python
# Apply for Birth Certificate
URL: /apply-birth-certificate/
Decorator: @citizen_required
Redirect: application_detail

# Apply for Death Certificate  
URL: /apply-death-certificate/
Decorator: @citizen_required
Redirect: application_detail

# Apply for Income Certificate
URL: /apply-income-certificate/
Decorator: @citizen_required
Redirect: application_detail

# Pay Tax (Water/House)
URL: /pay-tax/
Decorator: @citizen_required
Redirect: application_detail

# View My Applications
URL: /my-applications/
Decorator: @citizen_required
Features: Pagination, Status filter

# View Application Detail
URL: /application/<id>/
Decorator: @citizen_required
Features: Full details, Status history, Certificate download
```

### For Staff/Admin

```python
# Applications Dashboard
URL: /admin/applications/
Decorator: @staff_or_admin_required
Features: Filter, Search, Pagination

# Review Application
URL: /admin/review-application/<id>/
Decorator: @staff_or_admin_required
Features: Approve/Reject, Generate certificate, Add remarks
```

## 📦 Helper Functions

### 1. Create Status History

```python
from portal_app.views import create_status_history

create_status_history(
    application=application_instance,
    old_status='pending',          # or None for initial
    new_status='approved',         # required
    changed_by=request.user,       # required
    remarks='Optional comment'     # optional
)
```

**Usage Example:**
```python
# In application submission
create_status_history(
    application=application,
    old_status=None,
    new_status='pending',
    changed_by=request.user,
    remarks='Birth certificate application submitted'
)

# In status change
old = application.status
application.status = 'approved'
application.save()

create_status_history(
    application=application,
    old_status=old,
    new_status='approved',
    changed_by=request.user,
    remarks='All documents verified'
)
```

### 2. Generate Certificate Number

```python
from portal_app.views import generate_certificate_number

cert_number = generate_certificate_number('birth_certificate')
# Returns: CERTBIRT20240115143022

cert_number = generate_certificate_number('income_certificate')
# Returns: CERTINCO20240115143022
```

**Format:**
- `CERT` + First 4 letters of type + Timestamp
- Example: `CERTBIRT20240115143022`
- Always unique based on timestamp

### 3. Get Application Statistics

```python
from portal_app.views import get_application_statistics

# For specific user
stats = get_application_statistics(request.user)

# Returns dictionary:
{
    'total': 25,
    'pending': 10,
    'under_review': 2,
    'approved': 12,
    'rejected': 1
}
```

**Usage in Dashboard:**
```python
@citizen_required
def dashboard(request):
    stats = get_application_statistics(request.user)
    context = {
        'total_apps': stats['total'],
        'pending_apps': stats['pending'],
        'approved_apps': stats['approved']
    }
    return render(request, 'dashboard.html', context)
```

## 🔄 Application Workflow Code

### Standard Application Submission Pattern

```python
@citizen_required
def apply_for_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Create Application
            application = Application.objects.create(
                applicant=request.user,
                application_type='service_type',  # birth_certificate, etc.
                status='pending'
            )
            
            # 2. Create Service Record (linked to Application)
            service = form.save(commit=False)
            service.application = application
            service.save()
            
            # 3. Create Status History
            create_status_history(
                application=application,
                old_status=None,
                new_status='pending',
                changed_by=request.user,
                remarks='Service application submitted'
            )
            
            # 4. Success Message
            messages.success(
                request,
                f'<strong>Application submitted!</strong><br>'
                f'Application Number: <strong>{application.application_number}</strong>',
                extra_tags='safe'
            )
            
            # 5. Redirect to Detail
            return redirect('application_detail', application_id=application.id)
    else:
        form = ServiceForm()
    
    return render(request, 'form_template.html', {'form': form})
```

### Standard Review/Approval Pattern

```python
@staff_or_admin_required
def review_application(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    
    # Get linked service data
    service_data = application.birth_certificate  # or other service
    
    if request.method == 'POST':
        form = ApplicationReviewForm(request.POST, instance=application)
        if form.is_valid():
            old_status = application.status
            updated_app = form.save(commit=False)
            updated_app.reviewed_by = request.user
            updated_app.reviewed_date = timezone.now()
            
            # Only create history if status changed
            if old_status != updated_app.status:
                updated_app.save()
                
                # Create status history
                create_status_history(
                    application=updated_app,
                    old_status=old_status,
                    new_status=updated_app.status,
                    changed_by=request.user,
                    remarks=updated_app.admin_remarks
                )
                
                # If approved, generate certificate
                if updated_app.status == 'approved' and service_data:
                    if not service_data.certificate_number:
                        service_data.certificate_number = generate_certificate_number(
                            application.application_type
                        )
                        service_data.issued_date = timezone.now().date()
                        service_data.save()
                
                messages.success(
                    request, 
                    f'Application {updated_app.application_number} {updated_app.status}!'
                )
            else:
                updated_app.save()
                messages.info(request, 'Application updated.')
            
            return redirect('admin_applications')
    else:
        form = ApplicationReviewForm(instance=application)
    
    # Get status history for timeline
    status_history = application.status_history.all().order_by('-changed_at')
    
    context = {
        'application': application,
        'service_data': service_data,
        'form': form,
        'status_history': status_history,
    }
    return render(request, 'review_template.html', context)
```

## 📊 Database Queries

### Get Applications by Status

```python
# All pending applications
pending = Application.objects.filter(status='pending')

# User's approved applications
approved = Application.objects.filter(
    applicant=request.user,
    status='approved'
)

# Applications with certificate numbers
with_certs = Application.objects.filter(
    birth_certificate__certificate_number__isnull=False
)
```

### Get Application with Related Data

```python
# Single application with all related data
application = Application.objects.select_related(
    'applicant',
    'reviewed_by',
    'birth_certificate',
    'death_certificate',
    'income_certificate',
    'tax_payment'
).prefetch_related(
    'status_history'
).get(pk=application_id)

# Access related data
if application.application_type == 'birth_certificate':
    cert = application.birth_certificate
    print(f"Child Name: {cert.child_name}")
    print(f"Certificate: {cert.certificate_number}")
```

### Status History Queries

```python
# Get history for an application (ordered newest first)
history = ApplicationStatusHistory.objects.filter(
    application=application
).order_by('-changed_at')

# Get all changes by a specific user
admin_changes = ApplicationStatusHistory.objects.filter(
    changed_by=admin_user
)

# Get recent approvals (last 7 days)
from datetime import timedelta
recent = ApplicationStatusHistory.objects.filter(
    new_status='approved',
    changed_at__gte=timezone.now() - timedelta(days=7)
)
```

## 🎨 Template Examples

### Display Application Status

```html
<!-- Status Badge -->
<span class="badge bg-{{ application.status|status_color }}">
    {{ application.get_status_display }}
</span>

<!-- Custom template filter for colors -->
{% load portal_filters %}
<span class="badge bg-{{ application.status|status_badge }}">
    {{ application.status|title }}
</span>
```

### Status History Timeline

```html
<div class="timeline">
    {% for history in status_history %}
    <div class="timeline-item">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
            <h6>{{ history.new_status|title }}</h6>
            <p class="text-muted">
                {{ history.changed_at|date:"M d, Y H:i" }}
                by {{ history.changed_by.get_full_name }}
            </p>
            {% if history.remarks %}
            <p>{{ history.remarks }}</p>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
```

### Application List with Filters

```html
<form method="get">
    <select name="status" onchange="this.form.submit()">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
    </select>
</form>

{% for app in applications %}
<div class="card mb-3">
    <div class="card-body">
        <h5>{{ app.application_number }}</h5>
        <p>Type: {{ app.get_application_type_display }}</p>
        <p>Status: {{ app.get_status_display }}</p>
        <a href="{% url 'application_detail' app.id %}">View Details</a>
    </div>
</div>
{% endfor %}
```

## 🔒 Access Control Patterns

### View Protection

```python
# Single role
@citizen_required
def citizen_only_view(request):
    ...

@staff_required
def staff_only_view(request):
    ...

@admin_required
def admin_only_view(request):
    ...

# Multiple roles
@staff_or_admin_required
def staff_or_admin_view(request):
    ...

@role_required(['admin', 'staff'])
def custom_roles_view(request):
    ...
```

### Manual Permission Checks

```python
# In view
if request.user.role != 'admin':
    messages.error(request, 'Admin access required')
    return redirect('home')

# In template
{% if user.role == 'admin' %}
<a href="{% url 'admin_dashboard' %}">Admin Panel</a>
{% endif %}
```

## 📱 Success Message Patterns

### Simple Message

```python
messages.success(request, 'Application submitted successfully!')
```

### HTML-Formatted Message

```python
messages.success(
    request,
    f'<strong>Success!</strong><br>'
    f'Application Number: <strong>{app.application_number}</strong>',
    extra_tags='safe'
)
```

### Conditional Messages

```python
if application.status == 'approved':
    messages.success(request, 'Application approved!')
elif application.status == 'rejected':
    messages.warning(request, 'Application rejected. Check remarks.')
else:
    messages.info(request, 'Application status updated.')
```

## 🧪 Testing Quick Commands

```bash
# Create test applications
python manage.py shell
>>> from portal_app.models import *
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> citizen = User.objects.get(role='citizen')
>>> app = Application.objects.create(
...     applicant=citizen,
...     application_type='birth_certificate',
...     status='pending'
... )
>>> print(app.application_number)

# Check status history
>>> app.status_history.all()

# Generate certificate number
>>> from portal_app.views import generate_certificate_number
>>> cert_num = generate_certificate_number('birth_certificate')
>>> print(cert_num)

# Get statistics
>>> from portal_app.views import get_application_statistics
>>> stats = get_application_statistics(citizen)
>>> print(stats)
```

## 📋 Common URL Patterns

```python
# portal_app/urls.py
urlpatterns = [
    # Citizen URLs
    path('apply-birth-certificate/', views.apply_birth_certificate, name='apply_birth_certificate'),
    path('apply-death-certificate/', views.apply_death_certificate, name='apply_death_certificate'),
    path('apply-income-certificate/', views.apply_income_certificate, name='apply_income_certificate'),
    path('pay-tax/', views.pay_tax, name='pay_tax'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    path('track-application/', views.track_application, name='track_application'),
    
    # Admin URLs
    path('admin/applications/', views.admin_applications, name='admin_applications'),
    path('admin/review-application/<int:application_id>/', views.admin_review_application, name='admin_review_application'),
]
```

## 🎯 Key Points to Remember

1. **Always create status history** on status changes
2. **Use helper functions** for code reusability
3. **Redirect to detail page** after submission (better UX)
4. **Format success messages** with HTML for clarity
5. **Check old vs new status** before creating history
6. **Generate certificate number** only on approval
7. **Set reviewed_by and reviewed_date** on review
8. **Use decorators** for access control
9. **Include remarks** in status history for audit trail
10. **Test all workflows** thoroughly

## 📚 File Locations

```
portal_app/
├── models.py           # Application, Certificate, StatusHistory models
├── forms.py            # Application and Review forms
├── views.py            # Helper functions and view logic
├── decorators.py       # @citizen_required, @staff_or_admin_required
├── middleware.py       # RoleBasedAccessMiddleware
├── urls.py             # URL routing
└── templates/
    └── portal_app/
        ├── citizen/    # Application forms
        └── admin/      # Review interface
```

---

**Quick Tip**: Always check [SERVICE_APPLICATION_SYSTEM.md](SERVICE_APPLICATION_SYSTEM.md) for detailed workflow diagrams and comprehensive documentation.
