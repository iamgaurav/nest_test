from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from nest import config
from django.http import HttpResponseForbidden
import requests as r
import json

def get_next_data(headers):
    try:
        init_res = r.get('https://developer-api.nest.com', headers=headers, allow_redirects=False)
        if init_res.status_code == 307:
            api_response = r.get(init_res.headers['Location'], headers=headers, allow_redirects=False)
            if api_response.status_code == 200:
                return api_response.json()
        elif init_res.status_code == 200:
            return init_res.json()
    except Exception as ce:
        print(ce)

# Create your views here.

def index(request):
    if request.session.get('access_token'):
        return HttpResponseRedirect("/client")
    else:
        context = { 'client_id': config.CLIENT_ID }
        return render(request,'nest/index.html',context)

def client(request):
    if request.method == "POST":
        key = request.POST['code']
        request.session['key'] = key

        # Prepare to request access token
        payload = {'client_id': config.CLIENT_ID, 'client_secret': config.CLIENT_SECRET,
                   'grant_type': 'authorization_code', 'code': key}
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        req = r.post(url="https://api.home.nest.com/oauth2/access_token", data=payload, headers=headers)

        if req.status_code == 200:
            response = req.json()
            request.session['access_token'] = response["access_token"]

            # Fetch all Devices
            headers = {"Authorization": "Bearer " + response["access_token"], 'Content-type': 'application/json'}
            response = get_next_data(headers)

            devices = response["devices"]["thermostats"]
            request.session.modified = True
            devices = response["devices"]["thermostats"]
            return render(request, 'nest/client.html', context={'devices': devices})
        else:
            return HttpResponseRedirect("/client")

    else:
        if request.session.get('access_token'):
            token = request.session.get('access_token')
            # Fetch all Devices
            headers = {"Authorization": "Bearer " + token, 'Content-type': 'application/json'}
            response = get_next_data(headers)

            devices = response["devices"]["thermostats"]
            request.session.modified = True
            devices = response["devices"]["thermostats"]
            return render(request, 'nest/client.html', context={'devices': devices})

def thermostat_update(request):
    if request.method == "POST":
        id = request.POST['id']
        headers = {"Authorization": "Bearer " + request.session.get('access_token'), 'Content-type': 'application/json'}
        json_data = { 'target_temperature_f' : int(request.POST['newtemp']) }
        try:
            init_res = r.put('https://developer-api.nest.com/devices/thermostats/' + id, headers=headers, allow_redirects=False, json=json_data)
            if init_res.status_code == 307:
                api_response = r.put(init_res.headers['Location'], headers=headers, allow_redirects=False, json=json_data)
                if api_response.status_code == 200:
                    return HttpResponseRedirect("/client")
            elif init_res.status_code == 200:
                    return HttpResponseRedirect("/client")
        except Exception as ce:
            print(ce)
            return HttpResponseRedirect("/client")
    else:
        print(request.session.get('access_token'))
        return HttpResponse("Yes")