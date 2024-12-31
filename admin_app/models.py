from django.db import models
from user_api.models import User

# # Create your models here.

class MovieList(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.FileField(upload_to='uploads/images/')
    video = models.FileField(upload_to='uploads/videos/')
    movie_rating = models.DecimalField(max_digits=2,decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

class SubscriptionPlan(models.Model):
    plan_name = models.CharField(max_length=255)
    plan_description = models.TextField()
    plan_price = models.IntegerField()
    plan_validity = models.IntegerField()
    plan_added = models.DateTimeField(auto_now_add=True)
    is_enabled = models.BooleanField(default=True)

class UserSubscriptions(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan,on_delete=models.CASCADE)
    date_of_taken = models.DateTimeField(auto_now_add=True)

class WatchList(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    movie = models.ForeignKey(MovieList,on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class WatchHistory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    movie = models.ForeignKey(MovieList,on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class MovieRating(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE) #automatically change user to user_id in db
    movie = models.ForeignKey(MovieList,on_delete=models.CASCADE)#same here
    movie_rating = models.DecimalField(max_digits=2,decimal_places=1)
    added_at = models.DateTimeField(auto_now_add=True)



