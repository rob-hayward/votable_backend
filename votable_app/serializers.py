# serializers.py
from rest_framework import serializers
from .models import Votable


class VotableSerializer(serializers.ModelSerializer):
    user_vote = serializers.SerializerMethodField()
    votable_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Votable
        fields = '__all__'

    def get_user_vote(self, obj):
        user = self.context.get('request').user
        return obj.get_user_vote(user)

    def get_votable_type_display(self, obj):
        return obj.get_votable_type_display()


class VotableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Votable
        fields = ('title', 'text', 'votable_type')