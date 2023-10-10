import re
import ipaddress
from rest_framework import serializers

from virtance.models import Virtance
from .models import Firewall, Rule, Cidr, FirewallVirtance
from .tasks import firewall_attach, firewall_detach, firewall_update


class CidrField(serializers.Field):
    def to_internal_value(self, data):
        if "/" in data:
            try:
                ipaddress.ip_network(data)
            except ValueError:
                raise serializers.ValidationError("Invalid CIDR format.")
        else:
            try:
                ipaddress.ip_address(data)
            except ValueError:
                raise serializers.ValidationError("Invalid IP address format.")

        return data

    def to_representation(self, value):
        return value


class PortsField(serializers.Field):
    def to_internal_value(self, data):
        pattern = re.compile(r"^(\d+)(?:-(\d+))?$")
        match = pattern.match(str(data))

        if match:
            start_port = int(match.group(1))
            end_port = int(match.group(2)) if match and match.group(2) else None
            if not end_port and (start_port < -1 or start_port > 65535):
                raise serializers.ValidationError("Invalid port number. Use number from 0 to 65535.")
            if (start_port < 1 or start_port > 65535) and end_port and (end_port < 1 or end_port > 65535):
                raise serializers.ValidationError("Invalid ports range. Use 1-65535.")
            return data

        raise serializers.ValidationError("Invalid port format. Use 'port' or 'start_port-end_port'.")

    def to_representation(self, value):
        return value


class SourceSerializer(serializers.Serializer):
    addresses = serializers.ListField(child=CidrField())


class DestinationSerializer(serializers.Serializer):
    addresses = serializers.ListField(child=CidrField())


class InboundRuleSerializer(serializers.Serializer):
    protocol = serializers.CharField(max_length=4)
    ports = PortsField()
    sources = SourceSerializer()


class ListOfInboundRulesSerializer(serializers.ListSerializer):
    child = InboundRuleSerializer()


class OutboundRuleSerializer(serializers.Serializer):
    protocol = serializers.CharField(max_length=4)
    ports = PortsField()
    destinations = DestinationSerializer()


class ListOfOutboundRulesSerializer(serializers.ListSerializer):
    child = OutboundRuleSerializer()


class FirewallSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)
    event = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(source="created", read_only=True)
    virtance_ids = serializers.ListField(required=False)
    inbound_rules = ListOfInboundRulesSerializer(required=False)
    outbound_rules = ListOfOutboundRulesSerializer(required=False)

    class Meta:
        model = Firewall
        fields = (
            "uuid",
            "name",
            "event",
            "created_at",
            "virtance_ids",
            "inbound_rules",
            "outbound_rules",
        )

    def get_event(self, obj):
        if obj.event is None:
            return None
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

    def validate(self, attrs):
        user = self.context.get("user")
        inbound_rules = attrs.get("inbound_rules", [])
        outbound_rules = attrs.get("outbound_rules", [])
        virtance_ids = list(set(attrs.get("virtance_ids", [])))

        # Check inbound_rules duplicates
        if inbound_rules:
            in_rule_checked = set()
            for in_rule in inbound_rules:
                # Check 0.0.0.0/0 in sources
                src_addrs = in_rule.get("sources").get("addresses")
                if "0.0.0.0/0" in src_addrs and len(src_addrs) > 1:
                    raise serializers.ValidationError(
                        "Source '0.0.0.0/0' are allowed. Please remove other sources."
                    )

                # Check sources duplicates
                cidr_src_checked = set()
                for cidr in src_addrs:
                    if cidr in cidr_src_checked:
                        raise serializers.ValidationError("Please check duplication in sources.")
                    cidr_src_checked.add(cidr)

                in_rule_data = (in_rule.get('protocol'), in_rule.get('ports'))
                if in_rule_data in in_rule_checked:
                    raise serializers.ValidationError("Please check duplicate in inbound rules.")
                in_rule_checked.add(in_rule_data)

        # Check outbound_rules duplicates
        if outbound_rules:
            out_rule_checked = set()
            for out_rule in outbound_rules:
                # Check 0.0.0.0/0 in destinations
                dest_addrs = out_rule.get("destinations").get("addresses")
                if "0.0.0.0/0" in dest_addrs and len(dest_addrs) > 1:
                    raise serializers.ValidationError(
                        "Destination '0.0.0.0/0' are allowed. Please remove other destinations."
                    )

                # Check destinations duplicates
                cidr_dest_checked = set()
                for cidr in dest_addrs:
                    if cidr in cidr_dest_checked:
                        raise serializers.ValidationError("Please check duplication in destinations.")
                    cidr_dest_checked.add(cidr)
               
                out_rule_data = (out_rule.get('protocol'), out_rule.get('ports'))
                if out_rule_data in out_rule_checked:
                    raise serializers.ValidationError("Please check duplicate in outbound rules.")
                out_rule_checked.add(out_rule_data)

        # Check integer list in virtance_ids
        for v_id in virtance_ids:
            if not isinstance(v_id, int):
                raise serializers.ValidationError({"virtance_ids": ["This field must be a list of integers."]})

        # Check virtance exists
        list_ids = Virtance.objects.filter(
            user=user, id__in=virtance_ids, is_deleted=False
        ).values_list("id", flat=True)
        for v_id in virtance_ids:
            if v_id not in list_ids:
                raise serializers.ValidationError(f"Virtance with ID {v_id} does not exist.")

        # Check virtance already assigned
        for v_id in virtance_ids:
            if FirewallVirtance.objects.filter(firewall=self.instance, virance_id=v_id).exists():
                raise serializers.ValidationError(f"Virtance with ID {v_id} is already assigned firewall.")

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)

        inbound_rules = Rule.objects.filter(firewall=instance, direction=Rule.INBOUND, is_system=False)
        for in_rule in inbound_rules:
            in_rule.sources = {}
            in_rule.sources["addresses"] = [f"{i.address}/{i.prefix}" for i in Cidr.objects.filter(rule=in_rule)]
        data["inbound_rules"] = InboundRuleSerializer(inbound_rules, many=True).data
        outbound_rules = Rule.objects.filter(firewall=instance, direction=Rule.OUTBOUND, is_system=False)
        for out_rule in outbound_rules:
            out_rule.destinations = {}
            out_rule.destinations["addresses"] = [f"{i.address}/{i.prefix}" for i in Cidr.objects.filter(rule=out_rule)]
        data["outbound_rules"] = OutboundRuleSerializer(outbound_rules, many=True).data

        firewallvirtance = FirewallVirtance.objects.filter(firewall=instance)
        data["virtance_ids"] = [fv.virtance.id for fv in firewallvirtance]

        return data

    def update(self, instance, validated_data):
        name = validated_data.get("name")
        inbound_rules = validated_data.get("inbound_rules")
        outbound_rules = validated_data.get("outbound_rules")

        if name:
            instance.name = name
            instance.save()

        # Inbound rules
        if inbound_rules:
            # Delete old inbound rules
            for in_rule in Rule.objects.filter(firewall=instance, direction=Rule.INBOUND, is_system=False):
                Cidr.objects.filter(rule=in_rule).delete()
                in_rule.delete()

            # Create new inbound rules
            for in_rule in inbound_rules:
                if in_rule.get("protocol") == Rule.ICMP:
                    in_rule["ports"] = 0

                rule = Rule.objects.create(
                    firewall=instance,
                    direction=Rule.INBOUND,
                    protocol=in_rule.get("protocol"),
                    action=Rule.ACCEPT,
                    ports=in_rule.get("ports", 0),
                )
                for cidr in list(set(in_rule.get("sources").get("addresses"))):
                    if "/" in cidr:
                        address = cidr.split("/")[0]
                        prefix = cidr.split("/")[1]
                    else:
                        address = cidr
                        prefix = 32
                    Cidr.objects.create(
                        rule=rule,
                        address=address,
                        prefix=prefix,
                    )

        if outbound_rules:
            # Delete old outbound rules
            for out_rule in Rule.objects.filter(firewall=instance, direction=Rule.OUTBOUND, is_system=False):
                Cidr.objects.filter(rule=out_rule).delete()
                out_rule.delete()

            # Create new outbound rules
            for in_rule in inbound_rules:
                if in_rule.get("protocol") == Rule.ICMP:
                    in_rule["ports"] = 0

                rule = Rule.objects.create(
                    firewall=instance,
                    direction=Rule.OUTBOUND,
                    protocol=in_rule.get("protocol"),
                    action=Rule.ACCEPT,
                    ports=in_rule.get("ports", 0),
                )
                for cidr in list(set(in_rule.get("sources").get("addresses"))):
                    if "/" in cidr:
                        address = cidr.split("/")[0]
                        prefix = cidr.split("/")[1]
                    else:
                        address = cidr
                        prefix = 32
                    Cidr.objects.create(
                        rule=rule,
                        address=address,
                        prefix=prefix,
                    )

        # Update rules for virtances
        for fw_to_virt in FirewallVirtance.objects.filter(firewall=instance):
            instance.event = Firewall.UPDATE
            instance.save()
            virtance = Virtance.objects.get(id=fw_to_virt.virtance.id)
            virtance.event = Virtance.FIREWALL_ATTACH
            virtance.save()
            firewall_update.delay(instance.id, virtance.id)

        return instance

    def create(self, validated_data):
        user = self.context.get("user")
        name = validated_data.get("name")
        virtance_ids = validated_data.get("virtance_ids", [])
        inbound_rules = validated_data.get("inbound_rules", [])
        outbound_rules = validated_data.get("outbound_rules", [])

        firewall = Firewall.objects.create(name=name, event=Firewall.CREATE, user=user)

        # Create system rules for inbound
        rule = Rule.objects.create(
            firewall=firewall,
            direction=Rule.INBOUND,
            protocol=None,  # All protocols
            action=Rule.DROP,
            ports=0,
            is_system=True,
        )
        Cidr.objects.create(
            rule=rule,
            address="0.0.0.0",
            prefix=0,
        )

        if len(inbound_rules) == 0:
            # Allow SSH
            rule = Rule.objects.create(
                firewall=firewall,
                direction=Rule.INBOUND,
                protocol=Rule.TCP,
                action=Rule.ACCEPT,
                ports=22,
            )
            Cidr.objects.create(
                rule=rule,
                address="0.0.0.0",
                prefix=0,
            )

        # Create user rules for inbound
        for in_rule in inbound_rules:
            if in_rule.get("protocol") == Rule.ICMP:
                in_rule["ports"] = 0

            rule = Rule.objects.create(
                firewall=firewall,
                direction=Rule.INBOUND,
                protocol=in_rule.get("protocol"),
                action=Rule.ACCEPT,
                ports=in_rule.get("ports", 0),
            )
            for cidr in list(set(in_rule.get("sources").get("addresses"))):
                if "/" in cidr:
                    address = cidr.split("/")[0]
                    prefix = cidr.split("/")[1]
                else:
                    address = cidr
                    prefix = 32
                Cidr.objects.create(
                    rule=rule,
                    address=address,
                    prefix=prefix,
                )

        # Create system rules for outbound
        rule = Rule.objects.create(
            firewall=firewall,
            direction=Rule.OUTBOUND,
            protocol=None,  # All protocols
            action=Rule.DROP,
            ports=0,
            is_system=True,
        )
        Cidr.objects.create(
            rule=rule,
            address="0.0.0.0",
            prefix=0,
        )

        # Create default outbound rule if no user rules
        if len(outbound_rules) == 0:
            # All TCP
            rule = Rule.objects.create(
                firewall=firewall,
                direction=Rule.OUTBOUND,
                protocol=Rule.TCP,
                action=Rule.ACCEPT,
                ports=0,
            )
            Cidr.objects.create(
                rule=rule,
                address="0.0.0.0",
                prefix=0,
            )
            # All UDP
            rule = Rule.objects.create(
                firewall=firewall,
                direction=Rule.OUTBOUND,
                protocol=Rule.UDP,
                action=Rule.ACCEPT,
                ports=0,
            )
            Cidr.objects.create(
                rule=rule,
                address="0.0.0.0",
                prefix=0,
            )
            # All ICMP
            rule = Rule.objects.create(
                firewall=firewall,
                direction=Rule.OUTBOUND,
                protocol=Rule.ICMP,
                action=Rule.ACCEPT,
                ports=0,
            )
            Cidr.objects.create(
                rule=rule,
                address="0.0.0.0",
                prefix=0,
            )

        # Create user rules for outbound
        for out_rule in outbound_rules:
            if out_rule.get("protocol") == Rule.ICMP:
                out_rule["ports"] = 0

            rule = Rule.objects.create(
                firewall=firewall,
                direction=Rule.OUTBOUND,
                protocol=out_rule.get("protocol"),
                action=Rule.ACCEPT,
                ports=out_rule.get("ports", 0),
            )
            for cidr in list(set(out_rule.get("destinations").get("addresses"))):
                if "/" in cidr:
                    address = cidr.split("/")[0]
                    prefix = cidr.split("/")[1]
                else:
                    address = cidr
                    prefix = 32
                Cidr.objects.create(
                    rule=rule,
                    address=address,
                    prefix=prefix,
                )

        # Reset event if no virtances
        if len(list(set(virtance_ids))) == 0:
            firewall.reset_event()

        # Create Virtance links to firewall
        for virtance_id in list(set(virtance_ids)):
            FirewallVirtance.create(
                firewall=firewall,
                virtance_id=virtance_id,
            )

        # Attach firewall to virtances
        for virtance_id in list(set(virtance_ids)):
            firewall_attach.delay(firewall.id, virtance_id)

        return firewall


class FirewallAddRuleSerializer(serializers.Serializer):
    inbound_rules = ListOfInboundRulesSerializer(required=False)
    outbound_rules = ListOfOutboundRulesSerializer(required=False)

    def validate(self, data):
        if not data.get("inbound_rules") and not data.get("outbound_rules"):
            raise serializers.ValidationError("You must specify at least one rule.")

        if data.get("inbound_rules"):
            for in_rule in data.get("inbound_rules"):
                try:
                    Rule.objects.get(
                        firewall=self.instance,
                        direction=Rule.INBOUND,
                        protocol=in_rule.get("protocol"),
                        action=Rule.ACCEPT,
                        ports=in_rule.get("ports", 0),
                    )
                    raise serializers.ValidationError("The rule already exists.")
                except Rule.DoesNotExist:
                    pass

        if data.get("outbound_rules"):
            for out_rule in data.get("outbound_rules"):
                try:
                    Rule.objects.get(
                        firewall=self.instance,
                        direction=Rule.OUTBOUND,
                        protocol=out_rule.get("protocol"),
                        action=Rule.ACCEPT,
                        ports=out_rule.get("ports", 0),
                    )
                    raise serializers.ValidationError("The rule already exists.")
                except Rule.DoesNotExist:
                    pass

        return data

    def update(self, instance, validated_data):
        if validated_data.get("inbound_rules"):
            for in_rule in validated_data.get("inbound_rules"):
                if in_rule.get("protocol") == Rule.ICMP:
                    in_rule["ports"] = 0

                rule = Rule.objects.create(
                    firewall=instance,
                    direction=Rule.INBOUND,
                    protocol=in_rule.get("protocol"),
                    action=Rule.ACCEPT,
                    ports=in_rule.get("ports", 0),
                )
                for cidr in list(set(in_rule.get("sources").get("addresses"))):
                    if "/" in cidr:
                        address = cidr.split("/")[0]
                        prefix = cidr.split("/")[1]
                    else:
                        address = cidr
                        prefix = 32
                    Cidr.objects.create(
                        rule=rule,
                        address=address,
                        prefix=prefix,
                    )

        if validated_data.get("outbound_rules"):
            for out_rule in validated_data.get("outbound_rules"):
                if out_rule.get("protocol") == Rule.ICMP:
                    out_rule["ports"] = 0

                rule = Rule.objects.create(
                    firewall=instance,
                    direction=Rule.OUTBOUND,
                    protocol=out_rule.get("protocol"),
                    action=Rule.ACCEPT,
                    ports=out_rule.get("ports", 0),
                )
                for cidr in list(set(out_rule.get("destinations").get("addresses"))):
                    if "/" in cidr:
                        address = cidr.split("/")[0]
                        prefix = cidr.split("/")[1]
                    else:
                        address = cidr
                        prefix = 32
                    Cidr.objects.create(
                        rule=rule,
                        address=address,
                        prefix=prefix,
                    )

        # Update rules for virtances
        for fw_to_virt in FirewallVirtance.objects.filter(firewall=instance):
            instance.event = Firewall.UPDATE
            instance.save()
            virtance = Virtance.objects.get(id=fw_to_virt.virtance.id)
            virtance.event = Virtance.FIREWALL_ATTACH
            virtance.save()
            firewall_update.delay(instance.id, virtance.id)

        return validated_data


class FirewallDelRuleSerializer(serializers.Serializer):
    inbound_rules = ListOfInboundRulesSerializer(required=False)
    outbound_rules = ListOfOutboundRulesSerializer(required=False)

    def validate(self, data):
        if not data.get("inbound_rules") and not data.get("outbound_rules"):
            raise serializers.ValidationError("You must specify at least one rule.")

        if data.get("inbound_rules"):
            for in_rule in data.get("inbound_rules"):
                try:
                    Rule.objects.get(
                        firewall=self.instance,
                        direction=Rule.INBOUND,
                        protocol=in_rule.get("protocol"),
                        action=Rule.ACCEPT,
                        ports=in_rule.get("ports", 0),
                    )
                except Rule.DoesNotExist:
                    raise serializers.ValidationError("The rules does not exist.")

        if data.get("outbound_rules"):
            for out_rule in data.get("outbound_rules"):
                try:
                    Rule.objects.get(
                        firewall=self.instance,
                        direction=Rule.OUTBOUND,
                        protocol=out_rule.get("protocol"),
                        action=Rule.ACCEPT,
                        ports=out_rule.get("ports", 0),
                    )
                except Rule.DoesNotExist:
                    raise serializers.ValidationError("The rules does not exist.")

        return data

    def update(self, instance, validated_data):
        if validated_data.get("inbound_rules"):
            for in_rule in validated_data.get("inbound_rules"):
                rule = Rule.objects.get(
                    firewall=instance,
                    direction=Rule.INBOUND,
                    protocol=in_rule.get("protocol"),
                    action=Rule.ACCEPT,
                    ports=in_rule.get("ports", 0),
                )
                Cidr.objects.filter(rule=rule).delete()
                rule.delete()

        if validated_data.get("outbound_rules"):
            for out_rule in validated_data.get("outbound_rules"):
                rule = Rule.objects.get(
                    firewall=instance,
                    direction=Rule.OUTBOUND,
                    protocol=out_rule.get("protocol"),
                    action=Rule.ACCEPT,
                    ports=out_rule.get("ports", 0),
                )
                Cidr.objects.filter(rule=rule).delete()
                rule.delete()

        # Update rules for virtances
        for fw_to_virt in FirewallVirtance.objects.filter(firewall=instance):
            instance.event = Firewall.UPDATE
            instance.save()
            virtance = Virtance.objects.get(id=fw_to_virt.virtance.id)
            virtance.event = Virtance.FIREWALL_ATTACH
            virtance.save()
            firewall_update.delay(instance.id, virtance.id)

        return validated_data


class FirewallAddVirtanceSerializer(serializers.Serializer):
    virtance_ids = serializers.ListField(required=True)

    def validate(self, attrs):        
        virtance_ids = list(set(attrs.get("virtance_ids")))

        for v_id in virtance_ids:
            if not isinstance(v_id, int):
                raise serializers.ValidationError({"virtance_ids": ["This field must be a list of integers."]})

        list_ids = Virtance.objects.filter(
            user=self.instance.user, id__in=virtance_ids, is_deleted=False
        ).values_list("id", flat=True)
        for v_id in virtance_ids:
            if v_id not in list_ids:
                raise serializers.ValidationError(f"Virtance with ID {v_id} not found.")

        for v_id in virtance_ids:
            if FirewallVirtance.objects.filter(firewall=self.instance, virtance_id=v_id).exists():
                raise serializers.ValidationError(f"Virtance with ID {v_id} has already assigned firewall.")

        return attrs

    def update(self, instance, validated_data):
        virtance_ids = list(set(validated_data.get("virtance_ids")))

        for v_id in virtance_ids:
            FirewallVirtance.objects.create(firewall=instance, virtance_id=v_id)

        for virtance_id in virtance_ids:
            instance.event = Firewall.UPDATE
            instance.save()
            virtance = Virtance.objects.get(id=virtance_id)
            virtance.event = Virtance.FIREWALL_ATTACH
            virtance.save()
            firewall_attach.delay(instance.id, virtance.id)

        return validated_data


class FirewallDelVirtanceSerializer(serializers.Serializer):
    virtance_ids = serializers.ListField(required=True)

    def validate(self, attrs):
        virtance_ids = list(set(attrs.get("virtance_ids")))

        for v_id in virtance_ids:
            if not isinstance(v_id, int):
                raise serializers.ValidationError({"virtance_ids": ["This field must be a list of integers."]})

        for v_id in virtance_ids:
            if not FirewallVirtance.objects.filter(firewall=self.instance, virtance_id=v_id).exists():
                raise serializers.ValidationError(f"Virtance with ID {v_id} doesn't have assigned firewall.")

        return attrs

    def update(self, instance, validated_data):
        virtance_ids = list(set(validated_data.get("virtance_ids")))
        
        for virtance_id in virtance_ids:
            instance.event = Firewall.UPDATE
            instance.save()
            virtance = Virtance.objects.get(id=virtance_id)
            virtance.event = Virtance.FIREWALL_DETACH
            virtance.save()
            firewall_detach.delay(instance.id, virtance.id)

        return validated_data
