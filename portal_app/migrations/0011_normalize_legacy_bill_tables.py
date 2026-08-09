from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {col.name for col in description}


def _normalize_bill_table(apps, schema_editor, table_name, number_target):
    connection = schema_editor.connection

    # Fresh/test databases may not contain legacy bill tables yet.
    if table_name not in connection.introspection.table_names():
        return

    cols = _column_names(connection, table_name)

    # Rename legacy columns when present.
    if 'citizen_id' in cols and 'user_id' not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` CHANGE COLUMN `citizen_id` `user_id` bigint NOT NULL"
        )

    if 'bill_number' in cols and number_target not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` CHANGE COLUMN `bill_number` `{number_target}` varchar(30) NOT NULL"
        )

    if 'bill_amount' in cols and 'amount' not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` CHANGE COLUMN `bill_amount` `amount` decimal(10,2) NOT NULL"
        )

    if 'payment_date' in cols and 'paid_at' not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` CHANGE COLUMN `payment_date` `paid_at` datetime(6) NULL"
        )

    # Refresh columns after renames.
    cols = _column_names(connection, table_name)

    # Add missing columns expected by current models.
    if 'bill_month' not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` ADD COLUMN `bill_month` varchar(7) NULL"
        )

    if 'bill_month' in _column_names(connection, table_name):
        schema_editor.execute(
            f"UPDATE `{table_name}` SET `bill_month` = DATE_FORMAT(`due_date`, '%%Y-%%m') WHERE `bill_month` IS NULL"
        )
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` MODIFY COLUMN `bill_month` varchar(7) NOT NULL"
        )

    if 'generated_at' not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` ADD COLUMN `generated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)"
        )

    if 'transaction_id' not in cols:
        schema_editor.execute(
            f"ALTER TABLE `{table_name}` ADD COLUMN `transaction_id` varchar(120) NOT NULL DEFAULT ''"
        )


def forward(apps, schema_editor):
    _normalize_bill_table(apps, schema_editor, 'portal_app_electricitybill', 'consumer_number')
    _normalize_bill_table(apps, schema_editor, 'portal_app_waterbill', 'connection_number')


def noop_reverse(apps, schema_editor):
    # This migration normalizes legacy databases and is intentionally non-reversible.
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('portal_app', '0010_application_approval_email_sent_at_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, noop_reverse),
    ]
