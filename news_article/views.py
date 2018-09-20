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
from .myfilter import ArticleFilter
from .permissions import IsOwnerOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # authentication_classes = (TokenAuthentication, SessionAuthentication)  # settings中配置了全局的，这个就不需要配置了
    permission_classes = (IsOwnerOrReadOnly,)  # 加上这句后，就不会去读取settings中的配置，使用这里的配置
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
    pagination_class = ArticlePagination
    # 自定义查询 ArticleFilter
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = ArticleFilter
    search_fields = ('title', 'item__title', 'tags__name')
    ordering_fields = ('id', 'publish_date')

    lookup_field = "id"

    # 重写下，浏览数+1
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # 获取article这个对象
        instance.read_num += 1  # 将article中的read_num字段值加1
        instance.save()
        serializer = self.get_serializer(instance)  # 找到article的序列化类进行序列化
        return Response(serializer.data)


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
    # authentication_classes = (TokenAuthentication, SessionAuthentication)
    # 要走到这一句，那么后面的get_permissions方法不能存在，不然会使用get_permissions方法（这句和后面get_permissions都不写就走全局）
    # permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)

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

    # 重写认证
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
                {'username': user.username, 'id': user.id, 'token': token.key})
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # 这个目前没有，这里只是post，没有用到查询
    def get_object(self):
        return self.request.user


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


class UserFavViewSet(viewsets.ModelViewSet):
    queryset = UserFav.objects.all()
    serializer_class = UserFavSerializer
