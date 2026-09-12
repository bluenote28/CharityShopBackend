from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response    
from rest_framework.views import APIView
from ebay.serializers import UserSerializer, UserSerializerWithToken
from ebay.models import FavoriteList
from django.contrib.auth.models import User
from ebay.serializers import FavoriteListSerializer
from django.db import IntegrityError
import smtplib
import os
from rest_framework import status
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

class GetUserProfile(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
    
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        data = request.data

        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.username = data['email']
        user.email = data['email']

        if data['password'] != '':
            user.password = make_password(data['password'])

        user.save()

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)   

class UpdateUserProfile(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        user = request.user
        data = request.data

        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.username = data['email']
        user.email = data['email']

        if data['password'] != '':
            user.password = make_password(data['password'])

        user.save()

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)
    
class GetUsers(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class RegisterUser(APIView):
    
    def createFavoriteList(self, user_id):
        favorite_list = FavoriteList.objects.create(user_id=user_id)
        favorite_list.items.clear()
        favorite_list.charities.clear()
        favorite_list.save()
    
    def post(self, request):
        
        try: 
            user = User.objects.create_user(
                username=request.data['email'],
                email=request.data['email'],
                password=request.data['password'],
                first_name=request.data['first_name'],
                last_name=request.data['last_name']
            )
        except smtplib.SMTPAuthenticationError:
            message = {'detail': 'Account Created. Redirect Failed. Please login from the login screen'}
            created_user = User.objects.filter(email=request.data.get('email')).first()
            if created_user:
                self.createFavoriteList(created_user.id)
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError:
            message = {'detail': 'User already exists'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            message = {'detail': e}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
              
        self.createFavoriteList(user.id)

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        serializer = UserSerializerWithToken(self.user).data

        for k, v in serializer.items():
            data[k] = v
      
        return data
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class GoogleLogin(APIView):

    def get(self, request):
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            return Response({'detail': 'Google login is not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'client_id': client_id})

    def post(self, request):
        credential = request.data.get('credential')
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            return Response({'detail': 'Google login is not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not credential:
            return Response({'detail': 'Missing Google credential'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id,
            )
        except ValueError:
            return Response({'detail': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        if not idinfo.get('email_verified'):
            return Response({'detail': 'Google email is not verified'}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get('email')
        if not email:
            return Response({'detail': 'Google account has no email'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first() or User.objects.filter(username=email).first()
        if user is None:
            user = User(username=email, email=email)
            user.set_unusable_password()
            user.first_name = idinfo.get('given_name') or ''
            user.last_name = idinfo.get('family_name') or ''
            user.save()
            FavoriteList.objects.get_or_create(user_id=user.id)
        else:
            updated = False
            if not user.first_name and idinfo.get('given_name'):
                user.first_name = idinfo.get('given_name')
                updated = True
            if not user.last_name and idinfo.get('family_name'):
                user.last_name = idinfo.get('family_name')
                updated = True
            if updated:
                user.save()

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)