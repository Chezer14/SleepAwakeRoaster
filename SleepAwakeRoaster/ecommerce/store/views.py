from django.shortcuts import render,get_object_or_404,redirect
import stripe.error
from store.models import Category,Product,Cart,CartItem,Order,OrderItem
from store.forms import SignUpForm
from django.contrib.auth.models import Group,User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,authenticate,logout
from django.core.paginator import Paginator,EmptyPage,InvalidPage
from django.contrib.auth.decorators import login_required
from django.conf import settings
import stripe
# Create your views here.

def index(request,category_slug=None):
    products=None
    category_page=None
    #ถ้าหากว่าค่า category_slug!=None จะมีการเอาค่า slug มาใช้
    if category_slug!=None:
        #beams -> สินค้าหมวดหมู่เมล็ดจะส่งไปยัง productsและจะกรองหมวดหมู่สินค้า
        category_page=get_object_or_404(Category,slug=category_slug)
        products=Product.objects.all().filter(category=category_page,available=True)
    else:
        #ดึงหมวดหมู่มาทั้งหมด
        products=Product.objects.all().filter(available=True)
    
    
    #กำหนดหน้าเริ่มต้น
    paginator=Paginator(products,2)
    try:
        page=int(request.GET.get('page','1'))
    except:
        page=1

    try:
        productperPage=paginator.page(page)
    except (EmptyPage,InvalidPage):
        productperPage=paginator.page(paginator.num_pages)
    
    return render(request,'index.html',{'products':productperPage,'category':category_page})

def productPage(request,category_slug,product_slug): #ใช้ query ข้อมูลสินค้าตาม 2เงื่อนไขตามกำหนด

    try:
        product=Product.objects.get(category__slug=category_slug,slug=product_slug) #เรียกสินค้าตาม slug  และ category slug
    except Exception as e :
        raise e
    return render(request,'product.html',{'product':product})


def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart

@login_required(login_url='signIn')
def addCart(request,product_id):

    #ดึงสินค้าตามรหัส
    product=Product.objects.get(id=product_id)
    #สร้างตะกร้าสินค้า
    try:
        #เคยสร้างจะใช้ตะกร้าเดิม
        cart=Cart.objects.get(cart_id=_cart_id(request))
    
    except Cart.DoesNotExist:
         #สร้างตะกร้าสินค้าใหม่
         cart=Cart.objects.create(cart_id=_cart_id(request))
         cart.save()

    #ซื้อรายการสินค้าซ้ำ นับจำนวนสินค้า
    #ซื้อรายการสินค้าครั้งแรก นับจำนวนสินค้า

    try:
        #ซื้อรายการสินค้าซ้ำ นับจำนวนสินค้า
        cart_item=CartItem.objects.get(product=product,cart=cart)
        if cart_item.quantity<cart_item.product.stock:

            #เปลี่ยนแปลงจำนวน
            cart_item.quantity+=1
            cart_item.save()
    except CartItem.DoesNotExist:
        #ซื้อรายการสินค้าครั้งแรก นับจำนวนสินค้า
        #บันทึกลงฐานข้อมูล
        cart_item=CartItem.objects.create(
            product=product,
            cart=cart,
            quantity=1
        )
        cart_item.save()
    return redirect('cartdetail')

def cartdetail(request):
    total=0
    counter=0
    cart_items=None
    try:
        cart=Cart.objects.get(cart_id=_cart_id(request)) #ดึงตะกร้าสินค้า
        cart_items=CartItem.objects.filter(cart=cart,active=True) #ดึงข้อมูลสินค้าในตะกร้า
        for item in cart_items:
            total+=(item.product.price * item.quantity)
            counter+=item.quantity
    except Exception as e:
        pass
    stripe.api_key=settings.SECRET_KEY
    stripe_total=int(total*100)
    description="Payment Online"
    data_key=settings.PUBLIC_KEY

    if request.method=='POST':
        try:
            token=request.POST['stripeToken']
            email=request.POST['stripeEmail']
            name=request.POST['stripeBillingName']
            address=request.POST['stripeBillingAddressLine1']
            city=request.POST['stripeBillingAddressCity']
            postcode=request.POST['stripeBillingAddressZip']
            
            customer=stripe.Customer.create(
                email=email,
                source=token
            )
            charge=stripe.Charge.create(
                amount=stripe_total,
                currency='thb',
                description=description,
                customer=customer.id
            )
            #บันทึกข้อมูลใบสั่งซื้อ
            order=Order.objects.create(
                name=name,
                address=address,
                city=city,
                postcode=postcode,
                total=total,
                email=email,
                token=token
            )
            order.save()

            #บันทึกรายการสั่งซื้อ
            for item in cart_items:
                order_item=OrderItem.objects.create(
                    product=item.product.name,
                    quantity=item.quantity,
                    price=item.product.price,
                    order=order,
                )
                order_item.save()
                #ลดจำนวนStock
                product=Product.objects.get(id=item.product.id)
                product.stock=int(item.product.stock-order_item.quantity)
                product.save()
                item.delete()
            return redirect('thankyou')
        
        except stripe.error.CardError as e:
            return False,e
    return render(request,'cartdetail.html',
                  dict(cart_items=cart_items,total=total,counter=counter,
                       data_key=data_key,description=description,strip_total=stripe_total))

def removeCart(request,product_id):
    #ทำงานในตะกร้าสินค้า
    cart=Cart.objects.get(cart_id=_cart_id(request))
    #ลบสินค้า 1 
    product=get_object_or_404(Product,id=product_id)
    cartItem=CartItem.objects.get(product=product,cart=cart)

    cartItem.delete()
    return redirect('cartdetail')

def signUpView(request):
    #บันทึกข้อมูลuser
    
    if request.method=='POST':
        form=SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data.get('username')
            signUpUser=User.objects.get(username=username)
            customer_group=Group.objects.get(name='Customer')
            customer_group.user_set.add(signUpUser)
    else:
        form=SignUpForm()
    return render(request,'signup.html',{'form':form})

def signInView(request):
    #รับค่าจากuser
    if request.method=='POST':
        form=AuthenticationForm(data=request.POST)
        if form.is_valid():
            #เช็คusername
            username=request.POST['username']
            password=request.POST['password']
            #เช็คว่าถูกต้องหรือไม่หากจับคู่กัน
            user=authenticate(username=username,password=password)
            if user is not None:
                login(request,user)
                return redirect('home')
            else:
                return redirect('signUp')
    else:
        form=AuthenticationForm()

    return render(request,'signIn.html',{'form':form})

def signOutView(request):
        logout(request)
        return redirect('signIn')

def search(requset):
    products=Product.objects.filter(name__contains=requset.GET['title'])
    return render(requset,'index.html',{'products':products})

def orderHistory(request):
    #เช็คว่าใครเข้าlogin
    if request.user.is_authenticated:
        email=str(request.user.email)
        orders=Order.objects.filter(email=email)
    return render(request,'orders.html',{'orders':orders})

def viewOrder(request,order_id):
    if request.user.is_authenticated:
        email=str(request.user.email)
        order=Order.objects.get(email=email,id=order_id)
        orderitem=OrderItem.objects.filter(order=order)
    return render(request,'viewOrder.html',{'order': order, 'order_items': orderitem})

def thankyou(request):
    return render(request,'thankyou.html')