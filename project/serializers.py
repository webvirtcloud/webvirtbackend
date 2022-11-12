from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    default = serializers.BooleanField(source='is_default', required=False)
    description = serializers.CharField(required=False)
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Project
        fields = ['uuid', 'name', 'default', 'description', 'created', 'updated']

    def validate(self, attrs):
        name = attrs.get('name')
        description = attrs.get('description')
        
        if name and len(name) > 100:
            raise serializers.ValidationError("Name must be less than 100 characters long.")

        if description and len(description) > 255:
            raise serializers.ValidationError("Description must be less than 1000 characters long.")

        return attrs

    def create(self, validated_data):
        return Project.objects.create(**validated_data)

    def update(self, instance, validated_data):
        name = validated_data.get('name', instance.name)
        default = validated_data.get('default', instance.is_default)
        description = validated_data.get('description', instance.description)

        instance.name = name
        instance.is_default = default
        instance.description = description
        instance.save()

        return instance
