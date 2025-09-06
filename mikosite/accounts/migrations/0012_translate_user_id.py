import uuid
from django.db import migrations, models


def convert_user_ids_to_uuid(apps, schema_editor):
    """Assign random UUID4 identifiers to existing users and update all
    foreign key references in the database to keep relations intact."""

    connection = schema_editor.connection
    if connection.vendor == "sqlite":
        return

    # Defer constraint checks so we can update PKs and FKs in any order
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL DEFERRED")

        # Build a mapping of old integer IDs to new UUID4 values
        cursor.execute("SELECT id FROM accounts_user")
        id_map = {row[0]: str(uuid.uuid4()) for row in cursor.fetchall()}

        introspection = connection.introspection
        tables = introspection.table_names(cursor)

        # Collect all foreign key columns that point at accounts_user.id
        fk_columns = []
        for table in tables:
            constraints = introspection.get_constraints(cursor, table)
            for details in constraints.values():
                if details.get("foreign_key") == ("accounts_user", "id"):
                    fk_columns.append((table, details["columns"][0]))

        # Update users and related rows with the newly generated UUIDs
        for old_id, new_id in id_map.items():
            cursor.execute(
                "UPDATE accounts_user SET id=%s WHERE id=%s", [new_id, old_id]
            )
            for table, column in fk_columns:
                cursor.execute(
                    f"UPDATE \"{table}\" SET {column}=%s WHERE {column}=%s",
                    [new_id, old_id],
                )


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0011_user_id_to_string",
        ),
    ]

    operations = [
        migrations.RunPython(convert_user_ids_to_uuid, migrations.RunPython.noop),
    ]
