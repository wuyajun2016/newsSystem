"""news_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import include, url
from rest_framework_swagger.views import get_swagger_view
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.authtoken import views

schema_view = get_swagger_view(title="news api")
urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('^docs/$', schema_view),  # swagger路由:ip/docs
    url(r'', include('news_article.urls')),  # 让diango能够找到应用的url
    url(r'^api-auth/', include('rest_framework.urls')),  # api权限认证，增加登录的功能
    # url(r'^api-token-auth/', obtain_jwt_token),  # jwt（settings配置后token可带过期时间,token不是存在数据库的）
    url(r'^api-token-auth/', views.obtain_auth_token),  # token(这个不带过期时间，且token需要存数据库，比较起来jwt好使)
]
