from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response    
from rest_framework.views import APIView
from ebay.serializers import UserSerializer, UserSerializerWithToken
from ebay.models import FavoriteList
from django.contrib.auth.models import User
import os
import logging
from rest_framework import status
from google.oauth2 import id_token
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests

logger = logging.getLogger(__name__)

def _google_token_audiences(aud):
    if isinstance(aud, str):
        return {aud}
    if isinstance(aud, (list, tuple)):
        return {item for item in aud if isinstance(item, str)}
    return set()

def _verify_google_id_token(credential, client_id):
    request = google_requests.Request()
    try:
        return id_token.verify_oauth2_token(
            credential,
            request,
            audience=client_id,
            clock_skew_in_seconds=60,
        )
    except ValueError as exc:
        if 'wrong audience' not in str(exc).lower():
            raise
        idinfo = id_token.verify_oauth2_token(
            credential,
            request,
            clock_skew_in_seconds=60,
        )
        if client_id not in _google_token_audiences(idinfo.get('aud')):
            raise
        return idinfo

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

        user.save()

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)
    
class GetUsers(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class GoogleLogin(APIView):

    def get(self, request):
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            return Response({'detail': 'Google login is not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'client_id': client_id})

    def post(self, request):
        credential = request.data.get('credential')
        client_id = (os.environ.get("GOOGLE_CLIENT_ID") or '').strip().strip('"').strip("'")
        if not client_id:
            return Response({'detail': 'Google login is not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not credential or not isinstance(credential, str):
            return Response({'detail': 'Missing Google credential'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = _verify_google_id_token(credential.strip(), client_id)
        except (ValueError, google_exceptions.GoogleAuthError) as exc:
            logger.warning('Google token verification failed: %s', exc)
            return Response({'detail': f'Invalid Google token: {exc}'}, status=status.HTTP_400_BAD_REQUEST)

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
