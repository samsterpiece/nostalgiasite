# Generated by Django 4.2.7 on 2024-09-01 01:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nostalgia_app", "0006_alter_informationitem_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="informationitem",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2024, 8, 31, 21, 43, 53, 963637)
            ),
        ),
        migrations.CreateModel(
            name="APIFact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("year", models.IntegerField()),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("source_url", models.URLField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("categories", models.ManyToManyField(to="nostalgia_app.category")),
            ],
            options={
                "unique_together": {("year", "title")},
            },
        ),
    ]
