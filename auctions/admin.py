from django.contrib import admin
from .models import Listing, Bid, Comment, Category, User # 導入您新定義的模型

# Register your models here.
admin.site.register(Listing)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Category)
# 如果您想在 Admin 中管理 User 模型，也可以註冊：
# admin.site.register(User)
