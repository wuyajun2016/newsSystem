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
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .mypage import ArticlePagination
from .myfilter import ArticleFilter, UserFilter
from .permissions import IsOwnerOrReadOnly
import datetime
import json
from django.shortcuts import get_object_or_404 as _get_object_or_404


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()  # 模型查询API
    # queryset = Category.objects.raw('select id as id,title as title from news_article_category')  # 使用raw
    serializer_class = CategorySerializer
    # authentication_classes = (TokenAuthentication, SessionAuthentication)  # settings中配置了全局的，这个就不需要配置了
    # permission_classes = (IsOwnerOrReadOnly,)  # 加上这句后，就不会去读取settings中的配置，使用这里的配置
    lookup_field = "id"


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    # 排序(这里ordering_fields指定可通过那些字段对结果进行排序)---跟model中的ordering区别？
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('-id',)  # 如果是降序前面加个‘-’
    # 搜索(可根据search_fields里面的配置字段进行查询)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('title', 'categorys__title',)
    # 过滤（可根据title、外键title分别进行查询，精确查询）
    # filter_backends = (DjangoFilterBackend,)
    # filter_fields = ('title', 'categorys__title')

    serializer_class = ItemSerializer
    # get等方法时候使用id去查询（默认就id，所以下面这句可以不写）
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
    # 分页
    pagination_class = ArticlePagination
    # 自定义查询 ArticleFilter
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 首先filter_backends中配上DjangoFilterBackend
    filter_class = ArticleFilter
    # 首先filter_backends中配上filters.SearchFilter，另外查询外键关联的字段，使用item__title这样的方式
    search_fields = ('title', 'item__title', 'tags__name')
    # 首先filter_backends中配上filters.OrderingFilter
    ordering_fields = ('id', 'publish_date')

    lookup_field = "id"

    # 重写下，浏览数+1
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # 获取article这个对象
        instance.read_num += 1  # 将article中的read_num字段值加1
        instance.save()
        serializer = self.get_serializer(instance)  # 找到article的序列化类进行序列化
        return Response(serializer.data)


# 热门文章
class HotArticleListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Article.objects.filter(is_active=True)[:10]
    serializer_class = ArticleSerializer
    ordering_fields = ('-id',)
    lookup_field = "id"


# 用户注册、查询
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    # 重写返回的序列化类
    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "create":
            return UserRegisterSerializer

        return UserDetailSerializer
    # authentication_classes = (TokenAuthentication, SessionAuthentication)
    # 要走到这一句，那么后面的get_permissions方法不能存在，不然会使用get_permissions方法（这句和后面get_permissions都不写就走全局）
    # 另外，如果要控制某个post/get等请求的权限，就使用自定义的permissions或则重写下get_permissions方法
    # permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)

    filter_backends = (UserFilter,)

    # 使用filter_backends = (UserFilter,)跟下面的方式是一样的
    # def get_queryset(self):
    #     users = User.objects.filter(id=self.request.user.id)
    #     if users:
    #         for user in users:
    #             issuperuser = user.is_superuser
    #         if issuperuser:
    #             queryset = User.objects.all()
    #         else:
    #             queryset = users
    #     else:
    #         queryset = users
    #     return queryset

    # 重写认证(这样就会使得全局的认证失效，读取这里的认证了)
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
        # re_dict = serializer.data
        # 查询和创建token
        token = Token.objects.get_or_create(user=user)

        # 试了下，这里的反序列化可以不需要，返回这样的也没用，因为UserRegisterSerializer中fields不带id和token
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
            token, created = Token.objects.update_or_create(user=user)
            time_now = datetime.datetime.now()
            if created or token.created < time_now - datetime.timedelta(minutes=1):
                token.delete()
                token = Token.objects.create(user=serializer.validated_data['user'])
                token.created = time_now
                token.save()
            token = Token.objects.get(user=user)
            # 重构返回数据1
            serializer = UserLoginSerializer(
                {'username': user.username, 'id': user.id, 'token': token.key})
            return Response(serializer.data, status=HTTP_200_OK)
        # 也可以不用重构返回数据，直接返回一个json就可以了2
        # return Response({'id': user.id, 'username': user.username, 'token': token.key}, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # 这个目前没有，这里只是post，没有用到查询（不知道原来添加这个是何意）
    # def get_object(self):
    #     return self.request.user


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer


# 用户修改密码
class UserSetPasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
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


class UserFavViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin, viewsets.GenericViewSet):
    # queryset = UserFav.objects.all()
    serializer_class = UserFavSerializer

    # 重写get_queryset（ListModelMixin是直接将这个queryset序列化然后返回，不会像RetrieveModelMixin一样执行get_object方法：先根据主键去查询出记录）
    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            queryset = UserFav.objects.filter(user=self.request.user)
        else:
            queryset = []
        return queryset
    lookup_field = 'articles_id'
    # 如果用RetrieveModelMixin，那么需要重写下获取对象方法，’将默认的根据pk去查询‘改成‘根据用户id去查询’
    # 当然最简单的方法是定义：lookup_field = 'articles_id'
    # def get_object(self):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     filter_kwargs = {"user_id": self.request.user.id}
    #     obj = _get_object_or_404(queryset, **filter_kwargs)
    #     return obj

    # 重写create
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        articleid = request.data['articles']
        userid = self.request.user.id
        userfav = UserFav.objects.get_or_create(articles_id=articleid, user_id=userid)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
