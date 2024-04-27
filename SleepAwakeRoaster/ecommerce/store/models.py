from django.db import models
from django.urls import reverse

# Create your models here.

class Category(models.Model):
    # จำกัดข้อความและลักษณะเฉพาะไม่ซ้ำกัน
    name=models.CharField(max_length=255,unique=True) 
    # เป็นการตั้งชื่อเล่นให้ข้อมูลในโมเดล ควบคุมการเปลี่ยนแปลงข้อมูล Slug
    slug=models.SlugField(max_length=255,unique=True)

    def __str__(self):
        return self.name
    #เปลี่ยนชื่อการจัดการเช่น category to หมวดหมู่สินค้า
    class Meta:
        ordering=('name',) #จัดเรียงข้อมูล
        verbose_name='หมวดหมู่สินค้า'
        verbose_name_plural="ข้อมูลประเภทสินค้า"
    #self ชี้ไปยังหมวกหมู่สินค้าที่เราจะใช้
    def get_url(self): 
        return reverse('product_by_category',args=[self.slug])

class Product(models.Model):
    name=models.CharField(max_length=255,unique=True)
    #ตั้งค่าslug
    slug=models.SlugField(max_length=255,unique=True)
    description=models.TextField(blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    #ผูกข้อมูล เอาPrimarykey มาเป็น ForeignKey,on_delete=models.CASCADE ตอนลบข้อมูลลบทั้งสองส่วน
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    #Upload product picture
    image=models.ImageField(upload_to="product",blank=True)
    #จัดstock สินค้า
    stock=models.IntegerField()
    #สถานะสินค้า
    available=models.BooleanField(default=True)
    #วันเวลาที่ stock สินค้า
    created=models.DateTimeField(auto_now_add=True)
    #updated มีการอัปเดตข้อมูล
    updated=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_url(self): 
        return reverse('productDetail',args=[self.category.slug,self.slug])
    
    class Meta:
        ordering=('name',) #จัดเรียงข้อมูล
        verbose_name='สินค้า'
        verbose_name_plural="ข้อมูลสินค้า"

class Cart(models.Model):

    cart_id=models.CharField(max_length=255,blank=True)
    date_added=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    
    class Meta:
        db_table='cart'
        ordering=('date_added',)
        verbose_name='ตะกร้าสินค้า'
        verbose_name_plural='ข้อมูลตะกร้าสินค้า'


#รายการสินค้่าในตะกร้า
class CartItem(models.Model):

    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE)
    quantity=models.IntegerField()
    active=models.BooleanField(default=True)

    class Meta:
        db_table='cartItem'
        verbose_name='รายการสินค้าในตะกร้า'
        verbose_name_plural='ข้อมูลรายการสินค้าในตะกร้า'
    
    
    #คำนวณราคาสินค้าบวกจำนวนสินค้า
    def sub_total(self):
        return self.product.price * self.quantity
    
    def __str__(self) -> str:
        return self.product.name 
    
class Order(models.Model):
    name=models.CharField(max_length=255,unique=True)
    address=models.CharField(max_length=255,unique=True)
    city=models.CharField(max_length=255,unique=True)
    postcode=models.CharField(max_length=255,unique=True)
    total=models.DecimalField(max_digits=10,decimal_places=2)
    email=models.EmailField(max_length=250,blank=True)
    token=models.CharField(max_length=255,unique=True)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)

    class Meta:
        db_table='Order'
        ordering=('id',)

    def __str__(self) -> str:
        return str(self.id)
    
class OrderItem(models.Model):
    product=models.CharField(max_length=250)
    quantity=models.IntegerField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)

    class Meta:
        db_table='OrderItem'
        ordering=('order',)

    def sub_total(self):
        return self.quantity*self.price
    def __str__(self) -> str:
        return self.product