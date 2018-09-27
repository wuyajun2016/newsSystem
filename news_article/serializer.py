from rest_framework import serializers
from .models import Category, Item, Tag, Article, Ad, UserFav
from django.contrib.auth.models import User, Group
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from rest_framework.compat import authenticate

# serializer作用：
# - 将queryset与model实例等进行序列化，转化成json格式，返回给用户(api接口)。
# - 将post与patch/put的上来的数据进行验证。
# - 对post与patch/put数据进行处理。
# - 简单来说，针对get来说，serializers的作用体现在第一条，但如果是其他请求，serializers能够发挥2,3条的作用！
# 用户(这个模型是django自带的)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # 让password不要输出

    class Meta:
        model = User
        fields = "__all__"


# 还不知道干嘛用的，在views中没有看到引用。先注释
# class GroupSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Group
#         fields = ('url', 'name')

# 分类序列化
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


# 分类下面的小类1
# 1）自定义方法，增加新字段
# 2）这里还用了一种新的调用方式：直接在序列化类里面调用其他序列化类，然后最终返回序列化后的数据
class CategoryItemsSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"

    def get_items(self, obj):
        items = Item.objects.filter(categorys=obj.id)  # 根据category id取出对应items，当作新的字段加入
        if items:
            items_serializer = ItemnocateSerializer(items, many=True, context={'request': self.context['request']})
            return items_serializer.data


class ItemnocateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = "__all__"


# StringRelatedField(大类中寻找小类，根据models中小类外键中定义的related_name取出对应小类,只展示小类的title(即model中__str__定义的字段))
class CategoryStringSerializer(serializers.ModelSerializer):
    items = serializers.StringRelatedField(many=True)

    class Meta:
        model = Category
        fields = "__all__"


# PrimaryKeyRelatedField
# read_only：True表示不允许用户自己上传，只能用于api的输出。如果某个字段设置了read_only=True，
#            那么就不需要进行数据验证，只会在返回时，将这个字段序列化后返回
class CategoryPrimaryKeySerializer(serializers.ModelSerializer):
    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = "__all__"


# SlugRelatedField(slug_field='title',这里的这个值貌似只要是item表中存在的都可以，官方文档中是要求能代表唯一性的字段)
class CategorySlugSerializer(serializers.ModelSerializer):
    items = serializers.SlugRelatedField(many=True, read_only=True, slug_field='title')

    class Meta:
        model = Category
        fields = "__all__"


# 分类下面的小类2
# 内嵌（需要存在外键关系）：
#   1)将"categorys": 3 显示成
#    "categorys": {
#       "id": 3,
#       "title": "娱乐版图"
#     }
#   2) categorys = CategorySerializer()，这个categorys一定要和model定义中的一致，不然会报错
class ItemSerializer(serializers.ModelSerializer):
    categorys = CategorySerializer()

    class Meta:
        model = Item
        # 也可以只定义model中的部分字段，这样的话入参就是fields中定义的字段（必填字段必须定义；我们mixin方法中需要涉及存储的需定义下）
        # fields = ('title', 'categorys')
        fields = "__all__"


# 标签
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


# 文章
class ArticleSerializer(serializers.ModelSerializer):
    item = ItemSerializer()
    tags = TagSerializer(many=True)  # 多对多的关系，需要加上many=True，不然请求时候会报错
    author = UserSerializer()

    class Meta:
        model = Article
        fields = "__all__"


# 广告
class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = "__all__"


# 用户详情序列化
class UserDetailSerializer(serializers.ModelSerializer):
    # token = serializers.CharField(required=False, max_length=1024,write_only=True)
    password = serializers.CharField(write_only=True)  # 控制password不要输出给用户

    class Meta:
        model = User
        fields = "__all__"


# 用户注册(验证方式1：UniqueValidator)
class UserRegisterSerializer(serializers.ModelSerializer):
    # 以下得username、password都是入参,同时也是出参
    # 如果fields不指定，应当是默认model中的全部参数(user model中入参必填的参数都必须传过来)
    # 定义的username、password等值都是model中带有的字段
    username = serializers.CharField(label="用户名", help_text="用户名", required=True, allow_blank=False,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message="用户已经存在")])
    password = serializers.CharField(style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True)
    # token = serializers.CharField(required=False, max_length=1024)  # 注册时应当不需要token，这个字典model中没有，验证通不过的

    class Meta:
        model = User
        fields = ('username', 'password')


# 用户登录(验证方式2：重写validate)
class UserLoginSerializer(serializers.ModelSerializer):
    # username、password都是入参（token被标记了read_only因此不需要入参），出参username、password、token(如果view中没有值传入出参就不展示该字段了)
    username = serializers.CharField(required=True, max_length=100)
    password = serializers.CharField(required=True, max_length=100, write_only=True)  # 不用在接口中返回给用户，所以设置了write_only=True
    token = serializers.CharField(required=False, max_length=1024, read_only=True)  # 只应该包含在输出中，任何输入字段（创建和更新）中包含该属性都会被忽略

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if not user:
                raise serializers.ValidationError('不能登录', code='authorization')
        else:
            raise serializers.ValidationError('必须输入同时输入名称和密码', code='authorization')
        attrs['user'] = user
        return attrs

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'token')


# 用户设置密码
class UserSetPasswordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label="用户名", help_text="用户名", required=True, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True)
    newpassword = serializers.CharField(style={'input_type': 'password'}, help_text="新密码", label="新密码", write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if not user:
                raise serializers.ValidationError('不能修改', code='authorization')
        else:
            raise serializers.ValidationError('必须同时输入用户名和密码', code='authorization')

        attrs['user'] = user
        return attrs

    class Meta:
        model = User
        fields = ('username', 'password', 'newpassword')


# 用户收藏(验证方式3：UniqueTogetherValidator)
# 这里还有一个知识点：CurrentUserDefault，这个不需要用户(前端)上传
class UserFavSerializer(serializers.ModelSerializer):
    # 有时候前端不需要传一个或多个字段，这些字段值是直接根据用户登录信息判断自动赋值的
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserFav
        validators = [
            UniqueTogetherValidator(
                queryset=UserFav.objects.all(),  # 用于明确验证唯一性集合，必须设置
                fields=('articles', 'user'),  # 列表或元组（哪些需要做唯一性校验的字段），字段必须是序列化类中存在的字段
                message="已经收藏"
            )
        ]
        # fields = "__all__"
        fields = ('user', 'articles', 'id')


