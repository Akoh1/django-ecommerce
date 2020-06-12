from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView,View
from django.shortcuts import redirect
from django.utils import timezone
from .models import Product, Order, OrderItem, BillingAddress, Payment
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutOrderForm
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm

# Create your views here.
import stripe
stripe.api_key = settings.STRIPE_KEY



class Checkout(View):
    def get(self, *args, **kwargs):
        form = CheckoutOrderForm()
        context = {'form': form}
        return render(self.request, 'checkout.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutOrderForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            print(self.request.POST)
            if form.is_valid():
                country = form.cleaned_data.get('country')
                street = form.cleaned_data.get('street')
                apartment = form.cleaned_data.get('apartment')
                zip_code = form.cleaned_data.get('zip_code')
                # save_information = form.cleaned_data.get('save_information')
                # same_billing_address = form.cleaned_data.get('same_billing_address')
                payment = form.cleaned_data.get('payment')
                bill_address = BillingAddress(
                    user = self.request.user,
                    street = street,
                    country = country,
                    apartment = apartment,
                    zip_code = zip_code
                )
                bill_address.save()
                order.bill_address = bill_address
                order.save()
                if payment == 'S':
                    print(form.cleaned_data)
                    return redirect('core:payment')
                    # return redirect('core:payment', payment_option='stripe')
                elif payment == 'P':
                    return redirect('core:paypal_payment')
                else:
                    messages.warning(self.request, "Invalid Payment Option selected")
                    return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request, "You don't have an active order")
            return redirect("core:cart-summary")

def paypal_payment(request):
    order = Order.objects.get(user=request.user, ordered=False)
    context = {'order': order}
    amount = int(order.get_total() * 100)

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": amount,
        "item_name": "Order {}".format(order.id),
        "invoice": str(order.id),
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return": request.build_absolute_uri(reverse('core:paypal_done')),
        "cancel_return": request.build_absolute_uri(reverse('core:paypal_cancelled')),
        # "custom": "premium_plan",  # Custom command to correlate to some function later (optional)
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form,
               "order": order}
    return render(request, "paypal_payment.html", context) 

@csrf_exempt
def paypal_done(request):
    return render(request, "paypal_doen.html")

@csrf_exempt
def paypal_cancelled(request):
    return render(request, "paypal_cancelled.html")

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {'order': order}
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)

        try:

            charge = stripe.Charge.create(
              amount=amount,
              currency="usd",
              source=token,
              
            )

            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user =  self.request.user
            payment.amount = order.get_total()
            payment.save()

            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Your have successfuly processed this order")
            return redirect("/")
        except stripe.error.CardError as e:
            # print('Status is: %s' % e.http_status)
            # print('Type is: %s' % e.error.type)
            # print('Code is: %s' % e.error.code)
            #   # param is '' in this case
            # print('Param is: %s' % e.error.param)
            # print('Message is: %s' % e.error.message)
            messages.error(self.request, f"{e.error.message}")
            return redirect("/")
        except stripe.error.RateLimitError as e:
          # Too many requests made to the API too quickly
            messages.error(self.request, "Rate limit error")
            return redirect("/")
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print('Param is: %s' % e.error.param)
            print('Message is: %s' % e.error.message)
            messages.error(self.request, "Invalid parameters")
            return redirect("/")
        except stripe.error.AuthenticationError as e:
          # Authentication with Stripe's API failed
          # (maybe you changed API keys recently)
            messages.error(self.request, "Not authenticated")
            return redirect("/")
        except stripe.error.APIConnectionError as e:
          # Network communication with Stripe failed
            messages.error(self.request, "Network Error")
            return redirect("/")
        except stripe.error.StripeError as e:
           # Display a very generic error to the user, and maybe send
           # yourself an email
            messages.error(self.request, "Something went wrong, please try again!")
            return redirect("/")
        except Exception as e:
          # Something else happened, completely unrelated to Stripe
            messages.error(self.request, "A serious error occured we have been notified!")
            return redirect("/")

             

class HomeView(ListView):
    model = Product
    paginate_by = 10
    template_name = 'home.html'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product.html'


class CartSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'order': order}
            return render(self.request, 'cart_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You don't have an active order")
            return redirect("/")


@login_required
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    order_product, created = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False
        )
    my_order = Order.objects.filter(user=request.user, ordered=False)
    if my_order.exists():
        order = my_order[0]
        # to check if the order item is in the order
        if order.products.filter(product__slug=product.slug).exists():
            order_product.num_of_prod += 1
            order_product.save()
            messages.info(request, "The quantity of this product was updated in cart")
            return redirect("core:cart-summary")
        else:
            order.products.add(order_product)
            messages.info(request, "This product was added to cart")
            return redirect("core:cart-summary")
    else:
        date_ordered = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=date_ordered)
        order.products.add(order_product)
        messages.info(request, "This product was added to cart")
        return redirect("core:cart-summary")


@login_required
def remove_from_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    my_order = Order.objects.filter(user=request.user, ordered=False)
    if my_order.exists():
        order = my_order[0]
        # to check if the order item is in the order
        if order.products.filter(product__slug=product.slug).exists():
            order_product = OrderItem.objects.filter(
                product=product,
                user=request.user,
                ordered=False
                )[0]
            order.products.remove(order_product)
            messages.info(request, "This product was removed from cart")
            return redirect('core:cart-summary')
        else:
            messages.info(request, "This product was not in cart")
            return redirect('core:product', slug=slug)
    else:
        # display a message that says the user doesn't hace an order
        messages.info(request, "You do not have an active order")
        return redirect('core:product', slug=slug)  

@login_required
def remove_a_product_from_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    my_order = Order.objects.filter(user=request.user, ordered=False)
    if my_order.exists():
        order = my_order[0]
        # to check if the order item is in the order
        if order.products.filter(product__slug=product.slug).exists():
            order_product = OrderItem.objects.filter(
                product=product,
                user=request.user,
                ordered=False
                )[0]
            if order_product.num_of_prod > 1:
                order_product.num_of_prod -= 1
                order_product.save()
            else:
                order.products.remove(order_product)
            messages.info(request, "The quantity of this product was updated")
            return redirect('core:cart-summary')
        else:
            messages.info(request, "This product was not in cart")
            return redirect('core:product', slug=slug)
    else:
        # display a message that says the user doesn't hace an order
        messages.info(request, "You do not have an active order")
        return redirect('core:product', slug=slug)
    
