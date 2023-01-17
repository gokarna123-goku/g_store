from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.contrib.auth import authenticate, login, logout
from django.views import generic
from .forms import CheckoutForm, RegistrationForm, LoginForm
from django.db.models import Q 
from django.core.paginator import Paginator
import requests
from .models import *

class EcomMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and request.user.customer:
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context[""] = 
    #     return context
    

# Create your views here.

class HomeView(EcomMixin, generic.TemplateView):
    template_name = 'home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = Product.objects.all().order_by("-id")
        paginator = Paginator(all_products, 4)
        page_number = self.request.GET.get('page')
        product_list = paginator.get_page(page_number)
        context['product_list'] = product_list
        return context

class AllProductView(EcomMixin, generic.TemplateView):
    template_name = 'allproducts.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allcategories'] = Category.objects.all().order_by("-id")
        return context

class ProductDetailView(EcomMixin, generic.TemplateView):
    template_name = 'productdetail.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        # print(slug + " is the slug value getting from backend")
        # context['product'] = Product.objects.get(slug=url_slug)
        product = Product.objects.get(slug=url_slug)
        product.view_count += 1
        product.save()
        context['product'] = product
        return context

class AddToCartView(EcomMixin, generic.TemplateView):
    template_name = 'addtocart.html'
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        # get product id from requested url
        product_id = self.kwargs['pro_id']
        # get product
        product_obj = Product.objects.get(id=product_id)
        # check if cart exists
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(product=product_obj)
            # Items already exists in cart
            if this_product_in_cart.exists():
                cartproduct = this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
            # New item is added in cart
            else:
                cartproduct = CartProduct.objects.create(cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save() 
        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session['cart_id'] = cart_obj.id
            cartproduct = CartProduct.objects.create(cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save() 
        # check if product already exists
        # 
        return context

class EmptyCartView(generic.View):
    def get(self, request, *args, **kwargs):
        cart_id = request.session.get('cart_id', None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total = 0
            cart.save()
        return redirect('ecomapp:mycart')

class MyCartView(generic.TemplateView):
    template_name = 'mycart.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context['cart'] = cart
        return context

class CheckoutView(EcomMixin, generic.CreateView):
    template_name = 'checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('ecomapp:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            pass
        else:
            return redirect('/login/?next=/checkout/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
        else:
            cart_obj = None
        context['cart'] = cart_obj
        return context

    def form_valid(self, form):
        cart_id = self.request.session.get('cart_id')
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0 
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session['cart_id']
            paymeth = form.cleaned_data.get("payment_method")
            order = form.save()
            if paymeth == 'Khalti':
                return redirect(reverse('ecomapp:khaltirequest') + '?o_id=' + str(order.id))
        else:
            return redirect('ecomapp:home')
        return super().form_valid(form)

class KhaltiRequestView(generic.View):
    template_name = 'khaltirequest.html'
    def get(self, request, *args, **kwargs):
        o_id = request.GET.get('o_id')
        # print(o_id, " order id")
        order = Order.objects.get(id=o_id)
        context = {
            'order':order,
        }
        return render(request, self.template_name, context)


class KhaltiVerifyView(generic.View):
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        amount = request.GET.get('amount')
        o_id = request.GET.get('order_id')
        # print(o_id, " ===== Order id =====")
        url = "https://khalti.com/api/v2/payment/verify/"
        payload = {
            'token': token,
            'amount': amount
        }
        headers = {
            'Authorization': 'Key test_secret_key_0cb8e03dc38049c68244c05ae99b77fe'
        }

        order_obj = Order.objects.get(id=o_id)
        # print(order_obj, " ==== order obj ==== ")

        response = requests.request("POST", url, headers=headers, data=payload)

        resp_dict = response.json()
        if resp_dict.get("idx"):
            success = True
            order_obj.payment_completed = True
            order_obj.save()
        else:
            success: False
        # print(resp_dict, " response data")

        data = {
            "success":success,
        }
        return JsonResponse(data)

class ManageView(EcomMixin, generic.View):
    def get(self, request, *args, **kwargs):
        print("This is manage cart section")
        cp_id = self.kwargs['cp_id']
        action = request.GET.get('action')
        # print(cp_id, action)
        cp_obj = CartProduct.objects.get(id=cp_id)
        cart_obj = cp_obj.cart
        if action == 'inc':
            cp_obj.quantity +=1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
        elif action == 'dcr':
            cp_obj.quantity -= 1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity == 0:
                cp_obj.delete()
        elif action == 'rmv':
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        else:
            pass
        return redirect('ecomapp:mycart')

class AboutView(EcomMixin, generic.TemplateView):
    template_name = 'about.html'

class RegisterView(generic.CreateView):
    template_name = 'register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy("ecomapp:home")

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        email = form.cleaned_data.get('email')
        user = User.objects.create_user(username, email, password)
        form.instance.user = user
        login(self.request, user)
        return super().form_valid(form)

class LogoutView(generic.View):
    def get(self, request):
        logout(request)
        return redirect('ecomapp:home')

class LoginView(generic.FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = reverse_lazy("ecomapp:home")
    # Form valid method is a type of post method and is available in createview, formview and updateview
    def form_valid(self, form):
        uname = form.cleaned_data.get('username')
        passwd = form.cleaned_data.get('password')
        user = authenticate(username=uname, password=passwd)
        if user is not None and Customer.objects.filter(user=user).exists():
            login(self.request,user)
        else:
            return render(self.request, self.template_name, {'form':self.form_class, 'error': "Invalid Credentials!!!"})
        return super().form_valid(form)
    
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url

class UserProfileView(generic.TemplateView):
    template_name = 'userprofile.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect('/login/?next=/userprofile/')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context['customer'] = customer
        orders = Order.objects.filter(cart__customer=customer).order_by('-id')
        context['orders'] = orders
        return context

class CustomerOrderDetailView(generic.DetailView):
    template_name = 'customerorderdetail.html'
    model = Order
    context_object_name = "order_obj"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            order_id = self.kwargs['pk']
            order = Order.objects.get(id=order_id)
            if request.user.customer != order.cart.customer:
                return redirect('ecomapp:userprofile')
        else:
            return redirect('/login/?next=/userprofile/')
        return super().dispatch(request, *args, **kwargs)

# Admin login view
class AdminLoginView(generic.FormView):
    template_name = 'adminpages/adminlogin.html'
    form_class = LoginForm
    success_url = reverse_lazy('ecomapp:adminhome')

    def form_valid(self, form):
        uname = form.cleaned_data.get('username')
        passwd = form.cleaned_data.get('password')
        usr = authenticate(username=uname, password=passwd)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request,usr)
        else:
            return render(self.request, self.template_name, {'form':self.form_class, 'error': "Invalid Credentials!!!"})
        return super().form_valid(form)

class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect('/login/?next=/userprofile/')
        return super().dispatch(request, *args, **kwargs)
    
class AdminHomeView(AdminRequiredMixin, generic.TemplateView):
    template_name = 'adminpages/adminhome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pendingorders'] = Order.objects.filter(order_status='Order Received').order_by('-id')
        return context

class AdminOrderDetailView(AdminRequiredMixin, generic.DetailView):
    template_name = 'adminpages/adminorderdetail.html'
    model = Order
    context_object_name = "order_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allstatus'] = ORDER_STATUS
        return context

class AdminOrderListView(AdminRequiredMixin, generic.ListView):
    template_name = 'adminpages/adminorderlist.html'
    queryset = Order.objects.all().order_by('-id')
    context_object_name = "allorders"

class AdminOrderStatusChangeView(AdminRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs['pk']
        order_obj = Order.objects.get(id=order_id)
        new_status = request.POST.get('status')
        order_obj.order_status = new_status
        order_obj.save()
        # print(new_status, " new status ")
        # print(order_obj, " order obj ")
        return redirect(reverse_lazy('ecomapp:adminorderdetail', kwargs={'pk': order_id}))

class SearchView(generic.TemplateView):
    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kw = self.request.GET.get('keyword')
        results = Product.objects.filter(Q(title__icontains=kw) | Q(description__icontains=kw))
        context['results'] = results
        return context


# Ended