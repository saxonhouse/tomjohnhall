from django.shortcuts import render, HttpResponseRedirect, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.core import serializers
from django.utils import timezone
from forms import TransactionForm
from models import Transaction, GuiltWord, GuiltLink
import datetime
import requests
import random
import json
from urllib2 import urlopen
from urllib2 import Request
from bs4 import BeautifulSoup




def login_form(request):
    if request.session.has_key('logged_in'):
        return HttpResponseRedirect('new')
    else:
        return render(request, 'login.html', {'user_login': 'transactions:user_login'})

def user_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        request.session['logged_in'] = True
        login(request, user)
        return HttpResponseRedirect(reverse_lazy('transactions:new_transaction'))
    else:
        error = 'Invalid'
        return render(request, 'login.html', {'user_login': 'transactions:user_login', 'error': error})

def user_logout(request):
    if request.session.has_key('logged_in'):
        del request.session['logged_in']
    logout(request)
    logged_out = 'logged out!'
    return render(request, 'login.html', {'user_login': 'transactions:user_login', 'logged_out': logged_out})

def new_transaction(request):
    if request.session.has_key('logged_in'):
        # get the time, time as string, and location via json thingy
        now = datetime.datetime.now()
        strnow = now.strftime('%d/%m/%Y')
        send_url = 'http://freegeoip.net/json'
        try:
            r = requests.get(send_url)
            j = json.loads(r.text)
            lat = j['latitude']
            lon = j['longitude']
        except:
            lat = 0
            lon = 0

        if request.method == 'POST':
            # Get everything from form
            form = TransactionForm(request.POST, request.FILES)
            if form.is_valid():
                # clean up and set vars
                cd = form.cleaned_data
                item = cd['item']
                price = cd['price']
                shop = cd['shop']
                notes = cd['notes']
                image = request.FILES.get('user_image')
                bing_image = cd['bing_image']
                lat = request.POST.get('manual-lat', 0)
                lon = request.POST.get('manual-lon', 0)
                if lat != None:
                    t = Transaction(date= now, strdate = strnow, item = item, price = price, shop= shop, notes = notes, lat = lat, lon = lon)
                    # to prevent
                    if image:
                        t.image = image
                    else:
                        t.bing_image = bing_image
                    t.save()
                    success = True
                    return render(request, 'new_transaction.html', {'success': success})
                else:
                    location_null = True
                    form = TransactionForm()
                    lat = j['latitude']
                    lon = j['longitude']
                    return render(request, 'new_transaction.html', {'form': form, 'location_null':location_null, 'lat': lat, 'lon': lon})
        else:
            form = TransactionForm()
            return render(request, 'new_transaction.html', {'form': form, 'lat': lat, 'lon': lon})
    else:
        return render(request, 'login.html', {'user_login': 'transactions:user_login'})

def latest_transaction(request):
    transaction = Transaction.objects.all().order_by('-id')
    transaction = transaction[0]
    return redirect('transactions:transaction_detail', transaction_id = str(transaction.id))

def transaction_detail(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    prev_id = transaction.id - 1
    next_id = transaction.id + 1
    try:
        Transaction.objects.get(id = prev_id)
        prev_tran = str(prev_id)
    except Transaction.DoesNotExist:
        prev_tran = None
    try:
        Transaction.objects.get(id = next_id)
        next_tran = str(next_id)
    except Transaction.DoesNotExist:
        next_tran = None
    links = []
    guiltwords = transaction.guiltwords.all()
    for word in guiltwords:
        word_links = word.links.all()
        for link in word_links:
            links.append(link.link)
    return render(request, 'transaction_detail.html', {'transaction': transaction, 'prev_tran': prev_tran, 'next_tran': next_tran, 'links': links})

def soup(request):
    guiltlinks = GuiltLink.objects.all()
    titles = []
    descriptions = []
    images = []
    exceptions = []
    for link in guiltlinks:
        if link.title:
            pass
        else:
            try:
                page = urlopen(link.link)
            except Exception, e:
                exceptions.append(link.link)
                exceptions.append(str(Exception))
                continue
            try:
                USERAGENT = 'something'
                HEADERS = {'User-Agent': USERAGENT}
                req = Request(link.link, headers=HEADERS)
                page = urlopen(req)
            except Exception, e:
                exceptions.append(link.link)
                exceptions.append(str(Exception))
                continue
            soup = BeautifulSoup(page.read(), "html.parser")
            title = soup.find("meta", property="og:title")
            description = soup.find("meta", property="og:description")
            image_url = soup.find("meta", property="og:image")
            if title:
                link.title = title["content"]
                titles.append(title["content"])
            else:
                title = soup.find("title")
                if title:
                    link.title = str(title)
                    titles.append(title)
            if description:
                link.description = description["content"]
                descriptions.append(description["content"])
            if image_url:
                link.image_url = image_url["content"]
                images.append(image_url["content"])
            link.save()
    return render(request, 'soup.html', {'exceptions': exceptions, 'titles': titles, 'descriptions': descriptions, 'images': images})


def thing(request):
    random_idx = random.randint(0, Transaction.objects.count() - 1)
    random_obj = Transaction.objects.all()[random_idx]
    if request.session.has_key('previous_id'):
        while random_idx == request.session['previous_id']:
            random_idx = random.randint(0, Transaction.objects.count() - 1)
            random_obj = Transaction.objects.all()[random_idx]
    request.session['previous_id'] = random_idx
    transaction = random_obj
    return render(request, 'transaction_thing.html', {'transaction': transaction })

def guiltfeed(request):
    if request.method == 'POST':
        tran_id = request.POST.get('id')
        transaction = Transaction.objects.get(id=tran_id)
        guiltwords = sorted(transaction.guiltwords.all(), key=lambda x: random.random())
        links = []
        for word in guiltwords:
            word_links = word.links.all()
            for link in word_links:
                jsonlink = {}
                jsonlink["link"] = link.link
                jsonlink["title"] = link.title
                jsonlink["description"] = link.description
                jsonlink["image_url"] = link.image_url
                links.append(jsonlink)
        return JsonResponse(links, safe=False)

def change(request):
    if request.method == 'POST':
        random_idx = random.randint(0, Transaction.objects.count() - 1)
        random_obj = Transaction.objects.all()[random_idx]
        if request.session.has_key('previous_id'):
            while random_idx == request.session['previous_id']:
                random_idx = random.randint(0, Transaction.objects.count() - 1)
                random_obj = Transaction.objects.all()[random_idx]
    request.session['previous_id'] = random_idx
    transaction = random_obj
    links = []
    guiltwords = transaction.guiltwords.all()
    for word in guiltwords:
        word_links = word.links.all()
        for link in word_links:
            links.append(link.link)
    if transaction.image:
        image_url = transaction.image.url
    else:
        image_url = None
    if transaction.bing_image:
        bing_image = transaction.bing_image
    else:
        bing_image = None
    data_set = {'tran_id': transaction.id,
                'strdate': transaction.strdate,
                'item': transaction.item,
                'price': transaction.price,
                'shop': transaction.shop,
                'image_url': image_url,
                'bing_image': bing_image,
                'lat': transaction.lat,
                'lon': transaction.lon,
                'notes': transaction.notes, }
    return JsonResponse(data_set)
