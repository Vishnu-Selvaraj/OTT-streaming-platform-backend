from django.urls import path
from . import views

urlpatterns = [

    path('signup',views.user_signup),
    path('login',views.user_login),
    path('change_password',views.user_changePassword),
    path('reset-password-request',views.reset_password_request),
    path('reset-new-password',views.reset_new_password),
    path('retrieve',views.movie_retrieve),
    path('view/<int:movieId>/',views.movie_view),
    path('user-rating',views.user_movie_rating),
    path('add-to-watchlist',views.add_movie_to_watchlater),
    path('get-watchlist-movies',views.get_watchlater_movies),
    path('delete-watchlist-movie/<int:movieId>/',views.delete_watchlater_movies),
    path('add-to-watchhistory',views.add_movies_to_watch_history),
    path('get-watchhistory-movies',views.get_watch_history_movies),
    path('get-subscription-plans',views.get_all_subscription_plans),
    path('view-subscription-plan/<int:subscriptionId>/',views.subscription_plan_view),
    path('user-to-subscription-plan',views.subscribe_user_to_plan),
    path('user-current-subscription-plan',views.user_current_subscription),
    path('user-previous-subscription-plans',views.user_previous_subscriptions_list),
    path('logout',views.user_logout),





]
