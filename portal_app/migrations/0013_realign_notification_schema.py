from django.db import migrations


def forwards(apps, schema_editor):
  with schema_editor.connection.cursor() as cursor:
    cursor.execute("SHOW TABLES LIKE 'portal_app_notification'")
    if not cursor.fetchone():
      return

    cursor.execute("SHOW COLUMNS FROM portal_app_notification")
    existing_columns = {row[0] for row in cursor.fetchall()}

    cursor.execute(
      """
      SELECT CONSTRAINT_NAME
      FROM information_schema.KEY_COLUMN_USAGE
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'portal_app_notification'
        AND COLUMN_NAME = 'user_id'
        AND REFERENCED_TABLE_NAME = 'portal_app_customuser'
      """
    )
    for (constraint_name,) in cursor.fetchall():
      cursor.execute(
        f"ALTER TABLE `portal_app_notification` DROP FOREIGN KEY `{constraint_name}`"
      )

    if 'user_id' in existing_columns and 'recipient_id' not in existing_columns:
      cursor.execute(
        "ALTER TABLE `portal_app_notification` CHANGE COLUMN `user_id` `recipient_id` bigint NOT NULL"
      )

    if 'notification_type' in existing_columns and 'category' not in existing_columns:
      cursor.execute(
        "ALTER TABLE `portal_app_notification` CHANGE COLUMN `notification_type` `category` varchar(20) NOT NULL DEFAULT 'system'"
      )

    if 'action_url' in existing_columns and 'target_url' not in existing_columns:
      cursor.execute(
        "ALTER TABLE `portal_app_notification` CHANGE COLUMN `action_url` `target_url` varchar(255) NOT NULL DEFAULT ''"
      )

    if 'title' in existing_columns:
      cursor.execute(
        "ALTER TABLE `portal_app_notification` MODIFY COLUMN `title` varchar(120) NOT NULL"
      )

    for column_name in ['status', 'priority', 'is_active', 'content_type', 'object_id', 'expires_at']:
      if column_name in existing_columns:
        cursor.execute(
          f"ALTER TABLE `portal_app_notification` DROP COLUMN `{column_name}`"
        )

    cursor.execute(
      """
      SELECT COUNT(*)
      FROM information_schema.TABLE_CONSTRAINTS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'portal_app_notification'
        AND CONSTRAINT_NAME = 'portal_app_notificat_recipien_fk_portal_ap'
      """
    )
    if not cursor.fetchone()[0] and 'recipient_id' in existing_columns:
      cursor.execute(
        """
        ALTER TABLE `portal_app_notification`
        ADD CONSTRAINT `portal_app_notificat_recipien_fk_portal_ap`
        FOREIGN KEY (`recipient_id`) REFERENCES `portal_app_customuser` (`id`)
        """
      )

    cursor.execute(
      """
      SELECT COUNT(*)
      FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'portal_app_notification'
        AND INDEX_NAME = 'portal_app__recipie_db088d_idx'
      """
    )
    if not cursor.fetchone()[0] and 'recipient_id' in existing_columns and 'is_read' in existing_columns:
      cursor.execute(
        """
        CREATE INDEX `portal_app__recipie_db088d_idx`
          ON `portal_app_notification` (`recipient_id`, `is_read`)
        """
      )


class Migration(migrations.Migration):

    dependencies = [
        ('portal_app', '0012_useractivity_notification'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
