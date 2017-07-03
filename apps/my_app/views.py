# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.db.models import Count
from .models import User, Appointment
from django.core.exceptions import ObjectDoesNotExist
import time
import re
import datetime
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

# Create your views here.
def index(request):
    return render(request, "my_app/index.html")

def register(request):
    check = True
    if(len(request.POST['name']) < 2):
        messages.error(request, "Name must have at least 2 characters")
        check = False
    if(request.POST['name'].isalpha() == False): 
        messages.error(request, "Name can only consist of letters, please reenter your name")
        check = False
    if(not EMAIL_REGEX.match(request.POST['email'])):
        messages.error(request, "Please enter a valid email address")
        check = False  
    if(len(request.POST['password']) < 8):
        messages.error(request, "Password must be at least 8 characters long")
        check = False
    if(len(request.POST['password']) > 20):
        messages.error(request, "Password cannot be longer than 20 characters, please try another")
        check = False   
    if(request.POST['password'] != request.POST['confirm_password']):
        messages.error(request, "Passwords must match") 
        raise ValidationError('Sorry, someone already has that [...]')
        check = False
    if(len(request.POST['date_of_birth']) < 1):
        messages.error(request, "Please enter your date of birth")     
        check = False
    if not check:
        return redirect ('/')     
    
    User.objects.create(name=request.POST['name'], password=request.POST['password'], email=request.POST['email'], date_of_birth=request.POST['date_of_birth'])
    request.session['current_user'] = User.objects.get(email=request.POST['email']).id
    return redirect('/display_appointments')

def login(request):
    try:
        users = User.objects.get(email=request.POST['email'], password=request.POST['password'])
    
    except ObjectDoesNotExist:
        messages.error(request, "Invalid username or password")
        return redirect('/')    
    
    else:
        context = {}
        request.session['current_user'] = User.objects.get(email=request.POST['email'], password=request.POST['password']).id
        if "current_user" in request.session.keys():
            return redirect('/display_appointments')

def display_appointments(request):
    if 'current_user' in request.session.keys():
        context = {
            "user" : User.objects.get(pk=request.session['current_user']),
            "today" : datetime.datetime.now().date(),
            "appointments_today" : Appointment.objects.filter(user_id=User.objects.get(pk=request.session['current_user'])).filter(date=datetime.datetime.now().date()).order_by('time'),
            "appointments_future" : Appointment.objects.filter(user_id=User.objects.get(pk=request.session['current_user'])).exclude(date=datetime.datetime.now().date()).order_by('date'),
            "appointments" : Appointment.objects.all()
        }
        return render(request, 'my_app/display_appointments.html', context)

def add_appointment(request):
    check = True 
 
    if len(request.POST['date']) < 6:
        messages.error(request, "Please enter a valid date")
        check = False
    elif datetime.datetime.strptime(request.POST['date'], '%Y-%m-%d').date() < datetime.datetime.now().date():
        messages.error(request, "Date must be today or a future date") 
        check = False        
    if len(request.POST['time']) < 4:
        messages.error(request, "Please enter a valid time (e.g., 10:00 AM)")
        check = False  
    if len(request.POST['name']) < 1:
        messages.error(request, "Please enter a task")
        check = False
  
    if not check:
        return redirect('/display_appointments')

    try:
        Appointment.objects.get(time=request.POST['time'], date=request.POST['date'])
    except ObjectDoesNotExist:
        then = True
    else:
        messages.error(request, "You have an existing appointment at this time")
        return redirect('/display_appointments')   

    Appointment.objects.create(user_id=(User.objects.get(pk=request.session['current_user'])), name=request.POST['name'], status="Pending", date=request.POST['date'], time=request.POST['time'])  
    return redirect('/display_appointments')

def update_appointment(request, id):
    check = True
    if len(request.POST['date']) < 6:
        messages.error(request, "Please enter a valid date")
        check = False
    elif datetime.datetime.strptime(request.POST['date'], '%Y-%m-%d').date() < datetime.datetime.now().date():
        messages.error(request, "Date must be today or a future date") 
        check = False        
    if len(request.POST['time']) < 4:
        messages.error(request, "Please enter a valid time (e.g., 10:00 AM)")
        check = False    
    if len(request.POST['name']) < 1:
        messages.error(request, "Please enter a task")
        check = False
        return redirect('/')
    if not check:
        return redirect('/edit/'+ str(Appointment.objects.get(id=id).id))
    try:
        Appointment.objects.exclude(id=id).get(time=request.POST['time'], date=request.POST['date'])
    except ObjectDoesNotExist:
        then = True
    else:
        messages.error("You have another appointment at this time, please select another time")
        return redirect('/edit/'+ str(Appointment.objects.get(id=id).id))       
    appointment = Appointment.objects.get(id=id)
    appointment.name = request.POST['name']   
    appointment.status = request.POST['status']
    appointment.date = request.POST['date']
    appointment.time = request.POST['time']
    appointment.save()
    return redirect('/display_appointments')

def edit(request, id):
    context = {
        "appointment" : Appointment.objects.get(id=id),
        "date" : str(Appointment.objects.get(id=id).date),
        "time" : str(Appointment.objects.get(id=id).time)
    } 
    return render(request, 'my_app/edit_appointments.html', context) 

def delete(request, id):
    Appointment.objects.get(id=id).delete()
    return redirect('/display_appointments') 

def logout(request):
    request.session.clear()
    messages.add_message(request, messages.INFO, "Successfully logged out")
    return redirect('/')