from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    default = serializers.BooleanField(source='is_default', required=False)
    description = serializers.CharField()
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(required=True)

    class Meta:
        model = Project
        fields = ['uuid', 'name', 'default', 'description', 'created', 'updated']

    def create(self, validated_data):
        return Project.objects.create(**validated_data)

    def update(self, instance, validated_data):
        name = validated_data.get('name', instance.name)
        default = validated_data.get('default', instance.default)
        description = validated_data.get('description', instance.description)

        instance.name = name
        instance.default = default
        instance.description = description
        instance.save()

        return instance
