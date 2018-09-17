from rest_framework import viewsets
from .models import Category, Item, Tag, Article, Ad, UserFav, User
from .serializer import CategorySerializer, ItemSerializer, TagSerializer, ArticleSerializer, \
    UserSerializer, AdSerializer, UserFavSerializer, CategoryItemsSerializer, CategoryStringSerializer, \
    CategoryPrimaryKeySerializer, CategorySlugSerializer, UserLoginSerializer, UserDetailSerializer, UserRegisterSerializer, UserSetPasswordSerializer
from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.response import Response


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "id"


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    lookup_field = "id"


class CategoryItemsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryItemsSerializer
    lookup_field = "id"


# StringRelatedField
class CategoryStringItemsViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryStringSerializer
    lookup_field = "id"


# PrimaryKeyRelatedField
class CategoryPrimaryKeyViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryPrimaryKeySerializer
    lookup_field = "id"


# SlugRelatedField
class CategorySlugViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySlugSerializer
    lookup_field = "id"


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "id"


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = "id"


# 用户注册、查询
class UserViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.all()
    # serializer_class = UserSerializer
    # serializer_class = UserDetailSerializer  # UserDetailSerializer貌似和UserSerializer返回一样，都是没有token
    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "create":
            return UserRegisterSerializer

        return UserDetailSerializer
    # 认证策略属性
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        users = User.objects.filter(id=self.request.user.id)
        if users:
            for user in users:
                issuperuser = user.is_superuser
            if issuperuser:
                queryset = User.objects.all()
            else:
                queryset = users
        else:
            queryset = users
        return queryset

    permission_classes = (permissions.IsAuthenticated,)

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.IsAuthenticated()]
        elif self.action == "create":
            return []

        return []

    # 重写create方法,给密码加密，并查询和创建token
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        passwd = request.data['password']
        user = self.perform_create(serializer)
        # 给密码加密
        user.set_password(passwd)
        user.save()
        re_dict = serializer.data
        # 查询和创建token
        token = Token.objects.get_or_create(user=user)

        serializer = UserRegisterSerializer({'id': user.id, 'username': user.username, 'token': token[0]})
        serializer.data["status"] = HTTP_201_CREATED
        # headers = self.get_success_headers(serializer.data)
        return Response(serializer.data)

    def perform_create(self, serializer):
        return serializer.save()


# 用户登录
class UserLoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            # 登录时，创建新的token
            tokenobj = Token.objects.update_or_create(user=user)
            token = Token.objects.get(user=user)
            # 重构返回数据
            serializer = UserLoginSerializer(
                {'username': user.username, 'id': user.id, 'password': '', 'token': token.key})
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def get_object(self):
        return self.request.user


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer


# 用户修改密码
class UserSetPasswordViewSet(mixins.CreateModelMixin,viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSetPasswordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.validated_data['user']
            instance.set_password(request.data['newpassword'])
            instance.save()
            return Response({'status': '密码修改成功'})
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class UserFavViewSet(viewsets.ModelViewSet):
    queryset = UserFav.objects.all()
    serializer_class = UserFavSerializer
