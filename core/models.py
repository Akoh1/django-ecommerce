from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField
# Create your models here.

CHOICES_OF_CATEGORY = (
	('S', 'SHIRT'),
	('SW', 'Sport Wear'),
	('OW', 'Outwear')
)

LABELS = (
	('P', 'primary'),
	('S', 'secondary'),
	('D', 'danger')
)


class Product(models.Model):
	"""docstring for Product"""
	title = models.CharField(max_length=100)
	price = models.FloatField()
	price_discount = models.FloatField(blank=True, null=True)
	category = models.CharField(choices=CHOICES_OF_CATEGORY, max_length=2)
	label = models.CharField(choices=LABELS, max_length=2)
	decription = models.TextField()
	slug = models.SlugField()

	def __str__(self):
		return self.title

	def get_add_to_cart_url(self):
		return reverse("core:add-to-cart", kwargs={
			'slug': self.slug
			})

	def get_remove_from_cart_url(self):
		return reverse("core:remove-from-cart", kwargs={
			'slug': self.slug
			})

	def get_absolute_url(self):
		return reverse("core:product", kwargs={
			'slug': self.slug
		})


class OrderItem(models.Model):
	"""docstring for OrderItem"""
	user = models.ForeignKey(settings.AUTH_USER_MODEL, 
							 on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	ordered = models.BooleanField(default=False)
	num_of_prod = models.IntegerField(default=1)

	def __str__(self):
		return f"{self.num_of_prod} of {self.product.title}"

	def get_total_price_of_product(self):
		return self.num_of_prod * self.product.price

	def get_total_discount_price_of_product(self):
		return self.num_of_prod * self.product.price_discount

	def get_absolute_price(self):
		if self.product.price_discount:
			return self.get_total_discount_price_of_product()
		return self.get_total_price_of_product()


class Order(models.Model):
	"""docstring for Order"""
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	products = models.ManyToManyField(OrderItem)
	start_date = models.DateTimeField(auto_now_add=True)
	ordered_date = models.DateTimeField()
	ordered = models.BooleanField(default=False)
	bill_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, 
									 blank=True, null=True)
	payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, 
								blank=True, null=True)

	
	def __str__(self):
		return self.user.username

	def get_total(self):
		total = 0
		for product_order in self.products.all():
			total += product_order.get_absolute_price()
		return total


class BillingAddress(models.Model):

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	street = models.CharField(max_length=100)
	country = CountryField(multiple=False)
	apartment = models.CharField(max_length=100)
	zip_code = models.CharField(max_length=100)

	def __str__(self):
		return self.user.username
		
		
class Payment(models.Model):
	stripe_charge_id = models.CharField(max_length=50)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, 
							 on_delete=models.SET_NULL,
							 blank=True, null=True)
	amount = models.FloatField()
	timestamp =  models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.user.username
