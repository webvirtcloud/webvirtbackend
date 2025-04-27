import json
import os

import yaml
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

# Applications to skip completely
SKIP_FIXTURE_APPS = ["account"]

# Models for strict update with field comparison
STRICT_UPDATE_MODELS = [
    "size.size",
    "size.dbms",
    "image.image",
    "region.feature",
]


class Command(BaseCommand):
    help = "Sync fixtures with selective update for certain models and skip certain apps"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate fixture sync without applying any changes",
        )

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get("dry_run", False)

        self.stdout.write("Searching for fixture files in installed apps...")

        total_objects = 0
        updated_objects = 0
        created_objects = 0
        skipped_objects = 0
        total_fixtures = 0
        skipped_fixtures = 0

        for app_config in apps.get_app_configs():
            if app_config.label in SKIP_FIXTURE_APPS:
                continue

            fixtures_dir = os.path.join(app_config.path, "fixtures")
            if not os.path.exists(fixtures_dir):
                continue

            fixtures = [
                f for f in os.listdir(fixtures_dir) if f.endswith(".json") or f.endswith(".yaml") or f.endswith(".yml")
            ]

            if not fixtures:
                continue

            self.stdout.write(f"Found {len(fixtures)} fixture(s) in {app_config.name}")

            for fixture in fixtures:
                fixture_path = os.path.join(fixtures_dir, fixture)

                created, updated, skipped = self.smart_update_fixture(fixture_path, dry_run=dry_run)
                created_objects += created
                updated_objects += updated
                skipped_objects += skipped
                total_objects += created + updated + skipped
                total_fixtures += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {total_fixtures} fixture(s): {created_objects} created, {updated_objects} updated, "
                f"{skipped_objects} skipped, {skipped_fixtures} fixture(s) ignored."
            )
        )

    def smart_update_fixture(self, fixture_path, dry_run=False):
        """
        Smart fixture update: creates new objects, updates only changed fields for selected models.
        """
        created = 0
        updated = 0
        skipped = 0

        if fixture_path.endswith(".json"):
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif fixture_path.endswith((".yaml", ".yml")):
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            self.stdout.write(self.style.ERROR(f"Unsupported fixture format: {fixture_path}"))
            return (0, 0, 0)

        if not data:
            return (0, 0, 0)

        for entry in data:
            model_label = entry["model"]
            pk = entry["pk"]
            fields = entry.get("fields", {})

            strict_update = model_label in STRICT_UPDATE_MODELS

            try:
                model_class = apps.get_model(model_label)
            except LookupError:
                self.stdout.write(self.style.ERROR(f"Unknown model: {model_label}"))
                continue

            with transaction.atomic():
                obj, created_flag = model_class.objects.get_or_create(pk=pk, defaults=fields)
                if created_flag:
                    created += 1
                    if dry_run:
                        self.stdout.write(self.style.WARNING(f"[DRY-RUN] Would create {model_label} id={pk}"))
                        obj.delete()
                    else:
                        self.stdout.write(self.style.SUCCESS(f"  Created {model_label} id={pk}"))
                    continue

                if strict_update:
                    # Object exists — compare and update only changed fields
                    changed = False
                    model_fields = {f.name: f for f in model_class._meta.get_fields()}
                    m2m_updates = []

                    for field_name, fixture_value in fields.items():
                        if not hasattr(obj, field_name):
                            continue

                        field = model_fields.get(field_name)
                        if field is None:
                            continue

                        if field.name not in ["regions", "created", "updated", "deleted", "is_active", "is_deleted"]:
                            if field.many_to_many:
                                related_manager = getattr(obj, field_name)
                                existing_ids = set(related_manager.all().values_list("id", flat=True))
                                desired_ids = set(fixture_value)

                                if existing_ids != desired_ids:
                                    m2m_updates.append((related_manager, desired_ids))
                                    changed = True
                            else:
                                obj_value = getattr(obj, field_name)

                                if isinstance(obj_value, bool):
                                    fixture_value = bool(fixture_value)
                                elif isinstance(obj_value, (int, float)) and isinstance(fixture_value, str):
                                    try:
                                        fixture_value = type(obj_value)(fixture_value)
                                    except ValueError:
                                        pass

                                if str(obj_value) != str(fixture_value):
                                    if dry_run:
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f"[DRY-RUN] {model_label} id={pk} field '{field_name}' would change: '{obj_value}' -> '{fixture_value}'"
                                            )
                                        )
                                    else:
                                        setattr(obj, field_name, fixture_value)
                                    changed = True

                    if changed:
                        save_fields = [
                            field_name
                            for field_name in fields.keys()
                            if field_name in model_fields and not model_fields[field_name].many_to_many
                        ]
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[DRY-RUN] Would update {model_label} id={pk}: fields {save_fields}"
                                )
                            )
                        else:
                            obj.save(update_fields=save_fields)
                            updated += 1
                            self.stdout.write(self.style.SUCCESS(f"  Updated {model_label} id={pk}"))

                        for related_manager, ids in m2m_updates:
                            if dry_run:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"[DRY-RUN] Would update ManyToMany {related_manager.model.__name__} with ids {ids}"
                                    )
                                )
                            else:
                                related_manager.set(ids)
                    else:
                        skipped += 1
                else:
                    # Model is not in STRICT_UPDATE_MODELS — only ensure object exists, do not update fields
                    skipped += 1

        return (created, updated, skipped)
