from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from main.models import Category, Product, Review, WishList, Cart, CartProduct


def index(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    if request.user.is_authenticated:
        for product in products:
            product.is_like = WishList.objects.filter(product=product, user=request.user).exists()
    reviews = Review.objects.all()
    mark = sum(review.mark for review in reviews) // len(reviews) if reviews else 0
    context = {
        'categories': categories,
        'products': products,
        'rating': range(1, 6),
        'mark': mark,
    }
    return render(request, 'front/index.html', context)


def product_detail(request, code):
    product = Product.objects.get(code=code)
    reviews = Review.objects.filter(product=product)
    images = product.productimg_set.all()
    liked = WishList.objects.filter(product=product, user=request.user).exists()
    mark = sum(review.mark for review in reviews) // len(reviews) if reviews else 0
    context = {
        'product': product,
        'mark': mark,
        'rating': range(1, 6),
        'images': images,
        'reviews': reviews,
        'liked': liked,
    }
    return render(request, 'front/product/detail.html', context)


def product_list(request, code):
    category = Category.objects.get(code=code)
    products = Product.objects.filter(category=category)
    if request.user.is_authenticated:
        for product in products:
            product.is_like = WishList.objects.filter(product=product, user=request.user).exists()
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'front/category/product_list.html', context)


def product_delete(request, id):
    CartProduct.objects.get(id=id).delete()
    return redirect('front:active_cart')


def filter_products(request):
    search_query = request.GET.get('search')
    products = Product.objects.filter(name__icontains=search_query)
    return render(request, 'front/index.html', {'products': products})


@login_required(login_url='auth:login')
def active_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user, status=1)
    return redirect('front:cart_detail', code=cart.code)


@login_required(login_url='auth:login')
def cart_detail(request, code):
    cart = Cart.objects.get(code=code)
    queryset = CartProduct.objects.filter(cart=cart)
    if request.method == 'POST':
        data = request.POST.dict()
        for id, value in data.items():
            if id != 'csrfmiddlewaretoken':
                cart_product = CartProduct.objects.get(id=id)
                cart_product.count = value
                cart_product.product.quantity -= int(value)
                cart_product.product.save()
                cart.save()
                cart_product.save()
    context = {
        'cart': cart,
        'queryset': queryset
    }
    return render(request, 'front/carts/detail.html', context)


def add_to_cart(request, code):
    if Product.objects.filter(code=code).exists():
        product = Product.objects.get(code=code)
        cart, _ = Cart.objects.get_or_create(user=request.user, status=1)
        is_product = CartProduct.objects.filter(product=product, cart=cart).exists()
        if is_product:
            cart_product = CartProduct.objects.get(product=product, cart=cart)
            cart_product.count += 1
            cart_product.save()
            return redirect('front:active_cart')
        CartProduct.objects.create(product=product, cart=cart, count=1)
        return redirect('front:active_cart')
    return redirect('front:index')


@login_required(login_url='auth:login')
def list_wishlist(request):
    wishlists = WishList.objects.filter(user=request.user)
    context = {
        'wishlists': wishlists,
    }
    return render(request, 'front/wishlist/list.html', context)


@login_required(login_url='auth:login')
def remove_wishlist(request, code):
    WishList.objects.get(user=request.user, product__code=code).delete()
    return redirect('front:wishlist')


@login_required(login_url='auth:login')
def add_wishlist(request, code):
    product = Product.objects.get(code=code)
    if WishList.objects.filter(product=product, user=request.user).exists():
        return redirect('front:remove_wishlist', code=product.code)
    WishList.objects.create(product=product, user=request.user)
    return redirect('front:wishlist')


@login_required(login_url='auth:login')
def order_list(request):
    ordered = CartProduct.objects.filter(cart__user=request.user, cart__status=2)
    returned = CartProduct.objects.filter(cart__user=request.user, cart__status=3)
    context = {
        'ordered': ordered,
        'returned': returned,
    }
    return render(request, 'front/order/list.html', context)
