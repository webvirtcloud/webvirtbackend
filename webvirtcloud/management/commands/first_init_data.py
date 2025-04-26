import json

from django.core.management.base import BaseCommand

from account.models import User
from image.models import Image
from region.models import Feature, Region
from size.models import Size


class Command(BaseCommand):
    help = "Initialize data for webvirtcloud"

    def handle(self, *args, **kwargs):
        size_json = "size/fixtures/size.json"
        image_json = "image/fixtures/image.json"
        region_json = "region/fixtures/region.json"
        feature_json = "region/fixtures/feature.json"

        # Load regions
        try:
            with open(region_json, "r") as region_file:
                data = json.load(region_file)
                for item in data:
                    Region.objects.update_or_create(
                        pk=item.get("pk"),
                        defaults=item.get("fields"),
                    )
                self.stdout.write(self.style.SUCCESS("Regions successfully loaded"))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {region_json}"))
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Error decoding JSON: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        # Load features
        try:
            with open(feature_json, "r") as feature_file:
                data = json.load(feature_file)
                for item in data:
                    Feature.objects.update_or_create(
                        pk=item.get("pk"),
                        defaults=item.get("fields"),
                    )
                self.stdout.write(self.style.SUCCESS("Features successfully loaded"))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {feature_json}"))
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Error decoding JSON: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        # Load sizes
        try:
            with open(size_json, "r") as size_file:
                data = json.load(size_file)
                for item in data:
                    Size.objects.update_or_create(
                        pk=item.get("pk"),
                        defaults=item.get("fields"),
                    )
                self.stdout.write(self.style.SUCCESS("Sizes successfully loaded"))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {size_json}"))
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Error decoding JSON: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        # Load images
        try:
            with open(image_json, "r") as image_file:
                data = json.load(image_file)
                for item in data:
                    regions = item.get("fields").get("regions")
                    item.get("fields").pop("regions")
                    image, created = Image.objects.update_or_create(
                        pk=item.get("pk"),
                        defaults=item.get("fields"),
                    )
                    image.regions.set(regions)
                self.stdout.write(self.style.SUCCESS("Images successfully loaded"))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {image_json}"))
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Error decoding JSON: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        # Create admin superuser
        try:
            User.objects.get(email="admin@localdomain")
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                email="admin@localdomain",
                password="admin",
            )
            user.first_name = "Charlie"
            user.last_name = "Root"
            user.is_active = True
            user.is_verified = True
            user.is_email_verified = True
            user.save()
            user.update_hash()
        self.stdout.write(self.style.SUCCESS("User 'admin@localdomain' with password 'admin' successfully created"))
