from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

# 1. Category model
# seperate categories
class Category(models.Model):
    name = models.CharField(max_length=64, unique=True) # categories name ex: "Fashion", "Electronics"

    class Meta:
        verbose_name_plural = "Categories" # 在 Django Admin 中顯示的名稱，避免複數名稱自動加 s

    def __str__(self):
        return self.name

# 2. Listing model
# to save the information of all the categories.
class Listing(models.Model):
    title = models.CharField(max_length=128) # 拍賣物品標題
    description = models.TextField() # 物品描述
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2) # 起始出價金額
    image_url = models.URLField(blank=True, null=True) # 物品圖片的 URL，可選填
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name="listings")
    # 外鍵關聯到 Category 模型。
    # on_delete=models.SET_NULL: 當 Category 被刪除時，相關的 Listing 的 category 欄位會被設為 NULL。
    # blank=True, null=True: 表示 category 欄位是可選填的。
    # related_name="listings": 允許我們從 Category 物件反向查詢所有相關的 Listing。

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings_owned")
    # 外鍵關聯到 User 模型，表示誰創建了這個拍賣清單。
    # on_delete=models.CASCADE: 當 User 被刪除時，他創建的所有 Listing 也會被刪除。
    # related_name="listings_owned": 允許我們從 User 物件反向查詢他擁有的所有 Listing。

    is_active = models.BooleanField(default=True) # 拍賣是否活躍 (進行中)。預設為 True。
    created_at = models.DateTimeField(auto_now_add=True) # 拍賣創建時間，自動設定為當前時間。

    # Watchlist (觀察清單)
    # 這是多對多關聯，表示一個拍賣清單可以被多個使用者添加到觀察清單，一個使用者也可以有多個觀察清單中的拍賣清單。
    watchlist = models.ManyToManyField(User, blank=True, related_name="watchlist_items")

    def __str__(self):
        return f"{self.title} (ID: {self.id})"

# 3. Bid (出價) 模型
# 用途：儲存使用者對拍賣物品的出價記錄。
class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    # 外鍵關聯到 Listing 模型，表示這個出價是針對哪個拍賣物品。
    # on_delete=models.CASCADE: 當 Listing 被刪除時，相關的 Bid 也會被刪除。
    # related_name="bids": 允許我們從 Listing 物件反向查詢所有相關的 Bid。

    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids_made")
    # 外鍵關聯到 User 模型，表示誰出了這個價。
    # on_delete=models.CASCADE: 當 User 被刪除時，他出的所有 Bid 也會被刪除。
    # related_name="bids_made": 允許我們從 User 物件反向查詢他出的所有 Bid。

    amount = models.DecimalField(max_digits=10, decimal_places=2) # 出價金額
    timestamp = models.DateTimeField(auto_now_add=True) # 出價時間

    def __str__(self):
        return f"{self.bidder.username} bid {self.amount} on {self.listing.title}"

# 4. Comment (評論) 模型
# 用途：儲存使用者在拍賣物品頁面上的評論。
class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    # 外鍵關聯到 Listing 模型，表示這個評論是針對哪個拍賣物品。
    # on_delete=models.CASCADE: 當 Listing 被刪除時，相關的 Comment 也會被刪除。
    # related_name="comments": 允許我們從 Listing 物件反向查詢所有相關的 Comment。

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments_made")
    # 外鍵關聯到 User 模型，表示誰發表了這個評論。
    # on_delete=models.CASCADE: 當 User 被刪除時，他發表的 Comment 也會被刪除。
    # related_name="comments_made": 允許我們從 User 物件反向查詢他發表的所有 Comment。

    content = models.TextField() # 評論內容
    timestamp = models.DateTimeField(auto_now_add=True) # 評論時間

    def __str__(self):
        return f"Comment by {self.author.username} on {self.listing.title}"