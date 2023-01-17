from django.urls import path 
from .views import *

app_name = 'ecomapp'

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('about/', AboutView.as_view(), name="about"),
    path('all-products/', AllProductView.as_view(), name="allproducts"),
    # <> means dynamic value
    path('product/<slug:slug>/', ProductDetailView.as_view(), name="productdetail"),
    path('add-to-cart-<int:pro_id>/', AddToCartView.as_view(), name="addtocart"),
    path('my-cart/', MyCartView.as_view(), name="mycart"),
    path('manage-cart/<int:cp_id>/', ManageView.as_view(), name='managecart'),
    path('empty-cart/', EmptyCartView.as_view(), name='emptycart'),
    path('checkout/', CheckoutView.as_view(), name="checkout"),

    # khaltipayment
    path('khalti-request/', KhaltiRequestView.as_view(), name="khaltirequest"),
    path('khalti-verify/', KhaltiVerifyView.as_view(), name="khaltiverify"),

    path('register/', RegisterView.as_view(), name="register"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('login/', LoginView.as_view(), name="login"),

    path('profile/', UserProfileView.as_view(), name="userprofile"),
    path('profile/order-<int:pk>/', CustomerOrderDetailView.as_view(), name="customerorderdetail"),


    path('search/', SearchView.as_view(), name="search"),

    path('admin-login/', AdminLoginView.as_view(), name="adminlogin"),
    path('admin-home/', AdminHomeView.as_view(), name="adminhome"),
    path('admin-order/<int:pk>/', AdminOrderDetailView.as_view(), name="adminorderdetail"),
    path('admin-all-orders/', AdminOrderListView.as_view(), name="adminorderlist"),
    path('admin-order-<int:pk>-change/', AdminOrderStatusChangeView.as_view(), name="adminorderstatuschange"),
]
