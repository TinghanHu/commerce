from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import CreateListingForm
from django.contrib.auth.decorators import login_required
from .models import Listing, Bid, Comment, User, Category


def index(request):
    active_listings = Listing.objects.filter(is_active=True).order_by('-created_at')
    return render(request, "auctions/index.html", {
        "listings": active_listings })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    
@login_required # 確保只有登入的使用者才能訪問此視圖
def create_listing(request):
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            # 從表單獲取數據，但暫時不保存到資料庫
            listing = form.save(commit=False)
            # 設置拍賣物品的擁有者為當前登入的使用者
            listing.owner = request.user
            # 保存到資料庫
            listing.save()
            return redirect("index") # 創建成功後重定向到首頁 (活躍拍賣清單頁面)
    else:
        # 如果是 GET 請求，則創建一個空表單實例
        form = CreateListingForm()
    return render(request, "auctions/create_listing.html", {
        "form": form
    })    

# 新增的視圖：單一拍賣清單頁面
def listing_page(request, listing_id):
    # 嘗試獲取指定 ID 的拍賣清單，如果不存在則返回 404 錯誤
    listing = get_object_or_404(Listing, pk=listing_id)

    # 獲取最高出價
    highest_bid = listing.bids.aggregate(Max('amount'))['amount__max']
    current_price = highest_bid if highest_bid else listing.starting_bid

    # 獲取所有評論，按時間排序
    comments = listing.comments.all().order_by('-timestamp')

    # 檢查拍賣是否在當前用戶的觀察清單中
    is_on_watchlist = False
    if request.user.is_authenticated:
        is_on_watchlist = request.user.watchlist_items.filter(id=listing_id).exists()

    # 檢查當前使用者是否是贏家 (如果拍賣已關閉)
    is_winner = False
    if not listing.is_active and request.user.is_authenticated:
        if highest_bid and listing.bids.filter(amount=highest_bid, bidder=request.user).exists():
            is_winner = True

    # 初始化表單
    bid_form = BidForm()
    comment_form = CommentForm()

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "current_price": current_price,
        "highest_bid": highest_bid, # 為了方便在模板中判斷是否有出價
        "comments": comments,
        "is_on_watchlist": is_on_watchlist,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "is_winner": is_winner,
    })

@login_required
def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    # 將當前使用者添加到拍賣清單的觀察清單多對多關係中
    request.user.watchlist_items.add(listing)
    return redirect("listing_page", listing_id=listing.id)

@login_required
def remove_from_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    # 將當前使用者從拍賣清單的觀察清單多對多關係中移除
    request.user.watchlist_items.remove(listing)
    return redirect("listing_page", listing_id=listing.id)

@login_required
def place_bid(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if not listing.is_active: # 只有活躍的拍賣才能出價
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "此拍賣已結束，無法出價。",
            "current_price": listing.bids.aggregate(Max('amount'))['amount__max'] or listing.starting_bid,
            "bid_form": BidForm(),
            "comment_form": CommentForm(),
        })

    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            new_bid_amount = form.cleaned_data["amount"]

            # 獲取當前最高出價 (如果有的話)
            highest_bid = listing.bids.aggregate(Max('amount'))['amount__max']
            current_price = highest_bid if highest_bid else listing.starting_bid

            # 檢查出價是否合法
            if new_bid_amount <= current_price:
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "message": "您的出價必須大於目前的價格。",
                    "current_price": current_price,
                    "bid_form": BidForm(), # 重新傳遞表單
                    "comment_form": CommentForm(),
                })
            else:
                # 創建新的出價
                bid = form.save(commit=False)
                bid.listing = listing
                bid.bidder = request.user
                bid.save()
                return redirect("listing_page", listing_id=listing.id)
        else:
            # 表單驗證失敗，通常是因為金額無效 (例如負數)
            current_price = listing.bids.aggregate(Max('amount'))['amount__max'] or listing.starting_bid
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "message": "無效的出價金額。",
                "current_price": current_price,
                "bid_form": form, # 傳回包含錯誤的表單
                "comment_form": CommentForm(),
            })
    return redirect("listing_page", listing_id=listing.id) # 如果是 GET 請求，只是重定向

@login_required
def add_comment(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.listing = listing
            comment.author = request.user
            comment.save()
            return redirect("listing_page", listing_id=listing.id)
    return redirect("listing_page", listing_id=listing.id) # 如果是 GET 請求或表單無效，只是重定向

@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    # 檢查是否是拍賣的擁有者
    if request.user != listing.owner:
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "您無權關閉此拍賣。",
            "current_price": listing.bids.aggregate(Max('amount'))['amount__max'] or listing.starting_bid,
            "bid_form": BidForm(),
            "comment_form": CommentForm(),
        })

    # 確保拍賣是活躍的才能關閉
    if not listing.is_active:
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "此拍賣已經關閉。",
            "current_price": listing.bids.aggregate(Max('amount'))['amount__max'] or listing.starting_bid,
            "bid_form": BidForm(),
            "comment_form": CommentForm(),
        })

    # 關閉拍賣
    listing.is_active = False
    listing.save()

    return redirect("listing_page", listing_id=listing.id) # 重定向回拍賣頁面以顯示更新後的狀態

@login_required # 只有登入的使用者才能訪問此頁面
def watchlist(request):
    # 獲取當前使用者觀察清單中的所有拍賣清單
    # 我們在 Listing 模型中定義了 related_name="watchlist_items"
    # 所以可以透過 request.user.watchlist_items 訪問
    user_watchlist_listings = request.user.watchlist_items.all()
    return render(request, "auctions/watchlist.html", {
        "listings": user_watchlist_listings
    })

def categories(request):
    # 獲取所有類別，按名稱排序
    all_categories = Category.objects.all().order_by('name')
    return render(request, "auctions/categories.html", {
        "categories": all_categories
    })

def category_listings(request, category_id):
    # 嘗試獲取指定 ID 的類別，如果不存在則返回 404 錯誤
    category = get_object_or_404(Category, pk=category_id)
    # 獲取該類別下所有活躍的拍賣清單
    listings_in_category = Listing.objects.filter(category=category, is_active=True).order_by('-created_at')
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings_in_category
    })