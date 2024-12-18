from rest_framework import serializers
from .models import Post, Image


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class DisplayPostSerializer(serializers.ModelSerializer):
    authors = serializers.SlugRelatedField('full_name', many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'subtitle', 'date', 'time', 'content', 'authors', 'file', 'images']
