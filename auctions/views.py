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
