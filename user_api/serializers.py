from rest_framework import serializers
from .models import User
from admin_app.models import MovieRating,WatchList,WatchHistory,UserSubscriptions


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required = True)
    new_password = serializers.CharField(required = True)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class ResetNewPasswordSerializer(serializers.Serializer):
    new_pasword = serializers.CharField(required = True)

class MovieRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieRating
        fields = ['movie','movie_rating'] #user excluded here because it is explicitily added when savin time

class WatchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchList
        fields = ['movie']

class WatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchHistory
        fields = ['movie','added_at']
        read_only_fields = ['added_at'] # It make to get the movie watch date , if it not given (means to given like this read_only_fields) then we need to explicitly add the datetime

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscriptions
        fields = ['subscription_plan','date_of_taken']
        read_only_fields = ['date_of_taken'] # It make to get the subscription purchase date , if it not given(means to given like this read_only_fields) then we need to explicitly add the datetime