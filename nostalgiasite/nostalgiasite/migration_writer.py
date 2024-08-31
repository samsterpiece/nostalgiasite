from django.db.migrations.writer import MigrationWriter

class CustomMigrationWriter(MigrationWriter):
    def write(self, migrations, filename=None):
        # Generate a more descriptive filename
        if filename is None:
            filename = self.migration_name(migrations)

        # Write the migration file
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(self.render(migrations))

    def migration_name(self, migrations):
        # Generate a descriptive name based on the migrations
        # For example, you can use the first migration operation's description
        if migrations:
            operation = migrations[0]['operations'][0]
            description = operation.describe()
            return f"{description}.py"
        else:
            return "initial.py"