from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from datetime import datetime,time
import geocoder
import math
import hmac
import hashlib
import base64
import json
import pytz
import requests

import pickle
from django.conf import settings
import cv2
from firebase import firebase

from PIL import Image
import base64

import matplotlib.pyplot as plt
from io import StringIO
import qrcode

from datetime import timedelta, date
import pandas as pd
import xlwt
from xlwt import Workbook


config = {
    "apiKey":"AIzaSyB4q-zEJzOjwR69oT1F24tJa-RyGw7BHUQ",
    "authDomain":"qr-code-attendance-syste-68dd9.firebaseapp.com",
    "databaseURL":"https://qr-code-attendance-syste-68dd9-default-rtdb.firebaseio.com",
    "storageBucket":"qr-code-attendance-syste-68dd9.appspot.com"
    }

firebaseconn = firebase.FirebaseApplication(config["databaseURL"],None)


def validate_qr_data(encoded_payload, secret_key):
    # Decode the payload
    decoded_data = json.loads(base64.urlsafe_b64decode(encoded_payload).decode())
    data = decoded_data["data"]
    received_signature = decoded_data["signature"]

    data_string = json.dumps(data, sort_keys=True)
    expected_signature = hmac.new(
        secret_key.encode(),
        data_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if received_signature != expected_signature:
        raise ValueError("Invalid QR Code Signature")

    return data


def Admin(request):
    try:
        print("hello")
        
        manualusername = "admin"
        manualpassword = "password"

        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            print(f"Username: {username}, Password: {password}")
            
        if username == manualusername and password == manualpassword:
            print("Login successful")
            return redirect('adminpanel') 
        else:
            error_message = "Invalid username or password"
            print(error_message)

        return render(request, 'login.html', {'error': error_message})
    except Exception as e:
        print(f"An error occurred: {e}")
        return render(request, 'login.html', {'error': 'An unexpected error occurred.'})



def sendtoparents(parentsno):

    url = "https://www.fast2sms.com/dev/bulkV2"

    try:

        querystring = {"authorization":"OYlEPe1DCdxAMpzIr6Xqf9a0cRVU4K8mnTjibsBv5hHtJ2w37gVBT3ki8yRpHlaoj9XG26Ag0fDrY4eO",
                    "message":"This is test message",
                    "language":"english",
                    "route":"q",
                    "numbers":parentsno}

        headers = {
            'cache-control': "no-cache"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)

        return {"success":True,"message":response.text}

    except Exception as e:
        print(e)
        return {"success":False,"message":"An error occured while sending the message"}


def dashboard(request):
    return render(request, "dashboard.html")


def submitattendance(request):
    if request.method == "POST":
        subject = request.POST.get('selectsubject')
        print(subject)

        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        detector = cv2.QRCodeDetector()

        while True:
            ret, img = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                continue
            
            if img is None:
                print("Error: Captured frame is empty")
                continue

            img = cv2.resize(img, (320, 240))
            data, bbox, _ = detector.detectAndDecode(img)

            cv2.imshow("Frame", img)  # Show the captured frame
            if cv2.waitKey(1) == ord('q'):  # Press 'q' to quit
                break

            if data:
                rollno = data
                print(rollno)
                break

            checktime = validate_qr_data(data,"test")
            print(checktime.get('expiryTime'))

            expire_timestr = checktime.get('expiryTime')
            expire_time = datetime.strptime(expire_timestr, '%H:%M').time()

            india_timezone = pytz.timezone('Asia/Kolkata')
            india_time = datetime.now(india_timezone)
            formatted_time = india_time.strftime('%H:%M')
            current_time = datetime.now().time()

            current_time = datetime.strptime(formatted_time, '%H:%M').time()


            if current_time > expire_time :
               return {"success":False, "message":"User time is exceeded"}
           


        try:
            students = firebaseconn.get('Students', '')
            students_ids = []

            # verify the signature and then only allow 

            for i in students:
                students_ids.append(i)

            # takes out student parents no for sending attendance and then drop it in the function 
            #qr has the value parents no take the value out and pass it in sendtoparents(number)
            parents_no = 123456890 

            sendtoparents(parents_no)




            if rollno in students_ids:
                attendance_data = {"" + str(date.today()): "Present"}
                result = firebaseconn.patch('/Students/%s/Attendance/%s' % (rollno, subject), attendance_data)
                cap.release()
                cv2.destroyAllWindows()
                return render(request, "submitattendance.html", context={"mymessage": "Attendance Submitted for Roll No : " + rollno, "Flag": "True", "Navigate": "True"})
            else:
                return render(request, "submitattendance.html", context={"mymessage": "Student with this ID does not exist", "Flag": "True", "Navigate": "True"})
        except Exception as e:
            print("Exception:", e)
            pass

        return render(request, "submitattendance.html", context={"mymessage": "Please Connect with admin to create your account", "Flag": "True", "Navigate": "True"})

    return render(request, "submitattendance.html")

def viewhistory(request):

    if request.method == "POST":
        inputroll = request.POST.get('inputroll')
        print(inputroll)
        result=firebaseconn.get('Students/'+inputroll+'/Attendance','')
        print(result)

        if result == None:
            return render(request, "viewhistory.html", context={"mymessage":"Student with this roll no does not exist","Flag":"True"})
        else:
            IOT = []
            CC = []
            IPCV = []
            Other = []
            for i in result:
                if result[i] != "":
                        if i == "IOT":
                            IOT.append(result[i])
                        if i == "CC":
                            CC.append(result[i])
                        if i == "IPCV":
                            IPCV.append(result[i])
                        if i == "Other":
                            Other.append(result[i])
            print(IOT)
            print(CC)
            print(IPCV)
            return render(request, "viewhistory.html",context = {"IOT":IOT, "CC":CC, "IPCV":IPCV,"Other":Other})

    return render(request, "viewhistory.html")




def haversine(lat1, lon1, lat2, lon2):
         lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
         dlat = lat2 - lat1
         dlon = lon2 - lon1
         a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
         c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
         radius = 6371000
    
         distance = radius * c
         return distance

def is_within_500m(user_lat, user_lon, reference_lat, reference_lon):
         distance = haversine(user_lat, user_lon, reference_lat, reference_lon)
         return distance <= 500

def check_proximity(user_lat, user_lon, reference_lat, reference_lon):
          if is_within_500m(user_lat, user_lon, reference_lat, reference_lon):
             return "User is within 500 meters of the reference point."
          else:
             return "User is not within 500 meters of the reference point."

# take referenec or of college 
reference_lat = 12.972778  
reference_lon = 77.595833 



def generate_qr_with_expiry(expiry_time, secret_key):
    data = {
        "expiryTime": expiry_time,  
    }

    data_string = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        secret_key.encode(),
        data_string.encode(),
        hashlib.sha256
    ).hexdigest()

    payload = {
        "data": data,
        "signature": signature
    }

    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()



def adminpanel(request):

    qr_fig = plt.figure(figsize=(5, 5))
    plt.axis('off')
    plt.imshow(Image.open("qrsample.png"))

    imagedata = StringIO()
    qr_fig.savefig(imagedata, format='svg')
    imagedata.seek(0)


    if request.method == "POST":
        inputrollno = request.POST.get('inputrollno')
        inputname = request.POST.get('inputname')
        inputaddress = request.POST.get('inputaddress')
        inputbranch = request.POST.get('inputbranch')
        inputcourse = request.POST.get('inputcourse')
        inputsemester = request.POST.get('inputsemester')
        inputyear = request.POST.get('inputyear')
        inputtime = request.POST.get('expire_time')
        inputnumber = request.POST.get('inputnumber')



        if not inputrollno or not inputname or not inputaddress or not inputbranch or not inputcourse or not inputsemester or not inputyear or not inputtime:
         return HttpResponse("All fields are required. Please provide input for all fields.", status=400)



        print(inputrollno)
        print(inputname)
        print(inputaddress)
        print(inputbranch)
        print(inputcourse)
        print(inputsemester)
        print(inputyear)
        print(inputtime)


        expiry = generate_qr_with_expiry(inputtime,"test")


        #create student id
        basewidth = 100

        wpercent = (basewidth)
        hsize = int(float(wpercent))
        QRcode = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H
        )


        g = geocoder.ip('me') 
        stud_latitude = g.latlng[0]
        stud_longitude = g.latlng[1]

        # save latitude and longitude in db and call the proximity check function to check here reference can be the colkege or eevent live attendance 

        # also we can dump data in db or reference latitude and longitude 

        result = check_proximity(stud_longitude,stud_longitude, reference_lat, reference_lon)

        print(result)
        

        student_details = {
            "name":inputname,
            "rollno":inputrollno,
            "address":inputaddress,
            "branch":inputbranch,
            "course":inputcourse,
            "semester":inputsemester,
            "year":inputyear,
            "mainlatitude":stud_latitude,
            "mainlongitude":stud_longitude,
            "signature":expiry,
            "parentsno":inputnumber
        }

        
        

        QRcode.add_data(student_details)
        QRcode.make()

        QRimg = QRcode.make_image(back_color="white").convert('RGB')

        QRimg.save('studentid.png')

        msg = "Student ID Generated"

        qr_fig = plt.figure(figsize=(5, 5))
        plt.axis('off')
        plt.imshow(Image.open('studentid.png'))

        imagedata = StringIO()
        qr_fig.savefig(imagedata, format='svg')
        imagedata.seek(0)

        print(msg)
        
        attendance_data = {"IOT":"",
        "CC":"",
        "IPCV":"",
        "Other":""
        }

        data = {"RollNo":inputrollno,
        "Name":inputname,
        "Address":inputaddress,
        "Branch":inputbranch,
        "Course":inputcourse,
         "Semester":inputsemester,
         "Year":inputsemester,
         "Attendance":attendance_data}

        try:
            students=firebaseconn.get('Students','')
            students_ids = []

            for i in students:
                students_ids.append(i)

            if inputrollno in students_ids:
                return render(request, "adminpanel.html", context={"msg":"Student with this ID already exist","Flag":"True"})
            else:
                result = firebaseconn.patch('/Students/%s/'%inputrollno,data)
                return render(request, "adminpanel.html", context={"pic":imagedata.getvalue(),"msg":"Details Submitted To DB","Flag":"True"})

        except:
            pass

        result = firebaseconn.patch('/Students/%s/'%inputrollno,data)
        return render(request, "adminpanel.html", context={"pic":imagedata.getvalue(),"msg":"Details Submitted To DB","Flag":"True"})

    return render(request, "adminpanel.html", context={"pic":imagedata.getvalue()})

def editdetails(request):

    if request.method == "POST":
        fieldname = request.POST.get("editfield")
        rollno = request.POST.get('editrollno')
        newvalue = request.POST.get('newvalue')

        print(fieldname)
        print(rollno)

        students=firebaseconn.get('Students',rollno)

        print(students[fieldname])
        

        if fieldname in students[fieldname]:
            return render(request, "editdetails.html", context={"msg":"Student with this ID does not exist","Flag":"True"})
        else:
            result = firebaseconn.patch('/Students/%s/'%rollno,{fieldname:newvalue})
            return render(request, "editdetails.html", context={"msg":"Value Updated in DB","Flag":"True"})

    return render(request, "editdetails.html")

def viewstudenthistory(request):

    if 'generatereport' in request.POST:
        inputrollno = request.POST.get('inputrollno')

        result=firebaseconn.get('Students/'+inputrollno+'/Attendance','')
        print(result)

        if result == None:
            return render(request, "viewstudenthistory.html", context={"mymessage":"Student with this roll no does not exist","Flag":"True"})
        else:
            IOT = []
            CC = []
            IPCV = []
            Other = []
            for i in result:
                if result[i] != "":
                        if i == "IOT":
                            IOT.append(result[i])
                        if i == "CC":
                            CC.append(result[i])
                        if i == "IPCV":
                            IPCV.append(result[i])
                        if i == "Other":
                            Other.append(result[i])


            all_dates = []

            for i in range(31):
                current_date = date.today() + timedelta(days=-i)
                all_dates.append(current_date.strftime("%Y-%m-%d"))
                
            print(all_dates)

            IOT_Attendance = []
            CC_Attendance = []
            IPCV_Attendance = []

            IOT_present_days_count = 0
            CC_present_days_count = 0
            IPCV_present_days_count = 0

            for i in all_dates:
                if i in IOT:
                    IOT_present_days_count += 1
                    IOT_Attendance.append("IOT "+str(i)+" Present")
                else:
                    IOT_Attendance.append("IOT "+str(i)+" Absent")

            for i in all_dates:
                if i in CC:
                    CC_present_days_count += 1
                    CC_Attendance.append("CC "+str(i)+" Present")
                else:
                    CC_Attendance.append("CC "+str(i)+" Absent")

            for i in all_dates:
                if i in IPCV:
                    IPCV_present_days_count += 1
                    IPCV_Attendance.append("IPCV "+str(i)+" Present")
                else:
                    IPCV_Attendance.append("IPCV "+str(i)+" Absent")


            IOT_percentage = (IOT_present_days_count/30) * 100
            CC_percentage = (CC_present_days_count/30) * 100
            IPCV_percentage = (IPCV_present_days_count/30) * 100

            

            subjects = []
            dates = []
            status = []

            wb = Workbook()

            sheet1 = wb.add_sheet('Sheet 1')

            ###

            subjects.clear()
            dates.clear()
            status.clear()

            for i in IOT_Attendance:
                subjects.append(i.split(" ")[0])
                dates.append(i.split(" ")[1])
                status.append(i.split(" ")[2])


            sheet1.write(0, 0, 'Subject')
            sheet1.write(0, 1, 'Dates')
            sheet1.write(0, 2, 'Status')

            for i in range(len(subjects)):
                sheet1.write(i+1,0, subjects[i])
                sheet1.write(i+1,1, dates[i])
                sheet1.write(i+1,2, status[i])

            #################

            subjects.clear()
            dates.clear()
            status.clear()

            for i in CC_Attendance:
                subjects.append(i.split(" ")[0])
                dates.append(i.split(" ")[1])
                status.append(i.split(" ")[2])


            sheet1.write(0, 4, 'Subject')
            sheet1.write(0, 5, 'Dates')
            sheet1.write(0, 6, 'Status')

            for i in range(len(subjects)):
                sheet1.write(i+1,4, subjects[i])
                sheet1.write(i+1,5, dates[i])
                sheet1.write(i+1,6, status[i])

            ###
            subjects.clear()
            dates.clear()
            status.clear()

            for i in IPCV_Attendance:
                subjects.append(i.split(" ")[0])
                dates.append(i.split(" ")[1])
                status.append(i.split(" ")[2])


            sheet1.write(0, 8, 'Subject')
            sheet1.write(0, 9, 'Dates')
            sheet1.write(0, 10, 'Status')

            for i in range(len(subjects)):
                sheet1.write(i+1,8, subjects[i])
                sheet1.write(i+1,9, dates[i])
                sheet1.write(i+1,10, status[i])

            sheet1.write(33,0,"Total Lectures attend in subject IOT : "+str(IOT_present_days_count)+" ")

            sheet1.write(34,0,"Total Lectures attend in subject CC : "+str(CC_present_days_count)+" ")

            sheet1.write(35,0,"Total Lectures attend in subject IPCV : "+str(IPCV_present_days_count)+" ")
            
            ##percentage
            sheet1.write(37,0,"Total Percentage in IOT "+"{0:.2f}%".format(IOT_percentage))

            sheet1.write(38,0,"Total Percentage in CC "+"{0:.2f}%".format(CC_percentage))

            sheet1.write(39,0,"Total Percentage in IPCV "+"{0:.2f}%".format(IPCV_percentage))

            #total percetage
            print("{0:.2f}%".format(IOT_percentage))
            print("{0:.2f}%".format(CC_percentage))
            print("{0:.2f}%".format(IPCV_percentage))

            wb.save('report.xls')

    if 'viewreport' in request.POST:
        inputroll = request.POST.get('inputroll')
        print(inputroll)
        result=firebaseconn.get('Students/'+inputroll+'/Attendance','')

        if result == None:
            return render(request, "viewstudenthistory.html", context={"mymessage":"Student with this roll no does not exist","Flag":"True"})
        else:
            IOT = []
            CC = []
            IPCV = []
            for i in result:
                if result[i] != "":
                        if i == "IOT":
                            IOT.append(result[i])
                        if i == "CC":
                            CC.append(result[i])
                        if i == "IPCV":
                            IPCV.append(result[i])

            print(IOT)
            print(CC)
            print(IPCV)
            return render(request, "viewstudenthistory.html",context = {"IOT":IOT, "CC":CC, "IPCV":IPCV})

    return render(request, "viewstudenthistory.html")