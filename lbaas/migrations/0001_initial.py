# Generated by Django 4.2.3 on 2024-05-23 16:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("virtance", "0002_virtance_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="LBaaS",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=100)),
                (
                    "event",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("create", "Create"),
                            ("reload", "Reload"),
                            ("delete", "Delete"),
                            ("add_virtance", "Add Virtance to a Load Balancer"),
                            ("remove_virtance", "Remove Virtance from a Load Balancer"),
                            ("add_forward_rule", "Add Forwarding Rules to a Load Balancer"),
                            ("update_forward_rule", "Update Forwarding Rules to a Load Balancer"),
                            ("remove_forward_rule", "Remove Forwarding Rules to a Load Balancer"),
                        ],
                        default="create",
                        max_length=40,
                        null=True,
                    ),
                ),
                ("private_key", models.TextField()),
                (
                    "check_protocol",
                    models.CharField(
                        choices=[("tcp", "TCP"), ("http", "HTTP"), ("https", "HTTPS")], default="tcp", max_length=10
                    ),
                ),
                ("check_port", models.IntegerField(default=80)),
                ("check_path", models.CharField(default="/", max_length=100)),
                ("check_interval_seconds", models.IntegerField(default=10)),
                ("check_timeout_seconds", models.IntegerField(default=5)),
                ("check_unhealthy_threshold", models.IntegerField(default=5)),
                ("check_healthy_threshold", models.IntegerField(default=3)),
                ("sticky_sessions", models.BooleanField(default=False)),
                ("sticky_sessions_cookie_name", models.CharField(default="sessionid", max_length=100)),
                ("sticky_sessions_cookie_ttl", models.IntegerField(default=3600)),
                ("redirect_http_to_https", models.BooleanField(default=False)),
                ("is_deleted", models.BooleanField(default=False, verbose_name="Deleted")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                (
                    "virtance", models.ForeignKey(
                        blank=True, 
                        on_delete=django.db.models.deletion.PROTECT, 
                        to="virtance.virtance", 
                        null=True,
                    )
                ),
            ],
            options={
                "verbose_name": "Load Balancer",
                "verbose_name_plural": "Load Balancers",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="LBaaSVirtance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="Deleted")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                ("lbaas", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="lbaas.lbaas")),
                ("virtance", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="virtance.virtance")),
            ],
            options={
                "verbose_name": "Load Balancer Virtance",
                "verbose_name_plural": "Load Balancer Virtances",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="LBaaSForwadRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entry_port", models.IntegerField()),
                (
                    "entry_protocol",
                    models.CharField(
                        choices=[
                            ("udp", "UDP"),
                            ("tcp", "TCP"),
                            ("http", "HTTP"),
                            ("https", "HTTPS"),
                            ("http2", "HTTP2"),
                            ("http3", "HTTP3"),
                        ],
                        default="http",
                        max_length=10,
                    ),
                ),
                ("target_port", models.IntegerField()),
                (
                    "target_protocol",
                    models.CharField(
                        choices=[
                            ("udp", "UDP"),
                            ("tcp", "TCP"),
                            ("http", "HTTP"),
                            ("https", "HTTPS"),
                            ("http2", "HTTP2"),
                            ("http3", "HTTP3"),
                        ],
                        default="http",
                        max_length=10,
                    ),
                ),
                ("is_deleted", models.BooleanField(default=False, verbose_name="Deleted")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                ("lbaas", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="lbaas.lbaas")),
            ],
            options={
                "verbose_name": "Load Balancer Forward Rule",
                "verbose_name_plural": "Load Balancer Forward Rules",
                "ordering": ["-id"],
            },
        ),
    ]
