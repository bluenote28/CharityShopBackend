from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response    
from rest_framework.views import APIView
from ebay.serializers import UserSerializer, UserSerializerWithToken
from django.contrib.auth.models import User
from django.db import IntegrityError
import smtplib
from rest_framework import status
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

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
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError:
            message = {'detail': 'User already exists'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            message = {'detail': e}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
    
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