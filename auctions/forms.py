from django import forms
from .models import Listing, Category # 導入 Listing 和 Category 模型

# 用途：用於創建新的拍賣清單的表單
class CreateListingForm(forms.ModelForm):
    # ModelForm 會自動根據模型定義來創建表單欄位
    class Meta:
        model = Listing # 表單關聯到 Listing 模型
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category'] # 選擇要顯示的欄位

        # Widgets 可以自定義表單欄位的 HTML 元素屬性，例如添加 CSS class
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'starting_bid': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional URL for an image'}),
            # Category 欄位將自動渲染為下拉式選單
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        # labels 可以自定義欄位在表單中顯示的標籤
        labels = {
            'title': '拍賣標題',
            'description': '物品描述',
            'starting_bid': '起始價格',
            'image_url': '圖片網址',
            'category': '類別',
        }

    # 為了讓 category 欄位顯示 Category 物件的名稱，我們需要自定義 queryset
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 獲取所有 Category 物件，並按名稱排序
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        # 允許 category 欄位為空選項
        self.fields['category'].required = False
        self.fields['category'].empty_label = "選擇類別 (可選)"
        