import re
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Count
import os 
from user_api.models import User
from .models import MovieList,SubscriptionPlan,WatchHistory,UserSubscriptions 
from django.contrib import messages # using django inbuild message system to show success and errors
# Create your views here.

#Admin signUp

def admin_signup(request):
    userObj = User()

    userObj.name = 'Sarath'
    userObj.email = 'sarath@gmail.com'
    userObj.username = 'sarath@gmail.com'
    userObj.set_password('Sarath@123')
    # userObj.is_superuser = True
    userObj.save()
    return HttpResponse('Admin Created Successfully')

# function to check is super user or not

def customFn_check_is_superuser(user):
    return user.is_superuser

#Admin  login

def admin_login(request):
    print(request.POST)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email == '' or password == '':
            messages.error(request,'All fields required.')
            return redirect('/')
        else:
            user = authenticate(username = email ,password = password)
            
            if user:
                # check whether user is superuser using custom function or not
                if customFn_check_is_superuser(user):
                    login(request,user)
                    return redirect('/get-all-movies')
                else:
                    messages.error(request,"Sorry, you don't have permission to access this page")
                    return redirect('/')

            else:    
                messages.error(request,'Invalid Credentials')
                return redirect('/')
          
    return render(request,'auth_pages/admin_login_page.html')

# Check password format is strong

def is_password_strong(password):
    pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d#@$!%*?&]{8,}$'
    if password is None:
        return False
    return bool(re.match(pattern,password)) # return True or False

#Admin change Password

@login_required(login_url='/')
def admin_change_password(request):
    print(request.user)
    user = request.user

    if not customFn_check_is_superuser(user):
        messages.error(request,"Sorry, you don't have permission to access this page")
        return redirect('/')

    if request.method == 'POST':
        user_old_password = request.POST.get('currentPassword')
        user_new_password = request.POST.get('newPassword')
        user_new_passwordConf = request.POST.get('passwordConf')

        if user_old_password == '' or user_new_password == '' or user_new_passwordConf =='':
            messages.error (request,'All fields required.')
            return redirect('/admin-change-password')
        elif user_new_password != user_new_passwordConf :
            messages.error (request,'''Passwords don't match.''')
            return redirect('/admin-change-password')
        elif not is_password_strong(user_new_password):
            messages.error (request,'Password is too weak.Password must be at least 8 characters long with at least one capital letter and symbol.')
            return redirect('/admin-change-password')
        elif not user.check_password(user_old_password): #Check pass return true or false
            messages.error (request,'Incorrect current password.')
            return redirect('/admin-change-password')
        else:
            user.set_password(user_new_password)
            user.save()
            # password_message = 'Password changed successfully'
            return redirect('/')     
    return render(request,'auth_pages/admin_change_password_page.html')


#Admin forgot request mail
@login_required(login_url='/')
def admin_forgot_password_request(request):

    if request.method == 'POST':
        email = request.POST.get('email')

        if email == '':
            messages.error(request,'Email field is required.')
            print(email)
        else:
            is_admin = User.objects.filter(email__exact = email) # here it is queryset
            print(is_admin.first()) # here first() convert queryset into object
            if is_admin:
                if customFn_check_is_superuser(is_admin.first()):
                    token_generator = PasswordResetTokenGenerator()
                    token = token_generator.make_token(is_admin.first())
                    is_admin.update(password_reset_token = token) # Token created
                    password_reset_url = f"http://127.0.0.1:8000/admin-reset-password/{token}/"
                    subject = f'ott platform reset password'
                    from_email = 'Ott_platform@gmail.in.com'
                    recipient_list = ["your_mailtrap_inbox@mailtrap.io"]
                    html_message = render_to_string('password_reset_mail.html',{'link':password_reset_url})
                    plain_message = strip_tags(html_message)
                    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
                    messages.success(request,'A password reset link has been emailed to you. Check your inbox!')
                    return redirect('/admin-forgot-password-request')
                else:
                    messages.error(request,"Sorry, you don't have permission to access this page")
                    return redirect('/admin-forgot-password-request')
            else:
                messages.error (request,'Invalid Email address.')
    return render(request,'auth_pages/admin_forgot_password_page.html')

#Admin set the new password
@login_required(login_url='/')
def reset_new_password(request,token):
    print(token)
    print(request.POST)
    new_password = request.POST.get('newPassword')
    new_password_conf = request.POST.get('newPasswordConf')

    if request.method == 'POST':
        if  new_password == '' or new_password_conf =='':
            messages.error (request,'Please fill both the fields.')
            return redirect(f'/admin-reset-password/{token}/')
      
        if new_password != new_password_conf :
            messages.error (request,'''Passwords don't match.''')
            return redirect(f'/admin-reset-password/{token}/')
        if not is_password_strong(new_password):
            messages.error (request,'Password is too weak.Password must be at least 8 characters long with at least one capital letter and symbol.')    
            return redirect(f'/admin-reset-password/{token}/')
    
        is_valid_token_admin = User.objects.filter(password_reset_token = token).first()
        print(is_valid_token_admin)
        if is_valid_token_admin:
            is_valid_token_admin.set_password(new_password)
            is_valid_token_admin.password_reset_token = None
            is_valid_token_admin.save()
            return redirect('/')
        else:
            return HttpResponse('Oops! This link is no longer valid.')
    return render(request,'auth_pages/admin_rest_password_page.html')


#Check image the file type is valid

def check_thumbnail_file_type(thumbnail):
    IMAGE_FILE_TYPES = ['jpg', 'jpeg','png']
    movie_instance = MovieList()
    movie_instance.thumbnail = thumbnail
    image_file_type = movie_instance.thumbnail.url.split('.')[-1]
    if image_file_type.lower() in IMAGE_FILE_TYPES:
        return True
    else:
        return False

#Check video the file type is valid

def check_video_file_type(video):
    VIDEO_FILE_TYPES = 'mp4'
    movie_instance = MovieList()
    movie_instance.video = video
    video_file_type = movie_instance.video.url.split('.')[-1]
    if video_file_type.lower() in VIDEO_FILE_TYPES:
        return True
    else:
        return False

# Movie create
@login_required(login_url='/')
def movie_create(request):
    print(request.POST)
    print(request.FILES)

    if not customFn_check_is_superuser(request.user):
        messages.error(request,"Sorry, you don't have permission to access this page")
        return redirect('/')

    new_title = request.POST.get('title')
    new_description = request.POST.get('description')
    new_rating = request.POST.get('rating')
    new_thumbnail = request.FILES.get('thumbnail')
    new_video = request.FILES.get('video')

    if request.method == 'POST':
        if new_title == '' or new_description == '' or new_rating == '' or new_thumbnail == '' or new_video == '':
           messages.error( request,'Please fill all fields')
           return redirect('/add-movie')
        if len(new_description) > 185:
           messages.error( request,'Description is too long. Please limit it to 185 characters.')
           return redirect('/add-movie')
        if not check_thumbnail_file_type(new_thumbnail):
           messages.error( request,'Invalid thumbanil file type. Please upload an image in JPG, JPEG, or PNG format.')
           return redirect('/add-movie')
        if not check_video_file_type(new_video):
           messages.error( request,'Invalid video file type. Please upload an video in MP4 format.')
           return redirect('/add-movie')
        else:
            new_movie_data = MovieList(title = new_title,description = new_description, movie_rating = new_rating, thumbnail = new_thumbnail, video = new_video)
            new_movie_data.save()
            messages.success(request,'Movie added successfully!')
            return redirect('/add-movie')
        
    return render(request,'movie_pages/admin_movie_create_page.html')

#Movie List
@login_required(login_url='/')
def movie_retrieve(request):
    # to show reset btn and search btn vice-verse
    is_clicked_searchBtn = False
    if request.method == 'GET':
        # check have search term or not
        search_term = request.GET.get('searchTerm')
        print(search_term)

        if search_term:
            movie_data = MovieList.objects.filter(title__icontains = search_term)
            is_clicked_searchBtn = True
            if not movie_data.exists():
                messages.error(request,'No Movie Found!')
                 
            print(movie_data)
        else:
            movie_data = MovieList.objects.all()
            is_clicked_searchBtn = False

        paginator = Paginator(movie_data,5)
        page_number = request.GET.get('page') #on click the page number to get
        page_obj = paginator.get_page(page_number)
        print(request.user.is_superuser)
        return render(request,'movie_pages/admin_movie_list_page.html',{'movie_data':page_obj,'is_clicked_searchBtn':is_clicked_searchBtn})
       
    return render(request,'movie_pages/admin_movie_list_page.html',{'movie_data':[],'is_clicked_searchBtn':is_clicked_searchBtn})


#Movie View
@login_required(login_url='/')
def movie_view(request,movie_id):
    if request.method == 'GET':
        try:
            movie = MovieList.objects.get(pk = movie_id)
            print(movie)
        except MovieList.DoesNotExist:
            messages.error(request,'Movie not Found!')
            return redirect('/get-all-movies')
    return render(request,'movie_pages/admin_movie_view_page.html',{'movie':movie})


# Movie Edit
@login_required(login_url='/')
def movie_update(request,movie_id):
    
    try:
        movie_instance_to_edit = MovieList.objects.get(pk = movie_id)
        print(movie_instance_to_edit)
    except:
        messages.error(request,'Movie not Found!')
        return redirect('/get-all-movies')
    
    if request.method == 'POST':
        print(request.POST)
        print(request.FILES)

        edited_title = request.POST.get('title')
        edited_description = request.POST.get('description')
        edited_rating = request.POST.get('rating')
        edited_thumbnail = request.FILES.get('thumbnail')
        edited_video = request.FILES.get('video')
        

        if edited_title == '' or edited_description == '' or edited_rating == '':
           messages.error( request,'Please fill all fields')
           return redirect(f'/edit-movie/{movie_id}')
        if len(edited_description) > 185:
           messages.error( request,'Description is too long. Please limit it to 185 characters.')
           return redirect(f'/edit-movie/{movie_id}')
        
        #Check whether the edited request files contains new files
        if len(request.FILES) != 0:
            #Check have thumbnail
            if edited_thumbnail:
                if not check_thumbnail_file_type(edited_thumbnail):
                    messages.error( request,'Invalid thumbanil file type. Please upload an image in JPG, JPEG, or PNG format.')
                    return redirect(f'/edit-movie/{movie_id}')
                elif movie_instance_to_edit.thumbnail and os.path.exists(movie_instance_to_edit.thumbnail.path):
                    # This condition that check whether the new file has same name of old then also it consider both as different
                    if movie_instance_to_edit.thumbnail.name != edited_thumbnail.name:
                        os.remove(movie_instance_to_edit.thumbnail.path) #delete the actual image
                        movie_instance_to_edit.thumbnail = edited_thumbnail
                else:
                    movie_instance_to_edit.thumbnail = edited_thumbnail

            #check have video
            if edited_video:
                if not check_video_file_type(edited_video):
                    messages.error( request,'Invalid video file type. Please upload an video in MP4 format.')
                    return redirect(f'/edit-movie/{movie_id}')
                elif movie_instance_to_edit.video and  os.path.exists(movie_instance_to_edit.video.path):
                    # This condition that check whether the new file has same name of old then also it consider both as different
                    if movie_instance_to_edit.video.name != edited_video.name:
                        os.remove(movie_instance_to_edit.video.path)
                        movie_instance_to_edit.video = edited_video
                else:
                    movie_instance_to_edit.video = edited_video
        
        movie_instance_to_edit.title = edited_title
        movie_instance_to_edit.description = edited_description
        movie_instance_to_edit.movie_rating = edited_rating
        print(movie_instance_to_edit.title)
        movie_instance_to_edit.save()
        messages.success(request,'Movie edited successfully!')
        return redirect(f'/edit-movie/{movie_id}')

    return render(request,'movie_pages/admin_movie_edit_page.html',{'movie':movie_instance_to_edit})

# Movie Delete
@login_required(login_url='/')
def movie_delete(request,movie_id,):
    print(request.POST)
    print(movie_id)

    try:
        movie_data = MovieList.objects.get(pk = movie_id)
        movie_data.delete()
        # messages.success(request,'Movie deleted successfully.')
        return redirect('/get-all-movies')
    except MovieList.DoesNotExist:
        messages.error(request,'No Movie Found!')
    return redirect('/get-all-movies')

 
# User List
@login_required(login_url='/')
def get_user_Details(request):

    # to show reset btn and search btn vice-verse
    is_clicked_searchBtn = False
    if request.method == 'GET':
        search_name = request.GET.get('search_name')
        if search_name:
            users = User.objects.filter(Q(name__icontains = search_name ) & Q(is_superuser = False) | Q(email__icontains = search_name ) & Q(is_superuser = False))
            is_clicked_searchBtn = True
            if not users.exists():
                messages.error(request,'No User Data Found')
        else:
            users = User.objects.filter(is_superuser = False)
            is_clicked_searchBtn = False
            
        paginator = Paginator(users,1)
        page_number = request.GET.get('page') #on click the page number to get
        user_page_obj = paginator.get_page(page_number)
        print([user for user in users])
        return render(request,'user_pages/admin_user_list_page.html',{'users_data':user_page_obj,'is_clicked_searchBtn':is_clicked_searchBtn})
    return render(request,'user_pages/admin_user_list_page.html',{'users_data':[],'is_clicked_searchBtn':is_clicked_searchBtn})
       

# User View to show subscription details and history details
@login_required(login_url='/')

def get_user_history_and_subscription_details(request,user_id):

    if request.method == 'GET': 
        try:
            user_watch_history = WatchHistory.objects.filter(user = user_id).order_by('-added_at') # Queryset watch history object
            for data in user_watch_history:
                print(data.movie.title) # can be access movieList instance
            print(user_watch_history)
            paginator = Paginator(user_watch_history,10)
            page_number = request.GET.get('page') #on click the page number to get
            user_watch_page_obj = paginator.get_page(page_number)
        except WatchHistory.DoesNotExist:
            messages.error(request,'No Watch History for this user.')
        try:
            user_subscriptions = UserSubscriptions.objects.filter(user = user_id).order_by('-date_of_taken')
            print(user_subscriptions)
            paginator = Paginator(user_subscriptions,3)
            page_number = request.GET.get('page') #on click the page number to get
            user_subscription_page_obj = paginator.get_page(page_number)
        except UserSubscriptions.DoesNotExist:
            return
        return render(request,'user_pages/admin_user_more_detail_page.html',
                      {'user_watch_history_data':user_watch_page_obj,
                      'user_subscription_page_obj':user_subscription_page_obj})
    return render(request,'user_pages/admin_user_more_detail_page.html',
                  {'user_watch_history_data':[],
                  'user_subscription_page_obj':[]})
    

#User Block and Unblock
@login_required(login_url='/')
def handle_user_block_or_unblock(request,user_id):
    
    user_obj = get_object_or_404( User,pk = user_id)
    print(user_obj.is_blocked)
    
    # check if user not blocked
    if not user_obj.is_blocked:
        user_obj.is_blocked = True
        user_obj.save()
        messages.error(request,'User successfully blocked.')
        return redirect('/get-all-users')

    else:
        user_obj.is_blocked = False
        user_obj.save()
        messages.success(request,'User successfully unblocked.')
        return redirect('/get-all-users')
    

#Subscription plan Create

def create_subscription_plans(request):
    
    print(request.POST)

    if request.method == 'POST':
        planName = request.POST.get('planName')
        planDescription = request.POST.get('planDescription')
        planPrice = request.POST.get('planPrice')
        planDuration = request.POST.get('planDuration')

        if planName == '' or planDescription == '' or planPrice == '' or planDuration == '':
           messages.error( request,'Please fill all fields')
           return redirect('/add-plans')
    
        new_plan = SubscriptionPlan(plan_name = planName,plan_description = planDescription,plan_price = planPrice,plan_validity = planDuration)
        new_plan.save()
        messages.success(request,'Plan added successfully!')
        return render(request,'subscription_pages/admin_subscription_create_page.html')

    return render(request,'subscription_pages/admin_subscription_create_page.html')


# Subscription list

def subscription_plans(request):
    search_name = request.GET.get('search_name')
    is_clicked_searchBtn = False
    if request.method == 'GET':
        if search_name:
            all_subscription_plans = SubscriptionPlan.objects.filter(plan_name__icontains = search_name)
            is_clicked_searchBtn = True

            if not all_subscription_plans.exists():
                messages.error(request,'No Subscription plans Found')
        else:
            all_subscription_plans = SubscriptionPlan.objects.all()
            is_clicked_searchBtn = False
            
        paginator = Paginator(all_subscription_plans,1)
        page_number = request.GET.get('page') #on click the page number to get
        subscription_plans_page_obj = paginator.get_page(page_number)
        return render(request,'subscription_pages/admin_subscription_plan_page.html',{'subscription_plans_page_obj':subscription_plans_page_obj,'is_clicked_searchBtn':is_clicked_searchBtn})
    return render(request,'subscription_pages/admin_subscription_plan_page.html',{'subscription_plans_page_obj':[],'is_clicked_searchBtn':is_clicked_searchBtn})

# Subscription View 

def subscription_plan_view(request,plan_id):
    if request.method == 'GET':
        try:
            individual_plan_data = SubscriptionPlan.objects.get(pk = plan_id)
        except SubscriptionPlan.DoesNotExist:
            messages.error('No plan Found')
            return redirect('/get-all-plans')
        return render(request,'subscription_pages/admin_subscription_plan_detailed_view_page.html',{'individual_plan_data':individual_plan_data})
    return render(request,'subscription_pages/admin_subscription_plan_detailed_view_page.html')
    
# Plan Enable and Disable

def handle_plan_enable_disable(request,plan_id):
    if request.method == 'GET':
        subscription_plan = get_object_or_404(SubscriptionPlan,pk = plan_id)
        if subscription_plan.is_enabled:
            subscription_plan.is_enabled = False
            messages.error(request,'Plan successfully disabled.')
            subscription_plan.save()
            return redirect('/get-all-plans')
        else:
            subscription_plan.is_enabled = True
            subscription_plan.save()
            messages.success(request,'Plan successfully Enabled.')
            return redirect('/get-all-plans')
    






#View Count Report
@login_required(login_url='/')
def handle_view_count(request):
    search_term = request.GET.get('searchTerm')
    is_clicked_searchBtn = False

    if request.method == 'GET':
        if search_term:
            movie_data_obj = MovieList.objects.annotate(view_count = Count('watchhistory')).filter(title__icontains = search_term).order_by('-view_count')
            # used annoate and added a extra attribute to the queryset
            is_clicked_searchBtn = True

            if not movie_data_obj.exists():
                pass
        else:
            movie_data_obj = MovieList.objects.annotate(view_count = Count('watchhistory')).order_by('-view_count')
            # used annoate and added a extra attribute to the queryset
            is_clicked_searchBtn = False

        paginator = Paginator(movie_data_obj,1)
        page_number = request.GET.get('page') #on click the page number to get
        movie_count_page_obj = paginator.get_page(page_number)
        return render(request,'report_pages/admin_view_count_page.html',{'movie_view_count_data':movie_count_page_obj,'is_clicked_searchBtn':is_clicked_searchBtn})

    return render(request,'report_pages/admin_view_count_page.html',{'movie_view_count_data':[],'is_clicked_searchBtn':is_clicked_searchBtn})

# Search view count movies
@login_required(login_url='/')
def search_movie_with_view_count(request):
    search_term = request.GET.get('movieCountdata','')

    print(search_term)
 
    search_movie_data = MovieList.objects.annotate(view_count = Count('watchhistory')).filter(title__icontains = search_term).order_by('-view_count')

    filteredMovieData = [{'id':movie_data.id , 'title':movie_data.title ,'view_count':movie_data.view_count } for movie_data in search_movie_data ]
    return JsonResponse(filteredMovieData,safe=False) 


def admin_logout(request):

    if request.method == 'POST':
        logout(request)
    return redirect('/')

