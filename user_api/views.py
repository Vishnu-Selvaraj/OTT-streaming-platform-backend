from django.shortcuts import render,get_object_or_404
from django.core.validators import EmailValidator
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db.models import Avg
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK,HTTP_201_CREATED,HTTP_400_BAD_REQUEST,
HTTP_404_NOT_FOUND,HTTP_401_UNAUTHORIZED,HTTP_409_CONFLICT)
from rest_framework.authtoken.models import Token
from .models import User
from admin_app.serializers import MovieListSerializer,SubscriptionPlanSerializer
from admin_app.models import MovieList,MovieRating,WatchList,WatchHistory,SubscriptionPlan,UserSubscriptions
from .serializers import MovieRatingSerializer,WatchListSerializer,WatchHistorySerializer,UserSubscriptionSerializer
from .serializers import ChangePasswordSerializer,ResetPasswordSerializer


# Create your views here.

#Custom function to normalize the email
def normalize_email(email):
    if email:
      return email.strip().lower()
    return email
   

@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))

def user_signup(request):
    
   name = request.data['name']
   email = request.data['email']
   password = request.data['password']

   validate_email = EmailValidator() # email validator class validate_email is the object

   if not name:
      return Response({'error':'Name field is required'},status=HTTP_400_BAD_REQUEST)
   elif not email:
      return Response({'error':'Please provide an email address in the proper format.'},status=HTTP_400_BAD_REQUEST)
   elif not password:
      return Response({'error':'password field is required'},status=HTTP_400_BAD_REQUEST)
    
   #password validation
   try:
      validate_password(password)
   except ValidationError as error:
      print(error)
      return Response({'error':error},status=HTTP_400_BAD_REQUEST)
    
   #Email format validation

   try:
      validate_email(email)
   except ValidationError as error:
      return Response({'error':error},status=HTTP_400_BAD_REQUEST)
   
   if User.objects.filter(email__exact=email).exists():
      return Response({'error':'Email already exists'},status=HTTP_400_BAD_REQUEST)
   else:   
      print(request.data['password'])
      email = normalize_email(email)
      user = User(name = name,email = email,username = email ) #adding username as email to avoid error because it already set as unique=True
      user.set_password(password)
      user.save()
      return Response({'message':'User Created'},status=HTTP_201_CREATED)


def customFn_to_check_user_blocked_or_not(user):
   print(user.is_blocked)
   return user.is_blocked

@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))

def user_login(request):
   email = request.data['email']
   password = request.data['password']

   if not email or not password:
      return Response({'error':'Please fill both fields'},status=HTTP_400_BAD_REQUEST)
    
   user = authenticate(username = email,password=password)
   if not user:
      return Response({'error':'Invalid Credentials'},status=HTTP_401_UNAUTHORIZED) 
   
   if customFn_to_check_user_blocked_or_not(user):
      return Response({'error':'Your account has been blocked. Please contact support for assistance.'},status=HTTP_401_UNAUTHORIZED) 
   
   else:
      print(user.is_blocked)
      login(request,user)
      token,_ = Token.objects.get_or_create(user = user)
      return Response({'token':token.key,'name':user.name},status=HTTP_200_OK) #ok
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def user_changePassword(request):
   
   serializer = ChangePasswordSerializer(data = request.data)
   if serializer.is_valid():
      user = request.user
      if user.check_password(serializer.data.get('old_password')): #condition satisfies retures True else False and also the check_password func changes the hashed password into raw password
         user.set_password(serializer.data.get('new_password')) #set new password hashed in db
         user.save() #then only password get updated on db
         return Response({'message':'Password changed successfully'},status=HTTP_200_OK)
      return Response({'error':'Incorrect current password'},status=HTTP_404_NOT_FOUND)
   return Response(serializer.errors,status=HTTP_400_BAD_REQUEST) #ok

#Forgot password/ sent reset-password-request mail
@api_view(['POST'])
@permission_classes((AllowAny,))

def reset_password_request(request):
   email_serializer = ResetPasswordSerializer(data = request.data)
   if email_serializer.is_valid():
      user = User.objects.filter(email__exact = email_serializer.data.get('email'))
      #Check user exists and not blocked
      if user.exists() and not customFn_to_check_user_blocked_or_not(user.first()):
         token_generator = PasswordResetTokenGenerator()
         token = token_generator.make_token(user.first()) # first() Take mail id directly from db
         print(token)
         user.update(password_reset_token = token)
         password_reset_url = f"http://localhost:3000/reset-password/{token}/"
         subject = f'ott platform'
         from_email = 'Ott_platform@gmail.in.com'
         recipient_list = ["your_mailtrap_inbox@mailtrap.io"]
         html_message = render_to_string('password_reset_mail.html',{'link':password_reset_url})
         plain_message = strip_tags(html_message)
         send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
         return Response({'message':'A password reset link has been emailed to you. Check your inbox!','token':token},status=HTTP_200_OK)
      if customFn_to_check_user_blocked_or_not(user.first()):
         return Response({'error':'Your account has been blocked. Please contact support for assistance.'},status=HTTP_401_UNAUTHORIZED)

      return Response({'error':'Invalid Email address'},status=HTTP_401_UNAUTHORIZED)
   return Response({'error':email_serializer.errors},status=HTTP_400_BAD_REQUEST)

#forgot password / confirm reset-new-password-request

@api_view(['POST'])
@permission_classes((AllowAny,))

def reset_new_password(request):
   token = request.data.get('token')
   newPassword = request.data.get('new_password')

   try:
      validate_password(newPassword)
   except ValidationError as error:
      return Response({'error':error},status=HTTP_400_BAD_REQUEST)
   
   user = User.objects.filter(password_reset_token__exact = token).first() # using first() matching first object is returned
   if user:
      user.set_password(newPassword)
      user.password_reset_token = None
      user.save()
      print(user.password_reset_token)   
      return Response(
         {'message':'Password reset successfully!.'},
         status=HTTP_201_CREATED
         )
   return Response(
      {'error':"You can't reset your password because the token is invalid."},
      status=HTTP_409_CONFLICT
      )


#movie Retrieve

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def movie_retrieve(request):
   
   if customFn_to_check_user_blocked_or_not(request.user):
      return Response({'error':'blocked'},status=HTTP_401_UNAUTHORIZED)
      
   else:
      movies = MovieList.objects.all().order_by('-created_at') 
      serializer = MovieListSerializer(movies,many = True) #no need of serializer validation 

   return Response({'message':serializer.data},status=HTTP_200_OK) #ok


'''Check User Subscription active or not'''

def check_user_subscription_valid_or_not(user_arg):

   userSubscriptions = UserSubscriptions.objects.filter(user = user_arg).order_by('-id').first()

   if userSubscriptions is None:
      return False
   plan_id = userSubscriptions.subscription_plan.id

   print(userSubscriptions.subscription_plan.id)

   subscriptionSerializer = SubscriptionPlanSerializer(userSubscriptions.subscription_plan)
   if len(subscriptionSerializer.data) != 0:
      today_date = timezone.now()
      valid_Usersubscription_obj = userSubscriptions
      plan_date = valid_Usersubscription_obj.date_of_taken # In here the plan taken date retrieve from the userSubscription object
      plan_validity_days =  userSubscriptions.subscription_plan.plan_validity
      plan_date_difference = (today_date - plan_date).days # Here calculate the diffrence to get it as no of days 'days' attribute used
   
   # In here check is there is any active plan if active plan then it return True.
      if 0 <= plan_date_difference < plan_validity_days:
         return True

#Movie Individual view
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def movie_view(request,movieId):
   user = request.user

   is_have_active_subscribtion = check_user_subscription_valid_or_not(user)

   if is_have_active_subscribtion:
      view_movie = get_object_or_404(MovieList,pk=movieId)
      serializer = MovieListSerializer(view_movie)
      print(serializer.data)
      return Response({'data':serializer.data},status= HTTP_200_OK) #ok
   return Response({'error':"You currently don't have an active plan."},status= HTTP_401_UNAUTHORIZED) #ok

''' The below function Update rating of each movie in movie list table'''

def update_movie_rating():

   Ratings = MovieRating.objects.values_list('movie',flat=True).distinct() 
   print(Ratings)
   
   for movieId in Ratings:
      print(movieId)
      #Avg of each movie taken
      avg_rating = MovieRating.objects.filter(movie = movieId).aggregate(avg = Avg('movie_rating')).get('avg')

      if avg_rating is not None:
         #Here updated
         MovieList.objects.filter(pk = movieId ).update(movie_rating = avg_rating )

   return Response({'message':'Movie rating updated successfully.'},status=HTTP_200_OK)


#User individual Movie rating

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def user_movie_rating(request): #Individul user ratings

   user = request.user #user instance
   serializer = MovieRatingSerializer(data = request.data) 

   if serializer.is_valid():
      movie_id = serializer.validated_data.get('movie') #Movie instance got not movie id
      print('rate',movie_id)
      #If user rate again update the user rating
      if MovieRating.objects.filter(user = user, movie = movie_id).exists():
         user_update_rating = MovieRating.objects.filter(user = user, movie = movie_id).first()
         user_update_rating.movie_rating = request.data.get('movie_rating')
         user_update_rating.save()
         update_movie_rating() #update function called here
         return Response({'message':"Rating updated successfully."},status=HTTP_200_OK)
      serializer.save(user=user) #here pass the user instance not user id
      
      update_movie_rating() #update function called here

      return Response({'message':'Movie rated successfully.'},status=HTTP_200_OK)
   print(serializer.errors)
   return Response({'error':serializer.errors},status=HTTP_400_BAD_REQUEST) #ok


#add to user watch list
@api_view(['POST'])
@permission_classes([IsAuthenticated])

def add_movie_to_watchlater(request):
   user = request.user #user instance

   serializer = WatchListSerializer(data=request.data)

   if serializer.is_valid():
      movie_id = serializer.validated_data.get('movie') #movie instance
      print(movie_id)

      if WatchList.objects.filter(user = user, movie = movie_id).exists():
         return Response({'error':'This movie is already in your watchlist.'},status=HTTP_400_BAD_REQUEST)
      serializer.save(user=user)
      return Response({'message':'Movie added to your watchlist!'},status=HTTP_200_OK)
   return Response({'error':serializer.errors},status=HTTP_400_BAD_REQUEST)
   
#get user watch list

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_watchlater_movies(request):
   watchlist = WatchList.objects.filter(user=request.user).order_by('-added_at')#retrieving the movies corresponding to idList and sorted it using date.
   print([movie.movie for movie in watchlist])

   watch_list_movies = [movie.movie for movie in watchlist] # Here watchlist is an query object to access the movie data from movieList table used list comprehension // *Foreign Key* //
   
   movieSerializer = MovieListSerializer(watch_list_movies,many=True)
   return Response({'data':movieSerializer.data})

#remove movie from user Watch list

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])

def delete_watchlater_movies(request,movieId):
   user = request.user
   try:
      watchlist_movies = WatchList.objects.filter(user = user, movie = movieId)
   except WatchList.DoesNotExist :
      return Response({'error':'movie not found'},status=HTTP_404_NOT_FOUND)

   print(watchlist_movies)
   watchlist_movies.delete()
   return Response({'message':'The movie has been successfully removed from your watch list.'})

#add movie to user Watch history

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def add_movies_to_watch_history(request):
   user = request.user

   if MovieList.objects.filter(pk = request.data.get('movie')).exists():
      serializer = WatchHistorySerializer(data = request.data)

      if serializer.is_valid():
         serializer.save(user = user)
         return Response({'message':'Movie added to watch history successfully.'},status=HTTP_201_CREATED)
   
      return Response({'error':serializer.errors},status=HTTP_400_BAD_REQUEST)
   return Response({'error':'Movie not Found.'},status=HTTP_404_NOT_FOUND)
   

#Get movies from Watch history

@api_view(['GET'])
@permission_classes((AllowAny,))

def get_watch_history_movies(request):
   user = request.user
   watch_history = WatchHistory.objects.filter(user = user).order_by('-added_at')
   serializer = WatchHistorySerializer(watch_history,many = True) #list of dict is returned

   watchId = [id.get('movie') for id in serializer.data] #List Comprehension ,list of id created 

   distinct_watchId = [] # This List contains distinct movie Id only
   
   for Id in watchId: #Loop used to get the distinct id
      if Id not in distinct_watchId:
         distinct_watchId.append(Id) 

   print(distinct_watchId)
   watch_history_moviesobj = [] #Contains the list of movieObjects

   for id in distinct_watchId:
         watch_history_moviesobj.append(MovieList.objects.get(pk = id))
   
   # Here the List Comprehension used to to get the movie added date from watchHistory table
   watch_history_added_date_obj = []

   for id in distinct_watchId:
      watch_history_added_date_obj.append(WatchHistory.objects.filter(user = user ,movie = id).order_by('-added_at').first())

   added_date_serializer = WatchHistorySerializer(watch_history_added_date_obj,many=True)

   if len(watch_history_moviesobj) != 0:
      print(watch_history_moviesobj)
      watch_history_serializer = MovieListSerializer(watch_history_moviesobj,many=True)
      return Response({'data':watch_history_serializer.data, 'watch_history_date':added_date_serializer.data})
   return Response({'error':'There are no movies in the watch history.'})
   

#Get all subscription plans 

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_all_subscription_plans(request):

   try:
      plans = SubscriptionPlan.objects.filter(is_enabled = True)
   except SubscriptionPlan.DoesNotExist:
      return Response({'error':'No plans Found.'},status=HTTP_404_NOT_FOUND)
   
   planSerializer = SubscriptionPlanSerializer(plans,many=True)
   return Response({'data':planSerializer.data},status=HTTP_200_OK)


#subscription plans view(checkout) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def subscription_plan_view(request,subscriptionId):

   if not subscriptionId:
      return Response({'error':'Invalid plan.'},status=HTTP_404_NOT_FOUND)

   try:
      view_subscription_plan = SubscriptionPlan.objects.get(pk = subscriptionId)
   except SubscriptionPlan.DoesNotExist:
      return Response({'error':'No subscription plan Found'},status=HTTP_400_BAD_REQUEST)

   view_subscription_serializer = SubscriptionPlanSerializer(view_subscription_plan)
   return Response({'data':view_subscription_serializer.data},status=HTTP_200_OK)


#Allow the user to select subscription plan Function

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def subscribe_user_to_plan(request):
   request_user = request.user #user instance
   is_active = check_user_subscription_valid_or_not(request_user)

   if is_active:
      return Response({'error':'You already have an active plan.'},status=HTTP_409_CONFLICT)

   serializer = UserSubscriptionSerializer(data= request.data)
   if serializer.is_valid():
      serializer.save(user = request_user)
      return Response({'message':'You have successfully purchased the subscription plan.'},status=HTTP_200_OK)
   

#User Current subscription status/user current subscription plan 

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def user_current_subscription(request):
   user = request.user
   is_active = check_user_subscription_valid_or_not(user)

   if is_active :
      userSubscriptions = UserSubscriptions.objects.filter(user = user).order_by('-id')
      valid_Usersubscription_obj = userSubscriptions.first()
      current_subscriptionPlan_serializer = SubscriptionPlanSerializer(valid_Usersubscription_obj.subscription_plan)
      current_Usersubscription_date_serializer = UserSubscriptionSerializer(valid_Usersubscription_obj)
      print(current_Usersubscription_date_serializer)
      #In here changed passing data from dict to list beacause in react looping is got performed so passing it as list.
      return Response({'data':[current_subscriptionPlan_serializer.data],'date_of_taken':[current_Usersubscription_date_serializer.data]},status=HTTP_200_OK)
   else:
      return Response({'error':'No Active Plans Found.'},status=HTTP_400_BAD_REQUEST)


#User Previous subscription status/user Previous subscription plans

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def user_previous_subscriptions_list(request):
   user = request.user
   userSubscriptions = UserSubscriptions.objects.filter(user = user).order_by('-id')#Here sorted the user taken plan desending order by table id
   
   is_active = check_user_subscription_valid_or_not(user)

   if not userSubscriptions.exists():
      return Response({'error':'No previous plans found.'},status=HTTP_400_BAD_REQUEST)

   #This condtion given because if the userSubscriptions queryset length is 1 
   #then the offset set to 0 else set to 1 if it is not given,
   #then user only taken 1 plan and if it expired then not shown in payment history of react.
   
   if len(userSubscriptions) == 1:
      # If user have only and if it is active then not show it on previous plan else set userSubscriptions[0:]s
      if is_active:
         return Response({'error':'No previous plans found.'},status=HTTP_400_BAD_REQUEST)
      else:
         userSubscriptions = userSubscriptions[0:]
   else:
      userSubscriptions = userSubscriptions[1:]

   serializer = UserSubscriptionSerializer(userSubscriptions,many=True)

   planId = [id.get('subscription_plan') for id in serializer.data ] #List Comprehension

   print(planId)

   Prev_subscriptions = SubscriptionPlan.objects.filter(pk__in=planId)

   if not Prev_subscriptions.exists():
      return Response({'error':'No previous plans found.'},status=HTTP_400_BAD_REQUEST)

   subscriptionSerializer = SubscriptionPlanSerializer(Prev_subscriptions,many=True)
   print(subscriptionSerializer.data)
   #In here changed passing data from dict to list beacause in react looping is got performed so passing it as list.
   return Response({'data':subscriptionSerializer.data,'date_of_taken':serializer.data},status=HTTP_200_OK)

#Logout

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def user_logout(request):
   user = request.user
   if user:
      user.auth_token.delete()
      return Response({'message':'You have been logged out successfully'})
   return Response({'error':'You are not logged in. Please log in.'})