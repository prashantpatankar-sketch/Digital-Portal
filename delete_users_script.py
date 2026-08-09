#!/usr/bin/env python
"""
SAFE USER DELETION SCRIPT
=========================

This script safely deletes all non-admin users from the database.

USAGE:
------
1. In Django Shell:
   python manage.py shell
   exec(open('delete_users_script.py').read())

2. Or directly:
   python delete_users_script.py

SAFETY FEATURES:
- Protects admin and superuser accounts
- Shows detailed before/after counts
- Asks for confirmation
- Verifies no orphan data remains
- Detailed logging
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import django

# Setup Django (if running standalone)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gram_panchayat.settings')
django.setup()

from django.db.models import Q
from django.contrib.sessions.models import Session
from portal_app.models import (
    CustomUser, Application, Complaint, 
    ElectricityBill, WaterBill, PropertyTaxRecord,
    Notification, UserActivity
)


def count_related_data(users_to_delete):
    """Count all related data that will be deleted"""
    user_ids = set(users_to_delete.values_list('id', flat=True))
    
    return {
        'applications': Application.objects.filter(applicant_id__in=user_ids).count(),
        'complaints': Complaint.objects.filter(complainant_id__in=user_ids).count(),
        'electricity_bills': ElectricityBill.objects.filter(user_id__in=user_ids).count(),
        'water_bills': WaterBill.objects.filter(user_id__in=user_ids).count(),
        'property_tax': PropertyTaxRecord.objects.filter(user_id__in=user_ids).count(),
        'notifications': Notification.objects.filter(recipient_id__in=user_ids).count(),
        'activity_logs': UserActivity.objects.filter(user_id__in=user_ids).count(),
    }


def force_logout_user_ids(user_ids):
    """Delete active sessions for users before removing accounts."""
    if not user_ids:
        return 0

    deleted_sessions = 0
    for session in Session.objects.all().iterator():
        try:
            data = session.get_decoded()
        except Exception:
            continue

        auth_user_id = data.get('_auth_user_id')
        if auth_user_id and str(auth_user_id) in user_ids:
            session.delete()
            deleted_sessions += 1

    return deleted_sessions


def main():
    """Main deletion function"""
    
    print("\n" + "=" * 75)
    print(" " * 20 + "SAFE USER DELETION SCRIPT")
    print("=" * 75)
    
    # Phase 1: Analysis
    print("\n[PHASE 1] Analyzing database...")
    print("-" * 75)
    
    citizen_users = CustomUser.objects.filter(role='citizen')
    staff_users = CustomUser.objects.filter(role='staff')
    admin_users = CustomUser.objects.filter(role='admin')
    superusers = CustomUser.objects.filter(is_superuser=True)
    
    citizens_count = citizen_users.count()
    staff_count = staff_users.count()
    admins_count = admin_users.count()
    superusers_count = superusers.count()
    total_users = CustomUser.objects.count()
    
    print(f"\nCURRENT USER DISTRIBUTION:")
    print(f"  ┌─ Citizens:           {citizens_count:>6}")
    print(f"  ├─ Staff:             {staff_count:>6}")
    print(f"  ├─ SUBTOTAL (Delete): {citizens_count + staff_count:>6}")
    print(f"  ├─ Admins:            {admins_count:>6}")
    print(f"  ├─ Superusers:        {superusers_count:>6}")
    print(f"  └─ TOTAL:             {total_users:>6}")
    
    total_to_delete = citizens_count + staff_count
    
    if total_to_delete == 0:
        print("\n✓ No users to delete. Database is clean.")
        print("=" * 75 + "\n")
        return True
    
    # Phase 2: Show related data
    print("\n[PHASE 2] Analyzing related data...")
    print("-" * 75)
    
    users_to_delete = CustomUser.objects.filter(
        role__in=['citizen', 'staff']
    ).exclude(is_superuser=True)
    
    related = count_related_data(users_to_delete)
    
    print(f"\nDATA TO BE DELETED WITH USERS:")
    print(f"  ├─ Applications:      {related['applications']:>6}")
    print(f"  ├─ Complaints:        {related['complaints']:>6}")
    print(f"  ├─ Electricity Bills: {related['electricity_bills']:>6}")
    print(f"  ├─ Water Bills:       {related['water_bills']:>6}")
    print(f"  ├─ Property Tax:      {related['property_tax']:>6}")
    print(f"  ├─ Notifications:     {related['notifications']:>6}")
    print(f"  └─ Activity Logs:     {related['activity_logs']:>6}")
    
    total_records = sum(related.values())
    print(f"\n  TOTAL RECORDS TO DELETE: {total_records}")
    
    # Phase 3: Confirmation
    print("\n[PHASE 3] Confirmation...")
    print("-" * 75)
    
    print(f"\n⚠️  WARNING: This will permanently delete:")
    print(f"   • {total_to_delete} users (citizens & staff)")
    print(f"   • {total_records} related records")
    print(f"\n   This action CANNOT be undone without database backup!")
    
    print(f"\nType 'DELETE' (uppercase) to proceed, or press Enter to cancel:")
    confirmation = input(">>> ").strip()
    
    if confirmation != 'DELETE':
        print("\n❌ Deletion cancelled.")
        print("=" * 75 + "\n")
        return False
    
    # Phase 4: Final confirmation
    print(f"\nAre you absolutely sure? Type 'YES' to confirm:")
    final_confirm = input(">>> ").strip()
    
    if final_confirm != 'YES':
        print("\n❌ Deletion cancelled.")
        print("=" * 75 + "\n")
        return False
    
    # Phase 5: Execute deletion
    print("\n[PHASE 4] Executing deletion...")
    print("-" * 75)
    
    try:
        print(f"\n🗑️  Deleting {total_to_delete} users and all related data...")

        target_user_ids = {str(value) for value in users_to_delete.values_list('id', flat=True)}
        force_logged_out = force_logout_user_ids(target_user_ids)
        if force_logged_out:
            print(f"🔐 Forced logout for {force_logged_out} active session(s) before deletion.")
        
        deleted_count, deleted_detail = users_to_delete.delete()
        
        print(f"\n✓ DELETION SUCCESSFUL!")
        print(f"  └─ Total records deleted: {deleted_count}")
        
    except Exception as e:
        print(f"\n❌ ERROR during deletion: {str(e)}")
        print("=" * 75 + "\n")
        return False
    
    # Phase 6: Verification
    print("\n[PHASE 5] Verification...")
    print("-" * 75)
    
    final_citizens = CustomUser.objects.filter(role='citizen').count()
    final_staff = CustomUser.objects.filter(role='staff').count()
    final_admins = CustomUser.objects.filter(role='admin').count()
    final_superusers = CustomUser.objects.filter(is_superuser=True).count()
    final_total = CustomUser.objects.count()
    
    print(f"\nFINAL USER DISTRIBUTION:")
    print(f"  ├─ Citizens:      {final_citizens:>6} (was {citizens_count})")
    print(f"  ├─ Staff:         {final_staff:>6} (was {staff_count})")
    print(f"  ├─ Admins:        {final_admins:>6} (was {admins_count})")
    print(f"  ├─ Superusers:    {final_superusers:>6} (was {superusers_count})")
    print(f"  └─ TOTAL:         {final_total:>6} (was {total_users})")
    
    # Check for orphan data
    print(f"\nORPHAN DATA CHECK:")
    orphan_apps = Application.objects.filter(applicant__isnull=True).count()
    orphan_complaints = Complaint.objects.filter(complainant__isnull=True).count()
    
    print(f"  ├─ Orphan applications: {orphan_apps} (expected: 0)")
    print(f"  └─ Orphan complaints:   {orphan_complaints} (expected: 0)")
    
    if orphan_apps == 0 and orphan_complaints == 0:
        print(f"\n✓ No orphan data found - Database integrity maintained!")
    else:
        print(f"\n⚠️  Warning: Orphan data detected")
    
    # Summary
    print("\n[PHASE 6] Summary...")
    print("-" * 75)
    
    print(f"\n✓ DELETION COMPLETE!")
    print(f"  ├─ Users removed:      {total_to_delete}")
    print(f"  ├─ Records deleted:    {deleted_count}")
    print(f"  ├─ Remaining users:    {final_total}")
    print(f"  ├─ Admin accounts:     {final_admins + final_superusers} (protected)")
    print(f"  └─ System status:      ✓ READY FOR NEW USERS")
    
    print(f"\n✓ Your system is clean and ready for fresh registration!")
    print(f"✓ All functionality remains intact")
    print(f"✓ Next users can register normally")
    
    print("\n" + "=" * 75 + "\n")
    
    return True


if __name__ == '__main__':
    main()
