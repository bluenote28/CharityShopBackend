from rest_framework import serializers
from .models import Charity, Item, FavoriteList
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class CharitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Charity
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class FavoriteListSerializer(serializers.ModelSerializer):

    items = ItemSerializer(many=True, read_only=True)
    charities = CharitySerializer(many=True, read_only=True)

    class Meta:
        model = FavoriteList
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField(read_only=True)
    id = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'isAdmin', 'first_name', 'last_name', 'username', 'name']

    def get_id(self, obj):
        return obj.id
    
    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_name(self, obj):
        return obj.first_name + ' ' + obj.last_name
    
    def get_email(self, obj):
        return obj.email   
        
    def get_username(self, obj):
        return obj.username
    
class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'isAdmin', 'token', 'refresh', 'first_name', 'last_name', 'username', 'name']

    def get_token(self, obj):
        jwt_token = RefreshToken.for_user(obj)
        return str(jwt_token.access_token)

    def get_refresh(self, obj):
        jwt_token = RefreshToken.for_user(obj)
        return str(jwt_token)