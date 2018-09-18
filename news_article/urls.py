from django.conf.urls import url, include
from . import views
from rest_framework.routers import DefaultRouter


# ViewSet使用了以下这种方式去定义路由
# 说明：
# 1）register(prefix, viewset, base_name)  -prefix 该视图集的路由前缀 -viewset 视图集 -base_name 路由名称的前缀(生成url时要取这个值，如没有会出错)
# 2）如果views中包含action的话，那就会生成类似的链接^snippets/action的方法名/$
router = DefaultRouter()
router.register(r'category', views.CategoryViewSet, base_name="category")
router.register(r'item', views.ItemViewSet, base_name="item")
router.register(r'tag', views.TagViewSet, base_name="tag")
router.register(r'article', views.ArticleViewSet, base_name="article")
router.register(r'user', views.UserViewSet, base_name="user")
router.register(r'ad', views.AdViewSet, base_name="ad")
router.register(r'userFav', views.UserFavViewSet, base_name="userFav")
router.register(r'categoryitems', views.CategoryItemsViewSet, base_name="categoryitems")
router.register(r'categoryStringitems', views.CategoryStringItemsViewSet, base_name="categoryStringitems")
router.register(r'categoryPrimaryKeyitems', views.CategoryPrimaryKeyViewSet, base_name="categoryPrimaryKeyitems")
router.register(r'categorySlugitems', views.CategorySlugViewSet, base_name="categorySlugitems")
router.register(r'userLogin', views.UserLoginViewSet, base_name="userLogin")
router.register(r'setPassword', views.UserSetPasswordViewSet, base_name="setPassword")
urlpatterns = [
    url(r'^', include(router.urls))
]
