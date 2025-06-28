from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from django.core.mail import send_mail
from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/order_history.html", {"orders": orders})


def checkout(request):
    cart = request.session.get("cart", {})
    if not cart:
        return redirect("product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            total = sum(item["price"] * item["quantity"] for item in cart.values())
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                address=form.cleaned_data["address"],
                total_price=total,
            )
            for pid, item in cart.items():
                product = Product.objects.get(id=pid)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price=item["price"],
                )

            # Clear cart after order
            request.session["cart"] = {}
            send_mail(
                subject="Order Confirmation",
                message=f'Thank you {form.cleaned_data["full_name"]}, your order #{order.id} was placed!',
                from_email="noreply@yourecom.com",
                recipient_list=[form.cleaned_data["email"]],
            )
            return render(request, "store/order_success.html", {"order": order})
    else:
        form = CheckoutForm()

    return render(request, "store/checkout.html", {"form": form, "cart": cart})


def product_list(request):
    products = Product.objects.all()

    return render(
        request,
        "store/product_list.html",
        {"products": products},
    )


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "store/product_detail.html", {"product": product})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get("cart", {})

    if str(product_id) in cart:
        cart[str(product_id)]["quantity"] += 1
    else:
        cart[str(product_id)] = {
            "name": product.name,
            "price": float(product.price),
            "quantity": 1,
            "image": product.image.url,
        }

    request.session["cart"] = cart
    return redirect("view_cart")


def view_cart(request):
    cart = request.session.get("cart", {})
    total = sum(item["price"] * item["quantity"] for item in cart.values())
    return render(request, "store/cart.html", {"cart": cart, "total": total})


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session["cart"] = cart
    return redirect("view_cart")
