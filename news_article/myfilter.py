import django_filters
from .models import Article
from rest_framework import filters
from .models import User


# 自定义搜索过滤器
class ArticleFilter(django_filters.rest_framework.FilterSet):
    # 注释掉也是可以的，只要Article model中有对应字段
    # author = django_filters.CharFilter(help_text="作者")
    # status = django_filters.CharFilter(help_text="状态")  # 从ChoiceFilter改成了CharFilter
    # publish_date = django_filters.DateTimeFilter(help_text="发布时间")
    # item = django_filters.CharFilter(help_text="分类")
    # tags = django_filters.CharFilter(help_text="标签")
    # is_active = django_filters.CharFilter(help_text="是否热门")
    # model中没有的字段，可以这么定义使用
    categorys = django_filters.NumberFilter(method='item_categorys_filter', help_text="大类")

    # 这里4个入参是必须的（根据外键item去查询大类：item__categorys）
    def item_categorys_filter(self, queryset, name, value):
        return queryset.filter(item__categorys=value)

    class Meta:
        model = Article
        fields = ['author', 'status', 'publish_date', 'is_active', 'item', 'categorys', 'tags']


# 限制非超级用户只能访问自己的数据
class UserFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        users = User.objects.filter(id=request.user.id)
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
