# Complaint Management System - Complete Guide

## Overview

The Complaint Management System allows citizens to file complaints about various civic issues (water supply, electricity, roads, sanitation, etc.) and enables staff/admin to manage, assign, track, and resolve these complaints with complete audit trail.

---

## Table of Contents

1. [Features](#features)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Complaint Categories](#complaint-categories)
4. [Complaint Lifecycle](#complaint-lifecycle)
5. [Citizen Guide](#citizen-guide)
6. [Staff/Admin Guide](#staffadmin-guide)
7. [Technical Implementation](#technical-implementation)
8. [Database Models](#database-models)

---

## Features

### For Citizens
- ✅ File new complaints with photo evidence
- ✅ Track complaint status in real-time
- ✅ View detailed complaint history timeline
- ✅ Filter complaints by status
- ✅ Dashboard with statistics (Total, Open, Resolved)
- ✅ Email/phone notifications (if configured)

### For Staff/Admin
- ✅ View all complaints with advanced filtering
- ✅ Assign complaints to staff members
- ✅ Update complaint status (Open → In Progress → Resolved → Closed)
- ✅ Set/change priority levels
- ✅ Add resolution remarks
- ✅ Complete audit trail of all actions
- ✅ Statistics dashboard
- ✅ Filter by: Status, Category, Priority, Assignment

---

## User Roles & Permissions

### Citizen
- File complaints
- View own complaints
- Track complaint progress
- View resolution details

### Staff
- View all complaints
- Update complaint status
- Assign complaints (to self or others)
- Change priority
- Add resolution remarks
- View full audit history

### Admin
- All staff permissions
- Delete complaints (via Django admin)
- Manage complaint categories
- Generate reports

---

## Complaint Categories

| Category | Description | Example Issues |
|----------|-------------|----------------|
| **Water Supply** | Water-related issues | No water, low pressure, contamination |
| **Electricity** | Power supply problems | Outages, voltage fluctuations |
| **Road & Infrastructure** | Road conditions | Potholes, broken roads, construction |
| **Sanitation** | Cleanliness issues | Garbage not collected, dirty areas |
| **Street Light** | Street lighting problems | Non-functional lights, dark areas |
| **Drainage** | Drainage system issues | Blocked drains, flooding |
| **Waste Management** | Waste disposal problems | Waste not picked up, illegal dumping |
| **Other** | Other civic issues | Miscellaneous complaints |

---

## Complaint Lifecycle

```
┌─────────────┐
│   CITIZEN   │ Files complaint with details
│  FILES NEW  │ Category, Subject, Description, Location, Photo
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    OPEN     │ Status: Open
│             │ Priority: Set by system/staff
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ASSIGNED   │ Staff/Admin assigns to team member
│             │ History: "Assigned to [Staff Name]"
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ IN PROGRESS │ Staff updates status to "In Progress"
│             │ Working on resolution
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  RESOLVED   │ Staff marks as resolved
│             │ Resolution remarks added
│             │ Resolved date automatically set
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   CLOSED    │ Final status (optional)
│             │ Complaint archived
└─────────────┘
```

### Status Definitions

| Status | Badge Color | Meaning |
|--------|-------------|---------|
| **Open** | 🔴 Red | Newly filed, awaiting assignment |
| **In Progress** | 🟡 Yellow | Assigned and being worked on |
| **Resolved** | 🟢 Green | Issue fixed, resolution remarks added |
| **Closed** | ⚫ Gray | Finalized, archived |

### Priority Levels

| Priority | Badge Color | Response Time | Use Case |
|----------|-------------|---------------|----------|
| **Urgent** | 🔴 Red | < 24 hours | Health/safety issues, major outages |
| **High** | 🟠 Orange | < 3 days | Significant impact on community |
| **Medium** | 🔵 Blue | < 7 days | Regular maintenance issues |
| **Low** | ⚪ Gray | < 14 days | Minor issues, cosmetic problems |

---

## Citizen Guide

### How to File a Complaint

1. **Login** to your citizen account
2. Navigate to **"File Complaint"** from menu or dashboard
3. Fill in complaint details:
   - **Category**: Select from dropdown (Water Supply, Electricity, etc.)
   - **Subject**: Brief title (e.g., "Water supply disrupted in Sector 5")
   - **Description**: Detailed explanation of the issue
   - **Location**: Specific address or landmark
   - **Priority**: Select urgency level
   - **Photo** (Optional): Upload supporting evidence
4. Click **"Submit Complaint"**
5. Note your **Complaint Number** (e.g., CMP20240001)

### Tracking Your Complaints

1. Go to **"My Complaints"**
2. View dashboard statistics:
   - Total Complaints
   - Open/In Progress
   - Resolved
3. Use status filters: Open, In Progress, Resolved
4. Click **"View"** on any complaint to see:
   - Full details
   - Current status and priority
   - Assignment status
   - Complete activity timeline
   - Resolution remarks (if resolved)

### Understanding the Timeline

The timeline shows every action taken on your complaint:
- 🟣 **Created**: When you filed the complaint
- 🔵 **Assigned**: When staff member was assigned
- 🟡 **Status Changed**: Status updates
- 🔴 **Priority Changed**: Priority adjustments
- 🟢 **Resolved**: When issue was fixed

---

## Staff/Admin Guide

### Viewing All Complaints

1. Navigate to **Admin > Manage Complaints**
2. View statistics dashboard:
   - Total Complaints
   - Open
   - In Progress
   - Resolved
   - Unassigned
   - Urgent

### Filtering Complaints

Use filters to find specific complaints:
- **Status**: Open, In Progress, Resolved, Closed
- **Category**: Water Supply, Electricity, Road, etc.
- **Priority**: Urgent, High, Medium, Low
- **Assignment**: Assigned to Me, Unassigned, All

**Example**: Show urgent unassigned complaints:
- Priority: Urgent
- Assignment: Unassigned

### Updating a Complaint

1. Click **Edit** button on any complaint
2. View complainant information:
   - Name, Phone, Email
   - Filed date
3. Review complaint details:
   - Category, Subject, Description
   - Location, Photo evidence
4. Update complaint:
   - **Assigned To**: Select staff member from dropdown
   - **Status**: Change to In Progress/Resolved/Closed
   - **Priority**: Adjust as needed
   - **Resolution Remarks**: Add notes (required for resolution)
5. Click **"Update Complaint"**

### Best Practices

#### Assignment
- Assign complaints based on category expertise
- Don't leave urgent complaints unassigned
- Reassign if staff unavailable

#### Status Updates
- Update status promptly when work begins
- Add resolution remarks with specific details
- Mark resolved only when issue truly fixed

#### Priority Management
- Urgent: Health/safety, major infrastructure
- High: Affecting multiple households
- Medium: Single household, scheduled maintenance
- Low: Cosmetic, non-critical

#### Resolution Remarks
✅ **Good**: "Water supply restored. Replaced damaged pipe in Sector 5, B-Block. Tested water pressure - normal."

❌ **Bad**: "Fixed"

---

## Technical Implementation

### URLs Configuration

```python
# Citizen URLs
path('file-complaint/', views.file_complaint, name='file_complaint')
path('my-complaints/', views.my_complaints, name='my_complaints')
path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail')

# Staff/Admin URLs
path('admin/complaints/', views.admin_complaints, name='admin_complaints')
path('admin/update-complaint/<int:complaint_id>/', views.admin_update_complaint, name='admin_update_complaint')
```

### Permissions

All complaint management views use decorators:
- `@login_required`: For citizen views
- `@staff_or_admin_required`: For admin views

### File Uploads

Complaint photos are stored in:
```
media/complaints/
```

Supported formats: JPG, PNG, GIF
Max size: 5 MB (configurable in settings)

---

## Database Models

### Complaint Model

```python
class Complaint(models.Model):
    complaint_number = CharField(unique=True)  # Auto-generated: CMP20240001
    complainant = ForeignKey(CustomUser)       # Who filed it
    category = CharField(choices=CATEGORIES)    # Water, Electricity, etc.
    subject = CharField(max_length=200)        # Brief title
    description = TextField()                  # Detailed explanation
    location = CharField(max_length=200)       # Address
    priority = CharField(choices=PRIORITIES)   # Urgent, High, Medium, Low
    status = CharField(choices=STATUSES)       # Open, In Progress, Resolved, Closed
    assigned_to = ForeignKey(CustomUser)       # Assigned staff (nullable)
    filed_date = DateTimeField(auto_now_add)   # When filed
    resolved_date = DateTimeField(null=True)   # When resolved
    resolution_remarks = TextField(blank=True) # Resolution notes
    complaint_photo = ImageField(upload_to='complaints/', blank=True)
```

### ComplaintHistory Model

Tracks all changes to complaints:

```python
class ComplaintHistory(models.Model):
    complaint = ForeignKey(Complaint)          # Related complaint
    action = CharField(choices=ACTIONS)        # Type of action
    old_value = CharField(blank=True)          # Previous value
    new_value = CharField(blank=True)          # New value
    performed_by = ForeignKey(CustomUser)      # Who made the change
    performed_at = DateTimeField(auto_now_add) # When changed
    notes = TextField(blank=True)              # Additional context
```

### Action Types

| Action | When Triggered | Old Value | New Value |
|--------|----------------|-----------|-----------|
| `created` | Complaint filed | - | - |
| `assigned` | Staff assigned | Previous assignee | New assignee |
| `status_changed` | Status updated | Old status | New status |
| `priority_changed` | Priority updated | Old priority | New priority |
| `updated` | Any other change | - | - |
| `resolved` | Marked resolved | - | Resolution remarks |
| `closed` | Marked closed | - | - |

---

## Statistics & Analytics

### Citizen Dashboard
- Total Complaints Filed
- Open/In Progress Count
- Resolved Count

### Admin Dashboard
- Total Complaints (System-wide)
- Open Complaints
- In Progress Complaints
- Resolved Complaints
- Unassigned Complaints
- Urgent Active Complaints

---

## Notifications (Optional Enhancement)

To enable email notifications:

1. Configure email settings in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

2. Add notification triggers in views:
   - New complaint filed → Email to admin
   - Complaint assigned → Email to assigned staff
   - Status changed → Email to complainant
   - Complaint resolved → Email to complainant

---

## Troubleshooting

### Common Issues

**Q: Photos not uploading?**
- Check `MEDIA_ROOT` and `MEDIA_URL` in settings.py
- Verify folder permissions: `media/complaints/`
- Check file size (max 5MB)

**Q: Can't see complaint history?**
- Ensure migration applied: `python manage.py migrate`
- Check model import in views
- Verify history queryset in view

**Q: Assignment dropdown empty?**
- Ensure users have `is_staff=True` or `is_admin=True`
- Check ComplaintUpdateForm queryset

**Q: Statistics not showing?**
- Verify view calculations
- Check context variables in template
- Ensure template variables match view context

---

## Future Enhancements

- [ ] Email notifications for status changes
- [ ] SMS alerts for urgent complaints
- [ ] Mobile app integration
- [ ] Complaint analytics dashboard
- [ ] Auto-assignment based on category
- [ ] SLA (Service Level Agreement) tracking
- [ ] Citizen feedback/rating system
- [ ] Complaint attachments (multiple files)
- [ ] Geo-location mapping
- [ ] Export complaints to Excel/PDF

---

## API Endpoints (Optional)

For mobile app or external integrations:

```
GET  /api/complaints/          - List all complaints
POST /api/complaints/          - Create new complaint
GET  /api/complaints/{id}/     - Get complaint details
PUT  /api/complaints/{id}/     - Update complaint
GET  /api/complaints/{id}/history/ - Get complaint history
```

---

## Support

For technical issues or questions:
- Email: support@grampanchayat.gov.in
- Phone: 1800-XXX-XXXX
- Portal: Help & Support section

---

**Version**: 1.0
**Last Updated**: January 2024
**Status**: ✅ Production Ready
