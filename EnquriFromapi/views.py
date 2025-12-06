import json
import os
from pathlib import Path
import time

from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from userManagement.models import *
from rest_framework.views import APIView
from .serializers import *
from rest_framework import viewsets, status
from django.core.mail import EmailMessage
from pathlib import Path
import requests
from Staanenquiryfromwithazure.settings import CURRENT_CLIENT_ID, CURRENT_AUTHORITY

from django.contrib.auth.models import User

from urllib.parse import quote

tenant_id = "2708cf11-c83a-466f-9399-671ebba3e8fc"
Client_ID = "52a3b712-cbab-461d-a03d-a6b234a9ed21"


def send_email(to, pdf_file_paths):
    subject = 'Thanks For Your Visit - STAAN'
    body = """Dear Sir/Madam,

It’s very nice meeting you at conference.

We, STAAN Biomed Engineering Private Limited was established in the year of 2003, as a leading manufacturer of Surgical Operating Tables, Surgical Operating Lights, Anesthesia Workstation, ICU Ventilators, HFNC (High Flow Nasal Cannula), Tourniquet, Surgical Instruments, Critical Care Devices. Our Organisation is an ISO 9001:2015 (Quality Management Systems & Requirements) & EN ISO 13485:2016 (Medical Devices – Quality Management Systems – Requirements) Certified Company.

Also, we do have recognition from world’s leading certification bodies like TUV SUD, ITC, ICR Polaska Co Ltd. And our Class I – Medical Devices are CE marked and US FDA registered. We are doing PAN India supply as a competitive manufacturer and exporter of Medical Devices.

We have successfully completed more than 550 Hospital projects directly and as well as through our dealer network, particularly in Orthopaedics, Gynaecology & Obsterics, Neuro, Vascular, Laparoscopy, Gastroenterology, Spine and General Surgery Operation Theatres and Intensive Care Units.

Please feel free to contact us for your requirements.

STAAN Biomed Engineering Private Limited

+91-98422 19018 | sales@staan.in | www.staan.in
T: +91-422 2533806 | +91-422 2531008 | +91-422 2537440"""
    To = [to]

    # Create an EmailMessage object
    email = EmailMessage(subject, body, 'marketing@staan.in', To)

    BASE_DIR = Path(__file__).resolve().parent.parent
    pdf_path = BASE_DIR / "PDF"

    # Attach multiple PDF files to the email
    for pdf_file_path in pdf_file_paths:
        try:
            # Normalize the path using os.path.join to handle backslashes
            normalized_path = os.path.join(pdf_path, pdf_file_path)

            with open(normalized_path, 'rb') as file:
                file_name = os.path.basename(pdf_file_path)  # Extract file name using os.path.basename
                print(normalized_path, "with base name")
                email.attach(file_name, file.read(), 'application/pdf')
        except Exception as e:
            print(f"Error attaching file {pdf_file_path}: {e}")
    # Send the email 
    try:
        email.send()
        print("Email sent successfully.")
        # print("--->>>5")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_custome_email(to, bcc):
    subject = 'Staan @ Medicall, Hyderabad - 2025'
    body =  """"""
    To = to
    Bcc = bcc
    try:
        # Create an EmailMessage object
        email = EmailMessage(subject, body, 'marketing@staan.in', To, Bcc)
        email.content_subtype = "html"
        email.send()
    except Exception as e:
        print(e)




def log_error(email_address, error_message):
    """Log error messages to a text file."""
    log_file_path = Path(__file__).resolve().parent / "email_errors.txt"
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Error sending email to {email_address}: {error_message}\n")


    

"""To get user Data"""


def get_user_info(access_token):
    graph_api_url = 'https://graph.microsoft.com/v1.0/me'
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(graph_api_url, headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        return user_info
    else:
        # Handle error
        print(f"Error accessing Graph API: {response.status_code}, {response.text}")
        return None


"""Save user Details"""


def create_or_authenticate_user(user_info):
    user_id = user_info.get('id')
    username = user_info.get('displayName')
    email = user_info.get('userPrincipalName')

    existing_user = User.objects.filter(email=email).first()

    if existing_user:

        # User already exists, return the existing user
        return existing_user
    else:
        # User doesn't exist, create a new user
        new_user = User.objects.create_user(username=username, email=email)

        # You can set additional properties or perform other actions here
        return new_user


# Example usage in a Django view
"""To check User """


def Login(request):
    errors = []
    user_data = None
    permission_list = []

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return HttpResponse("Missing or invalid access token. Please contact the administrator.", status=401)

    access_token = auth_header.split('Bearer ')[1]
    user_info = get_user_info(access_token)

    if not user_info:
        return HttpResponse("Access token invalid. Please contact the administrator.", status=401)

    # Authenticate or create user
    user = create_or_authenticate_user(user_info)

    try:
        user_management = UserManagement.objects.get(user=user.id)
    except UserManagement.DoesNotExist:
        return JsonResponse({"success": False, "errors": ["User management data not found."]}, status=404)
    if user_management.profile and user_management.profile.allowed_permission.all().exists():
        for permission in user_management.profile.allowed_permission.all():
            model_name = permission.permission_model.model_name
            for option in permission.permission_options.all():
                permission_list.append(f"{option.options_name}_{model_name}")

        # Now that permissions are confirmed, log in
        django_login(request, user)

        user_data = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "permission": permission_list,
            "userRole": {
                "is_sales_person": user_management.sales_person,
                "is_admin": user_management.admin,
                "is_service": user_management.service
            }
        }

        return JsonResponse({"success": True, "user_info": user_data})
    else:
        errors.append("Admin permission is required. Please contact the administrator.")
        return JsonResponse({"success": False, "errors": errors}, status=403)




"""EnquiryApi get and post """
class EnquiryApi(APIView):

    def get(self, request):
        Enquiry = enquiryDatas.objects.all().order_by('-id')
        # send_custome_email(["dtp@staan.in" ], ['jegathish.e@staan.in', 'drdhanuman@gmail.com', 'murthy.durgi@gmail.com', 'dachepallisunil@gmail.com', 'drsreenivas17@yahoo.com', 'drdsrivanth@gmail.com', 'deepthi.adla@gmail.com', 'shravankumar30@gmail.com', 'drdivisrinivas1966@gmail.com', 'divi.bandari15@gmail.com', 'doddaprsdl@gmail.com', 'eyyunnis@yahoo.co.in', 'edwin.luther@gmall.com', 'etteveeraji@redIffmail.com', 'sisirmig@hotmall.com', 'kishoreroy@yahoo.com', 'rrorthohospital@gmall.com', 'praveengalipalli@gmail.com', 'aparnahospitalrmur@gmail.com', 'drgsreddy@gmail.com', 'kakadegautarn@hotrnall.com', 'gsrpadma@hotmail.com', 'gsrpadma@hotmail.com', 'drgopikrishna28@gmail.com', 'gopinath.bandari@gmail.com', 'chitanyakishorel@gmail.com', 'sbharath78978@gmail.com', 'gkaulaiah@gmail.com', 'shailuhari@gmail.com', 'harrister@gmail.com', 'harishpalvai@gmail.com', 'harshadjawalkar@yahoo.com', 'rkreddymure@gmail.com', 'drramu27@gmail.com', 'drrameshgaripalli@yahoo.co.in', 'rameshkottur@yahoo.com', 'dr_ramesh143@yahoo.co.in', 'breddy22@gmail.com', 'krkreddy2009@gmail.com', 'drorthopaedicianl@gmail.com', 'drranjithkumar@gmail.com', 'thiru.rathna@gmail.com', 'ratnakarorthok@gmail.com', 'drnrkiran@rediffmail.com', 'ravikumarortho@gmail.com', 'bandrapalla@gmail.com', 'ravikanth_375@yahoo.com', 'ravikondepati@gmail.com', 'drravivutukuru@gmail.com', 'anjanikumarkadiri@gmail.com', 'gprkrohit@yahoo.com', 'dr_kostirohit@yahoo.com', 'drkalerohit23@gmail.com', 'rohith.munnull@gmail.com', 'jaiswal_roshan02@gmail.com', 'harikumarsreesailam@yahoo.co.in', 'jagadeeshbabuortho@gmail.com', 'sjatinkumar@yahoo.co.in', 'manay.reddy@gmail.com', 'dr.surendra27@gmail.com', 'drssreddyll@gmail.com', 'drsvrao99@gmail.com', 'ayubortho@gmail.com', 'drvikranth57@gmail.com', 'drsaikirangudala@gmail.com', 'sakethsaketh@gmail.corn', 'sampathv83@gmail.com', 'sandeepsriram29@gmail.com', 'dr.anand.kumar@hotmail.com', 'nandakadichary@gmail.com', 'drnsreddy67@gmail.com', 'nagireddy.ortho@gmail.com', 'nsreemanrao@gmail.com', 'drnnraj@gmail.com', 'narasimharao.thutari@gmail.com', 'prasad_peruri@yahoo.com', 'narsimludyavarashetty@yahoo.com', 'drmncreddy@gmail.com', 'naveengujjeti@gmail.com', 'drnaveen@gmail.com', 'naveenpreddy@gmail.com', 'naveenahanchatey@gmail.com', 'neelamramana@yahoo.com', 'dr.ahmednishat@gmail.com', 'omprakash.tumma@gmail.com', 'pallasukarna@gmail.com', 'pvc_reddy200@yahoo.com', 'amitred@yahoo.com', 'urfracturedoctor@gmail.com', 'prem.pooldandikar@gmail.com', 'anurag_ortho@yahoo.co.in', 'prangachari@yahoo.com', 'drgnaneswar@gmail.com', 'drjportho@yahoo.com', 'sudheerdwarak@gmail.com', 'dr.sadhanpalakuri@gmail.com', 'npu33@gmail.com', 'drkprpagadala@gmail.com', 'anil.palakolanu@gmail.com', 'dr.paragparadkar@gmail.com', 'drplsvas@yahoo.co.in', 'mohanpasham@gmail.com', 'pavansarma007@gmail.com', 'drpawanortho@gmail.com', 'sudhirdr9@gmail.com', 'docsuri.reddy@outlook.com', 'bvrschalla@gmail.com', 'drtimpu@gmail.com', 'ksudhirreddy@hotmail.com', 'vrsujitkumar@gmail.com', 'sukeshrao.sankineni@gmail.com', 'sukumar_chaya@yahoo.co.in', 'sumankalyanm@gmail.com', 'suman_ortho@rediffmail.com', 'sunil.alishalams@gmail.com', 'apsingi@gmail.com', 'soori.dr@gmail.com', 'sureshpadya@gmail.com', 'drsureshsankaramaddi@gmail.com', 'vsprao@rediffmail.com', 'mvsushanth@gmail.com', 'goud_rajeshkumar@yahoo.co.in', 'rtndrvijendra@gmail.com', 'tandra.1960@gmail.com', 'drtpsnaik@gmail.com', 'sreedhar_thuppal@yahoo.co.in', 'sreedhar_thuppal@yahoo.co.in', '9440015225ramu_ti@yahoo.com', 'drramanababu@gmail.corn', 'myneniuday@gmail.com', 'prasadvkv@gmail.com', 'ashok_vishwanath@hotmail.com', 'ashok_vishwanath@hotmail.com', 'vemaganti.prasad@gmail.com', 'vbraju_66@yahoo.co.in', 'drvprashanth@gmail.com', 'ramreddyvenuthurla@gmail.com', 'vootukuru.s.reddy@gmail.com', 'drvsnraju@gmail.com', 'drvrakesh09@yahoo.com', 'svallam@ymail.corn', 'drvamshikiran@gmail.com', 'vannelaashok@gmail.com', 'drsastri@yahoo.com', 'varuntandra@gmail.com', 'surenderortho@gmail.com', 'juvvadi.dev@gmail.com', 'vpraman04@gmail.com', 'docveda@yahoo.com', 'lara.gunda@gmail.com', 'sat_veera@yahoo.co.in', 'shekarvemula@yahoo.com', 'muralidrvemula@yahoo.co.in', 'drvenkees@gmail.corn', 'venky29091966@yahoo.co.in', 'vrpdr08@gmail.com', 'drvenkatreddy216@gmail.com', 'venkatreddy78@gmail.com', 'vboorgula@gmail.com', 'venuortho1966@gmail.com', 'venu2kl@gmail.com', 'drragi@yahoo.com', 'drjvsvidyasagar@gmail.com', 'dr.gvijaykumar@gmail.com', 'vijayorthoosm@gmail.com', 'dr.vijaykumarloya@gmail.com', 'vjreddy23@gmail.com', 'drviJayreddy.ms@gmail.com', 'ramarao47@gmail.com', 'drvipin_bbr@yahoo.coin', 'mahadevuni.vishwanath206@gmall.com', 'visu345@rediffmall.com', 'drsunaidu@rediffmall.com', 'vivekmekala@yahoo.com', 'bvivananddr@rediffmail.com', 'drvraman@gmail.com', 'wrsrao@gmail.com', 'nbrekha226@gmail.com', 'yprabhakar106@gmail.com', 'reddemrk@gmail.com', 'ramgopalmahesh@yahoo.co.in', 'shekarramineni9969@gmail.com', 'rahulkanumuri9@gmail.com', 'rahulkuraganti@gmail.com', 'rahulrai_22@yahoo.com', 'adishankar.perla@gmail.com', 'joshuaswarupa@yahoo.com', 'bpdheer@gmail.com', 'drpradeepchandra@gmail.com', 'dbpurprak@yahoo.co.in', 'prasadpnvsv@hotmail.com', 'praveenraoortho@gmail.com', 'p.mereddy@yahoo.com', 'bandipraveen8@gmail.com', 'dr_chavanjaikrishna@yahoo.co.in', 'rprajputta@gmail.com', 'sunee1705@gmail.com', 'karthikreddyratna@gmail.com', 'sreedharrakasi@gmail.com', 'dr_srikanthvarma@yahoo.co.in', 'dr.nagender.rachakonda@gmail.com', 'bpreddy@rediffmail.com', 'surgeonrk@yahoo.com', 'drrapaka@yahoo.com', 'rdmuluk@gmail.com', 'ragz0000@gmail.com', 'raghuveer3@rediffmail.com', 'ragiprasad@gmail.com', 'rajkollam@yahoo.co.in', 'komeravelli@yahoo.com', 'rajashekarkandi@gmail.com', 'rajesh.vanajesh@gmail.com', 'rajesh.reddy44@gmail.com', 'vishwanathrajesh@yahoo.com', 'rajuayengar@rediffmail.com', 'dr.rakeshreddy@yahoo.com', 'rakeshreddymandala99@gmail.com', 'stanly@staan.in', 'antony@staan.in', 'sagayaraj@staan.in', 'martin.a@staan.in', 'madhu.t@staan.in'])
        # print("sent completed.")
        serializer_datas = EnquirySerializers(Enquiry, many=True)

        return Response(serializer_datas.data)

    def post(self, request):
        data_dict = request.data.copy()
        try:
            data_dict['Interesteds'] = data_dict.pop('Interesteds[]')[0]
        except:
            pass
        serializer = EnquirySerializers(data=data_dict)

        if serializer.is_valid():
            serializer.save()
            email_value = serializer.validated_data.get('Email')
            intrested = serializer.validated_data.get('Interesteds')
            BASE_DIR = Path(__file__).resolve().parent.parent
            pdf_path = BASE_DIR / "PDF"
            intrested_list = []
            for data in (intrested):
                data = str(data) + ".pdf"
                intrested_list.append(pdf_path / str(data))
            try:
                send_email(request, email_value, intrested_list)
            except Exception as e:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""EnquiryApi get and  and Put """
class EnquiryDetails(APIView):
    def get_object(self, pk):
        try:
            return enquiryDatas.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = EnquirySerializers(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = EnquirySerializers(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""productDetails get and post """


class productApi(APIView):
    def get(self, request):
        product_ = product.objects.all()
 
        serializer_datas = productSerializers(product_, many=True)

        return Response(serializer_datas.data)

    def post(self, request):
        serializer = productSerializers(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""productDetails get and  put and delete """


class productDetails(APIView):
    def get_object(self, pk):
        try:
            return product.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = productSerializers(article)
        return Response(serialzer.data)


"""conferenceApi get and post """


class conferenceApi(APIView):
    def get(self, request):
        Conference_ = Conferencedata.objects.all().order_by('-id')
        # print(Conference_)
        serializer_datas = ConferenceSerializers(Conference_, many=True)

        return Response(serializer_datas.data)

    def post(self, request):
        serializer = ConferenceSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""conferenceDetails get and  put and delete """


class conferenceDetails(APIView):
    def get_object(self, pk):
        try:
            return Conferencedata.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ConferenceSerializers(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        print(request)
        article = self.get_object(pk)
        serializer = ConferenceSerializers(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        article = self.get_object(pk)
        try:
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            # If the deletion is protected, handle the exception

            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""user get"""


class passUser(APIView):
    def get(self, request):
        User_ = User.objects.all()
        serializer_datas = userSerializer(User_, many=True)

        return Response(serializer_datas.data)


@login_required(login_url='unauthorized')
def dashboard(request):
    return render(request, 'dashboard.html')

def unauthorized(request):
    return render(request, 'unauthorized.html')


def send_email_persnal():
    access_token = ""
    to_email =  "antony@staan.in"
    subject = "test mail"
    body_content = "only for test---- final  last"
    graph_api_url = 'https://graph.microsoft.com/v1.0/me/sendMail'
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",  # "HTML" if you want to send an HTML email
                "content": body_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email
                    }
                }
            ]
        }
    }

    # Send the email via the Graph API
    response = requests.post(graph_api_url, headers=headers, data=json.dumps(email_data))

    if response.status_code == 202:
        # get_sent_email_id(access_token)
        print("Email sent successfully!")
    else:
        print(f"Error sending email: {response.status_code} - {response.text}")
    try:
        response_json = response.json()
        print("Response JSON: ", response_json)
    except ValueError:  # JSONDecodeError is a subclass of ValueError
        print("Response is not in JSON format.")
        print(f"Response Text: {response.text}")


def get_sent_email_id(access_token):
    # Fetch the latest sent email from the 'sent' folder
    sent_folder_url = 'https://graph.microsoft.com/v1.0/me/messages'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(sent_folder_url, headers=headers)

    if response.status_code == 200:
        emails = response.json().get('value', [])
        if emails:
            # Get the ID of the most recent sent email
            message_id = emails[0].get('id')
            print(f"Most recent sent email ID: {message_id}")
            print("emails[0]", emails[0])
            return message_id
        else:
            print("No sent emails found.")
            return None
    else:
        print(f"Error fetching sent emails: {response.status_code} - {response.text}")
        return None

def get_sent_emails():
    # Microsoft Graph API URL to get sent items
    access_token =""
    graph_api_url = 'https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Send GET request to retrieve the sent messages
    response = requests.get(graph_api_url, headers=headers)

    # if response.status_code == 200:
    #     sent_emails = response.json() 
    #     for email in sent_emails['value']:
    #         print(email)
    #         print(f"{email['id']}")
    #         print(f"Subject: {email['subject']}")
    #         print(f"Sender: {email['from']['emailAddress']['address']}")
    #         print(f"Sent Date: {email['sentDateTime']}")
    #         print(f"Body: {email['body']['content'][:100]}...")  # Print first 100 characters of the body
    #         print("-" * 50)  # Separator between emails
    # else:
    #     print(f"Error retrieving sent emails: {response.status_code} - {response.text}")

def get_email_by_id(access_token):
    graph_api_url = f'https://graph.microsoft.com/v1.0/me/messages/AAMkADgyNzcyMTllLWMyZDUtNGMyNC1iMTEyLTY0ODcyOTg2YTFjMABGAAAAAABnlWTe8zeYQKhtEoiy1ZFNBwB6pohXiYsySoJxaEkBPlxSAAAAAAEJAAB6pohXiYsySoJxaEkBPlxSAAFhaUZSAAA='

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(graph_api_url, headers=headers)

    if response.status_code == 200:
        email = response.json()
        print(f"Subject: {email['subject']}")
        print(f"From: {email['from']['emailAddress']['address']}")
        print(f"Body: {email['body']['content']}")
    else:
        print(f"Error retrieving the email: {response.status_code} - {response.text}")


WHATS_APP_URL =f"https://live-mt-server.wati.io/439643/api/v2/sendTemplateMessages"
HEADERS = {
            "Content-Type": "application/json-patch+json",
            "accept": "*/*",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhZTMxY2JmNy04ZWQ3LTRjZWItODc2Ny1lOTYwZjE0NWUzNGEiLCJ1bmlxdWVfbmFtZSI6InN1ZGFyc2hhbi5iQHN0YWFuLmluIiwibmFtZWlkIjoic3VkYXJzaGFuLmJAc3RhYW4uaW4iLCJlbWFpbCI6InN1ZGFyc2hhbi5iQHN0YWFuLmluIiwiYXV0aF90aW1lIjoiMDUvMDgvMjAyNSAwNzozMjo0NyIsInRlbmFudF9pZCI6IjQzOTY0MyIsImRiX25hbWUiOiJtdC1wcm9kLVRlbmFudHMiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBRE1JTklTVFJBVE9SIiwiZXhwIjoyNTM0MDIzMDA4MDAsImlzcyI6IkNsYXJlX0FJIiwiYXVkIjoiQ2xhcmVfQUkifQ.-B5NJYv1OpEvKG5b6Il8e0Dt9MrvWPJQucqENE5kOH8"
        }
def sendWhatsApp(name, number, conference):
    whatsApp_number = str(number).replace("+","")
    payload = {'template_name': 'conference_promotion', 'broadcast_name': 'conference_promotion',
            'receivers': [{'whatsappNumber': whatsApp_number, 'customParams': [{'name': 'Name', 'value': f"{name}"}, {'name': 'conference', 'value': f"{conference}"},
            {'name': 'image', 'value': 'https://conferencemarketing.s3.ap-south-1.amazonaws.com/Medicall2025_Chennai_Promotion.jpg'}]}]}

    response = requests.post(WHATS_APP_URL, json=payload , headers=HEADERS)

class WhatsAppSendApi(APIView):
    def post(self, request):
        payload_data = request.data.get("payload",None)
        file_type = request.data.get("fileType",None)
        bulk_message = request.data.get("bulkMessage", None)

        # Validate `bulkMessage` is explicitly provided
        if bulk_message is None:
            return Response(
                {"error": "'bulkMessage' field is required and must be either true or false."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
       
        if file_type == "img":
            payload ={
                "template_name": "staan_image_template" if bulk_message else "staan_comman_image_template",
                "broadcast_name": "staan_image_template" if bulk_message else "staan_comman_image_template",
                "receivers": payload_data
            }
        elif file_type == "doc":
            payload ={
                "template_name": "staan_document_template" if bulk_message else "staan_comman_document_template",
                "broadcast_name": "staan_document_template" if bulk_message else "staan_comman_document_template",
                "receivers": payload_data
            }
        else:
            payload ={
                "template_name": "staan_text_template" if bulk_message else "staan_com_txt_template",
                "broadcast_name": "staan_text_template" if bulk_message else "staan_com_txt_template",
                "receivers": payload_data
            } 
        try:
            response = requests.post(WHATS_APP_URL, json=payload, headers=HEADERS)
            # Print Request Info
            print("===== REQUEST =====")
            print(f"URL: {response.request.url}")
            print(f"Method: {response.request.method}")
            print(f"Headers: {response.request.headers}")
            print(f"Body: {response.request.body}")

            # Print Response Info
            print("===== RESPONSE =====")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Body: {response.text}")
        except Exception as e:
            print(e)
        
        return Response(response, status=200)


class WhatsAppChatApi(APIView):
    def post(self, request):
        whatsNum = request.data.get("whatsNum", None)
        pageSize = request.data.get("pageSize", 50)
        pageNumber = request.data.get("pageNumber", 1)

        if not whatsNum:
            return Response({"error": "whatsNum is required"}, status=400)

        # Safely encode the phone number for use in the URL path
        encoded_whatsNum = quote(whatsNum)

        # Construct the final URL with path and query parameters
        url = f"https://live-mt-server.wati.io/439643/api/v1/getMessages/{encoded_whatsNum}?pageSize={pageSize}&pageNumber={pageNumber}"
        print("Request URL:", url)

        headers={
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhZTMxY2JmNy04ZWQ3LTRjZWItODc2Ny1lOTYwZjE0NWUzNGEiLCJ1bmlxdWVfbmFtZSI6InN1ZGFyc2hhbi5iQHN0YWFuLmluIiwibmFtZWlkIjoic3VkYXJzaGFuLmJAc3RhYW4uaW4iLCJlbWFpbCI6InN1ZGFyc2hhbi5iQHN0YWFuLmluIiwiYXV0aF90aW1lIjoiMDUvMDgvMjAyNSAwNzozMjo0NyIsInRlbmFudF9pZCI6IjQzOTY0MyIsImRiX25hbWUiOiJtdC1wcm9kLVRlbmFudHMiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBRE1JTklTVFJBVE9SIiwiZXhwIjoyNTM0MDIzMDA4MDAsImlzcyI6IkNsYXJlX0FJIiwiYXVkIjoiQ2xhcmVfQUkifQ.-B5NJYv1OpEvKG5b6Il8e0Dt9MrvWPJQucqENE5kOH8"
        }

        try:
            response = requests.get(url, headers=headers)
            print("response",response)
            return Response(response.json(), status=response.status_code)
        except Exception as e:
            print("e",e)
            return Response({"error": str(e)}, status=500)
        


class WhatsAppFileDownload(APIView):
    def post(self, request):
        whatsfile = request.data.get("file_name", None)

        if not whatsfile:
            return Response({"error": "File is required"}, status=400)

        # Safely encode the phone number for use in the URL path
        encoded_whatsFile = quote(whatsfile)
        # Construct the final URL with path and query parameters
        url = f"https://live-mt-server.wati.io/439643/api/v1/getMedia?fileName={encoded_whatsFile}"
        print("Request URL:", url)

        headers={
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhZTMxY2JmNy04ZWQ3LTRjZWItODc2Ny1lOTYwZjE0NWUzNGEiLCJ1bmlxdWVfbmFtZSI6InN1ZGFyc2hhbi5iQHN0YWFuLmluIiwibmFtZWlkIjoic3VkYXJzaGFuLmJAc3RhYW4uaW4iLCJlbWFpbCI6InN1ZGFyc2hhbi5iQHN0YWFuLmluIiwiYXV0aF90aW1lIjoiMDUvMDgvMjAyNSAwNzozMjo0NyIsInRlbmFudF9pZCI6IjQzOTY0MyIsImRiX25hbWUiOiJtdC1wcm9kLVRlbmFudHMiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBRE1JTklTVFJBVE9SIiwiZXhwIjoyNTM0MDIzMDA4MDAsImlzcyI6IkNsYXJlX0FJIiwiYXVkIjoiQ2xhcmVfQUkifQ.-B5NJYv1OpEvKG5b6Il8e0Dt9MrvWPJQucqENE5kOH8"
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                filename = whatsfile.split('/')[-1]
                return HttpResponse(
                    response.content,
                    content_type=content_type,  # e.g. "image/jpeg" or "application/pdf"
                    headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                    }
                )
            else:
                return Response({"error": "Failed to download file"}, status=response.status_code)
        except Exception as e:
            print("e", e)
            return Response({"error": str(e)}, status=500)
