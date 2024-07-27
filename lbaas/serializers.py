from rest_framework import serializers

from region.serializers import RegionSerializer
from size.models import Size
from image.models import Image
from region.models import Region
from virtance.models import Virtance
from virtance.utils import make_ssh_private, encrypt_data
from .tasks import create_lbaas, reload_lbaas
from .models import LBaaS, LBaaSForwadRule, LBaaSVirtance


class HeathCheckSerializer(serializers.Serializer):
    path = serializers.CharField(required=False, source="check_path")
    port = serializers.IntegerField(source="check_port")
    protocol = serializers.CharField(source="check_protocol")
    healthy_threshold = serializers.IntegerField(source="check_healthy_threshold")
    unhealthy_threshold = serializers.IntegerField(source="check_unhealthy_threshold")
    check_interval_seconds = serializers.IntegerField(source="check_interval_seconds")
    response_timeout_seconds = serializers.IntegerField(source="check_timeout_seconds")


class ForwardingRuleSerializer(serializers.Serializer):
    entry_port = serializers.IntegerField()
    entry_protocol = serializers.CharField(max_length=4)
    target_port = serializers.IntegerField()
    target_protocol = serializers.CharField(max_length=4)


class ListOfForwardingRuleSerializer(serializers.ListSerializer):
    child = ForwardingRuleSerializer()


class StickySessionsSerializer(serializers.Serializer):
    cookie_name = serializers.CharField()
    cookie_ttl_seconds = serializers.IntegerField()


class LBaaSSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False, read_only=True, source="uuid")
    ip = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField()
    region = serializers.CharField(write_only=True)
    created_at = serializers.DateTimeField(read_only=True, source="created")
    virtance_ids = serializers.ListField(required=False, write_only=True)
    health_check = serializers.DictField(required=False)
    sticky_sessions = serializers.DictField(required=False, write_only=True)
    forwarding_rules = ListOfForwardingRuleSerializer(write_only=True)
    redirect_http_to_https = serializers.BooleanField(required=False)

    class Meta:
        model = LBaaS
        fields = (
            "id",
            "ip",
            "name",
            "event",
            "region",
            "created_at",
            "virtance_ids",
            "health_check",
            "sticky_sessions",
            "forwarding_rules",
            "redirect_http_to_https",
        )

    def get_ip(self, obj):
        return None

    def validate(self, attrs):
        user = self.context.get("user")
        region = attrs.get("region")
        virtance_ids = list(set(attrs.get("virtance_ids", [])))
        health_check = attrs.get("health_check")
        sticky_sessions = attrs.get("sticky_sessions")
        forwarding_rules = attrs.get("forwarding_rules")

        # Check if region is active
        try:
            check_region = Region.objects.get(slug=region, is_deleted=False)
            if check_region.is_active is False:
                raise serializers.ValidationError({"region": ["Region is not active."]})
        except Region.DoesNotExist:
            raise serializers.ValidationError({"region": ["Region not found."]})

        # Check forwarding_rules
        if not forwarding_rules:
            raise serializers.ValidationError({"forwarding_rules": ["Forwarding rules is required."]})
        if not all(isinstance(x, dict) for x in forwarding_rules):
            raise serializers.ValidationError({"forwarding_rules": ["Invalid forwarding rules."]})

        if len([tuple(sorted(d.items())) for d in forwarding_rules]) != len(
            set([tuple(sorted(d.items())) for d in forwarding_rules])
        ):
            raise serializers.ValidationError({"forwarding_rules": ["Duplicate forwarding rules."]})

        # Check duplicate forwarding rules on entry data
        entry_data = [f'{rule.get("entry_protcol")}_{rule.get("entry_port")}' for rule in forwarding_rules]
        if len(entry_data) != len(set(entry_data)):
            raise serializers.ValidationError({"forwarding_rules": ["Duplicate entry_protcol and entry_port."]})

        for rule in forwarding_rules:
            if (
                not rule.get("entry_port")
                or not rule.get("entry_protocol")
                or not rule.get("target_port")
                or not rule.get("target_protocol")
            ):
                raise serializers.ValidationError({"forwarding_rules": ["Invalid forwarding rules."]})

            if rule.get("entry_protocol") not in [x[0] for x in LBaaSForwadRule.PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid entry_protocol."]})

            if not 0 < rule.get("entry_port") < 65536:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid entry_port."]})

            if not 0 < rule.get("target_port") < 65536:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid target_port."]})

            if rule.get("target_protocol") not in [x[0] for x in LBaaSForwadRule.PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid target_protocol."]})

            if rule.get("entry_protocol") != rule.get("target_protocol"):
                raise serializers.ValidationError(
                    {
                        "forwarding_rules": [
                            ("Entry and target protocol must be the same. "
                             "Support for different procotols is temporarily unsupported.")
                        ]
                    }
                )

        # Check if virtance_ids are valid
        if virtance_ids:
            if not all(isinstance(x, int) for x in virtance_ids):
                raise serializers.ValidationError({"virtance_ids": ["Invalid virtance_ids."]})

            exist_virtances = Virtance.objects.filter(
                user=user, id__in=virtance_ids, region=check_region, is_deleted=False
            )
            if len(exist_virtances) != len(virtance_ids):
                raise serializers.ValidationError({"virtance_ids": ["Virtance not found in the region."]})

        # Check if health_check is valid
        if health_check:
            if health_check.get("protocol") not in [x[0] for x in LBaaS.CHECK_PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"health_check": ["Invalid protocol."]})

            if health_check.get("protocol") == LBaaS.HTTP or health_check.get("protocol") == LBaaS.HTTPS:
                if health_check.get("path") == "" or not health_check.get("path"):
                    raise serializers.ValidationError({"health_check": ["Path is required for HTTP protocol."]})

            if 1 > health_check.get("port") < 65535:
                raise serializers.ValidationError({"health_check": ["Invalid port."]})

            if 1 > health_check.get("check_interval_seconds") < 9999:
                raise serializers.ValidationError({"health_check": ["Invalid check_interval_seconds."]})

            if 1 > health_check.get("response_timeout_seconds") < 9999:
                raise serializers.ValidationError({"health_check": ["Invalid response_timeout_seconds."]})

            if 1 > health_check.get("healthy_threshold") < 999:
                raise serializers.ValidationError({"health_check": ["Invalid healthy_threshold."]})

            if 1 > health_check.get("unhealthy_threshold") < 999:
                raise serializers.ValidationError({"health_check": ["Invalid unhealthy_threshold."]})

        # Check if sticky_sessions is valid
        if sticky_sessions:
            if not sticky_sessions.get("cookie_name") or sticky_sessions.get("cookie_name") == "":
                raise serializers.ValidationError({"sticky_sessions": ["Cookie name is required."]})

            if not sticky_sessions.get("cookie_ttl_seconds") or 1 > sticky_sessions.get("cookie_ttl_seconds") < 9999:
                raise serializers.ValidationError({"sticky_sessions": ["Invalid cookie_ttl."]})

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["region"] = RegionSerializer(Region.objects.get(id=instance.virtance.region.id, is_deleted=False)).data
        data["health_check"] = HeathCheckSerializer(instance).data
        data["virtance_ids"] = [lv.virtance.id for lv in LBaaSVirtance.objects.filter(lbaas=instance, is_deleted=False)]
        data["sticky_sessions"] = StickySessionsSerializer(instance) if instance.sticky_sessions else None
        data["forwarding_rules"] = ForwardingRuleSerializer(
            LBaaSForwadRule.objects.filter(lbaas=instance, is_deleted=False), many=True
        ).data

        return data

    def create(self, validated_data):
        user = self.context.get("user")
        name = validated_data.get("name")
        region_slug = validated_data.get("region")
        virtance_ids = list(set(validated_data.get("virtance_ids", [])))
        health_check = validated_data.get("health_check")
        sticky_sessions = validated_data.get("sticky_sessions")
        forwarding_rules = validated_data.get("forwarding_rules", [])
        redirect_http_to_https = validated_data.get("redirect_http_to_https", False)
        enc_private_key = encrypt_data(make_ssh_private())

        size = Size.objects.filter(type=Size.LBAAS, is_deleted=False).first()
        region = Region.objects.get(slug=region_slug, is_deleted=False)
        template = Image.objects.filter(type=Image.LBAAS, is_deleted=False).first()

        stick_session_enabled = True if sticky_sessions else False
        stick_session_cookie_name = "sessionid"
        stick_session_cookie_ttl = 3600
        if sticky_sessions:
            stick_session_cookie_name = sticky_sessions.get("cookie_name")
            stick_session_cookie_ttl = sticky_sessions.get("cookie_ttl_seconds")

        check_protocol = LBaaS.TCP
        check_path = "/"
        check_port = 80
        check_check_interval_seconds = 10
        check_response_timeout_seconds = 5
        check_healthy_threshold = 3
        check_unhealthy_threshold = 5
        if health_check:
            check_protocol = health_check.get("protocol")
            check_path = health_check.get("path", check_path)
            check_port = health_check.get("port")
            check_check_interval_seconds = health_check.get("check_interval_seconds")
            check_response_timeout_seconds = health_check.get("response_timeout_seconds")
            check_healthy_threshold = health_check.get("healthy_threshold")
            check_unhealthy_threshold = health_check.get("unhealthy_threshold")

        if not template and not size:
            raise serializers.ValidationError(
                {"error": ["Template or size not found. Plese contact support for more information."]}
            )

        virtance = Virtance.objects.create(
            name=name,
            user=user,
            size=size,
            type=Virtance.LBAAS,
            region=region,
            disk=size.disk,
            template=template,
        )

        lbaas = LBaaS.objects.create(
            name=name,
            user=user,
            private_key=enc_private_key,
            virtance=virtance,
            check_protocol=check_protocol,
            check_port=check_port,
            check_path=check_path,
            check_interval_seconds=check_check_interval_seconds,
            check_timeout_seconds=check_response_timeout_seconds,
            check_unhealthy_threshold=check_unhealthy_threshold,
            check_healthy_threshold=check_healthy_threshold,
            sticky_sessions=stick_session_enabled,
            sticky_sessions_cookie_name=stick_session_cookie_name,
            sticky_sessions_cookie_ttl=stick_session_cookie_ttl,
            redirect_http_to_https=redirect_http_to_https,
        )

        if forwarding_rules:
            for rule in forwarding_rules:
                LBaaSForwadRule.objects.create(
                    lbaas=lbaas,
                    entry_port=rule.get("entry_port"),
                    entry_protocol=rule.get("entry_protocol"),
                    target_port=rule.get("target_port"),
                    target_protocol=rule.get("target_protocol"),
                )

        if virtance_ids:
            for v_id in virtance_ids:
                virtance = Virtance.objects.get(user=user, id=v_id, region=region, is_deleted=False)
                LBaaSVirtance.objects.create(lbaas=lbaas, virtance=virtance)

        create_lbaas.delay(lbaas.id)

        return lbaas

    def update(self, instance, validated_data):
        return instance


class LBaaSAddVirtanceSerializer(serializers.ModelSerializer):
    virtance_ids = serializers.ListField(required=False)

    def validate(self, attrs):
        virtance_ids = list(set(attrs.get("virtance_ids", [])))

        for v_id in virtance_ids:
            if not isinstance(v_id, int):
                raise serializers.ValidationError({"virtance_ids": ["This field must be a list of integers."]})

        list_ids = Virtance.objects.filter(user=self.instance.user, id__in=virtance_ids, is_deleted=False).values_list(
            "id", flat=True
        )
        for v_id in virtance_ids:
            if v_id not in list_ids:
                raise serializers.ValidationError(f"Virtance with ID {v_id} not found.")

        for v_id in virtance_ids:
            if LBaaSVirtance.objects.filter(lbaas=self.instance, virtance_id=v_id, is_deleted=False).exists():
                raise serializers.ValidationError(f"Virtance with ID {v_id} has already added to load balancer.")

        return attrs

    def update(self, instance, validated_data):
        virtance_ids = list(set(validated_data.get("virtance_ids")))

        for v_id in virtance_ids:
            LBaaSVirtance.objects.create(lbaas=instance, virtance_id=v_id)

        instance.event = LBaaS.ADD_VIRTANCE
        instance.save()

        reload_lbaas.delay(instance.id)

        return validated_data


class LBaaSDelVirtanceSerializer(serializers.ModelSerializer):
    virtance_ids = serializers.ListField(required=False)

    def validate(self, attrs):
        virtance_ids = list(set(attrs.get("virtance_ids", [])))

        for v_id in virtance_ids:
            if not isinstance(v_id, int):
                raise serializers.ValidationError({"virtance_ids": ["This field must be a list of integers."]})

        list_ids = Virtance.objects.filter(user=self.instance.user, id__in=virtance_ids, is_deleted=False).values_list(
            "id", flat=True
        )
        for v_id in virtance_ids:
            if v_id not in list_ids:
                raise serializers.ValidationError(f"Virtance with ID {v_id} not found.")

        for v_id in virtance_ids:
            if not LBaaSVirtance.objects.filter(lbaas=self.instance, virtance_id=v_id, is_deleted=False).exists():
                raise serializers.ValidationError(f"Virtance with ID {v_id} has not added to load balancer.")

        return attrs

    def update(self, instance, validated_data):
        virtance_ids = list(set(validated_data.get("virtance_ids")))

        LBaaSVirtance.objects.filter(lbaas=instance, virtance_id__in=virtance_ids, is_deleted=False).update(
            is_deleted=True
        )

        instance.event = LBaaS.REMOVE_VIRTANCE
        instance.save()

        reload_lbaas.delay(instance.id)

        return validated_data


class LBaaSAddRuleSerializer(serializers.ModelSerializer):
    forwarding_rules = ListOfForwardingRuleSerializer()

    def validate(self, attrs):
        forwarding_rules = attrs.get("forwarding_rules")

        if not all(isinstance(x, dict) for x in forwarding_rules):
            raise serializers.ValidationError({"forwarding_rules": ["Invalid forwarding rules."]})
        for rule in forwarding_rules:
            if (
                not rule.get("entry_port")
                or not rule.get("entry_protocol")
                or not rule.get("target_port")
                or not rule.get("target_protocol")
            ):
                raise serializers.ValidationError({"forwarding_rules": ["Invalid forwarding rules."]})

            if rule.get("entry_protocol") not in [x[0] for x in LBaaSForwadRule.PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid entry_protocol."]})

            if rule.get("target_protocol") not in [x[0] for x in LBaaSForwadRule.PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid target_protocol."]})

            if 1 > rule.get("entry_port") < 65535:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid entry_port."]})

            if 1 > rule.get("target_port") < 65535:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid target_port."]})

        for rule in forwarding_rules:
            if LBaaSForwadRule.objects.filter(
                lbaas=self.instance,
                entry_port=rule.get("entry_port"),
                entry_protocol=rule.get("entry_protocol"),
                target_port=rule.get("target_port"),
                target_protocol=rule.get("target_protocol"),
                is_deleted=False,
            ).exists():
                raise serializers.ValidationError({"forwarding_rules": ["Rule already exists."]})

        return attrs

    def update(self, instance, validated_data):
        forwarding_rules = validated_data.get("forwarding_rules")

        for rule in forwarding_rules:
            LBaaSForwadRule.objects.create(
                lbaas=instance,
                entry_port=rule.get("entry_port"),
                entry_protocol=rule.get("entry_protocol"),
                target_port=rule.get("target_port"),
                target_protocol=rule.get("target_protocol"),
            )

        instance.event = LBaaS.ADD_RULE
        instance.save()

        reload_lbaas.delay(instance.id)

        return validated_data


class LBaaSDelRuleSerializer(serializers.ModelSerializer):
    forwarding_rules = ListOfForwardingRuleSerializer()

    def validate(self, attrs):
        forwarding_rules = attrs.get("forwarding_rules")

        if not all(isinstance(x, dict) for x in forwarding_rules):
            raise serializers.ValidationError({"forwarding_rules": ["Invalid forwarding rules."]})
        for rule in forwarding_rules:
            if (
                not rule.get("entry_port")
                or not rule.get("entry_protocol")
                or not rule.get("target_port")
                or not rule.get("target_protocol")
            ):
                raise serializers.ValidationError({"forwarding_rules": ["Invalid forwarding rules."]})

            if rule.get("entry_protocol") not in [x[0] for x in LBaaSForwadRule.PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid entry_protocol."]})

            if rule.get("target_protocol") not in [x[0] for x in LBaaSForwadRule.PROTOCOL_CHOICES]:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid target_protocol."]})

            if 1 > rule.get("entry_port") < 65535:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid entry_port."]})

            if 1 > rule.get("target_port") < 65535:
                raise serializers.ValidationError({"forwarding_rules": ["Invalid target_port."]})

        for rule in forwarding_rules:
            if not LBaaSForwadRule.objects.filter(
                lbaas=self.instance,
                entry_port=rule.get("entry_port"),
                entry_protocol=rule.get("entry_protocol"),
                target_port=rule.get("target_port"),
                target_protocol=rule.get("target_protocol"),
                is_deleted=False,
            ).exists():
                raise serializers.ValidationError({"forwarding_rules": ["Rule not found."]})

        return attrs

    def update(self, instance, validated_data):
        forwarding_rules = validated_data.get("forwarding_rules")

        for rule in forwarding_rules:
            LBaaSForwadRule.objects.filter(
                lbaas=instance,
                entry_port=rule.get("entry_port"),
                entry_protocol=rule.get("entry_protocol"),
                target_port=rule.get("target_port"),
                target_protocol=rule.get("target_protocol"),
                is_deleted=False,
            ).update(is_deleted=True)

        instance.event = LBaaS.REMOVE_RULE
        instance.save()

        reload_lbaas.delay(instance.id)

        return validated_data
