from django.urls import path
from . import views


urlpatterns = [

    path('',views.admin_login,name='admin_login'),
    path('admin-signup',views.admin_signup,name='signup'),
    path('admin-change-password',views.admin_change_password,name='admin_change_password'),
    path('admin-forgot-password-request',views.admin_forgot_password_request,name='forgot-password-request'),
    path('admin-reset-password/<str:token>/',views.reset_new_password,name='admin-reset-password'),
    path('add-movie',views.movie_create,name='create_movie'),
    path('get-all-movies',views.movie_retrieve,name='get_all_movies'),
    path('view-movie/<int:movie_id>/',views.movie_view,name='view_movie'),
    path('edit-movie/<int:movie_id>/',views.movie_update,name='update_movie'),
    path('delete-movie/<int:movie_id>/',views.movie_delete,name='delete_movie'),
    path('get-all-users',views.get_user_Details,name='get_all_users'),
    path('user-detailed-view/<int:user_id>/',views.get_user_history_and_subscription_details,name='user_detail_view'),
    path('user-block-or-unblock-request/<int:user_id>/',views.handle_user_block_or_unblock,name='user_block_or_unblock'),
    path('add-plans',views.create_subscription_plans,name='add_subscription_plans'),
    path('get-all-plans',views.subscription_plans,name='get_all_plans'),
    path('view-plan/<int:plan_id>/',views.subscription_plan_view,name='view_plan'),
    path('enable-or-disable-plans-request/<int:plan_id>/',views.handle_plan_enable_disable,name = 'plan_enable_or_disable'),

    path('view-count-report/',views.handle_view_count,name='view_count'),
    path('search-movie-view-count/',views.search_movie_with_view_count,name='search_movie_view_count'),
    path('logout',views.admin_logout,name='admin_logout_page'),



    








    # path('create',views.movie_create),
    # path('create-subscriptions',views.add_subscriptions),  

]