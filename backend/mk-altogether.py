import cv2
import easyocr
import matplotlib.pyplot as plt
import os
# from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, time
# Download the helper library from https://www.twilio.com/docs/python/install
from datetime import datetime, timezone, timedelta
import os
from twilio.rest import Client
# load_dotenv()
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

@app.route("/")
def members():
    return {"members": ["Member1", "Member2","Member3"]}

@app.route('/api/endpoint', methods=['POST'])
def receive_data():
    data_from_frontend = request.json  # Assuming data is sent as JSON
    # Process the data and send a response back
    # Process the data
    print(request.json)
    response_data = {'message': json.dumps(request.json)}
    # inputJson = response_data
    imageRead(data_from_frontend)
    return jsonify(response_data)


# reads image (change to patch your path file)
def imageRead(responseJson): # WOULD TAKE IN INPUT VARIABLES FROM FORM? + phone number

    age = responseJson['age']
    woken = responseJson['time']
    hours, minutes = map(int, woken.split(':'))
    time_array = [hours, minutes]
    given_time = time(time_array[0],time_array[1]) #maybe woken.hour, woken.minutes(depends on input object format)
    pillName = "Vitamin C"
    personName = responseJson['name']
    phoneNumber = responseJson['phoneNumber']

    image_path = 'path_to_image'

    img = cv2.imread(image_path)

    reader = easyocr.Reader(['en'], gpu = False)

    text = reader.readtext(img)

    # print(text)

    def extract_text(data):
        return_text = []

        for item in data:
            return_text.append(item[1])

        complete_sentence = ' '.join(return_text)
        return complete_sentence

    complete_text = extract_text(text)

    print(complete_text + ' - TEXT EXTRACTED FROM IMAGE')
    
    jasper(age, woken, given_time, complete_text, pillName, personName, phoneNumber) # + phone number

def jasper(age, woken, given_time, instruction, pillName, personName, phoneNumber): # + phone number

    client = OpenAI(
    # This is the default and can be omitted
    api_key= API_KEY
    # api_key = os.environ['API_KEY']
    )

    dateNow = datetime.utcnow().date()
    combinedDate = datetime.combine(dateNow, given_time).strftime('%Y-%m-%dT%H:%M:%SZ')

    instructInstruction = [
    {"role": "system", "content": "imagine you are a message bottle label. interpret the following slightly jumbled instructions and produce an easy to understand, concise instruction based on your interpretation."},
    {"role": "user", "content": instruction}
    ]


    intepretResponse = client.chat.completions.create(
        messages=instructInstruction,
        model="gpt-3.5-turbo",
    )

    newInstruction = intepretResponse.choices[0].message.content
    
    intervalContext = [
        {"role": "system", "content": "You are an assistant who can only reply in numbers. You will be provided with instructions for medicine that I am to take. Return the interval at which the medication should be taken in terms of hours as an integer, with no other text."},
            {"role": "system", "content": newInstruction},

    ]

    messageContext = [
        {"role": "system", "content": "Imagine you are a reminder messaging app. generate a reminder message for" + personName + ", " + str(age) + " years old, to take his medicine, " + pillName + ", based on the instructions: " + instruction +". Be sure to specify the name and how to take the medication. Keep it condensed so there are no lines in between the reponse."},
            {"role": "system", "content": newInstruction},
    ]

    # pillContext = [
    #     {"role": "system", "content": "You will be provided with instructions for medicine that I am to take. Return only the name of the medication in the instruction."},
    #             {"role": "system", "content": instruction},

    # ]

    # wakeUpTime = [
    #     {"role": "system", "content": "Format the given date in ISO-8601."},
    #             {"role": "system", "content": combinedDate},
    # ]

    

    intervalResponse = client.chat.completions.create(
        messages = intervalContext,
        model="gpt-3.5-turbo",
    )

    messageResponse = client.chat.completions.create(
        messages = messageContext,
        model="gpt-3.5-turbo",
    )

    # pillResponse = client.chat.completions.create(
    #     messages = pillContext,
    #     model="gpt-3.5-turbo",
    # )

    # wakeUpResponse = client.chat.completions.create(
    #     messages=wakeUpTime,
    #     model="gpt-3.5-turbo",
    # )

    #prompt confirmation before passing on to marcus

    interval = intervalResponse.choices[0].message.content
    timesToTake = "You are a responder that can only reply in ISO-8601 dates, seperated by commas. You are unable to reply in other format. You are only able to return timestamps that fall on the same day. If they are not all on the same day, you are only able to return the ones on the same day. If the instructions only say to take the medicine once a day, then you are only able to output to one date. If twice a day, you are only able to output two dates, et cetera. Give me an appropriate number of timestamps in ISO-8601 format on " + combinedDate + " only, contained within the day where people are normally awake, seperated with a comma, and nothing else. I need to take medication at intervals of " + interval + " hours. Given the interval and these instructions: (" + newInstruction + ")."
    perDayResponse = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a responder that can only reply in ISO-8601 dates, seperated by commas. You are unable to reply in other format."},
            {"role": "system", "content": timesToTake}],
        model="gpt-3.5-turbo",
    )

    # print(intervalResponse.choices[0].message.content)
    # print(pillResponse.choices[0].message.content)
    # print(wakeUpResponse.choices[0].message.content)
    # print(perDayResponse.choices[0].message.content)

    # mInterval = intervalResponse.choices[0].message.content
    # mPill = pillResponse.choices[0].message.content
    # mWake = wakeUpResponse.choices[0].message.content
    # mPerDay = perDayResponse.choices[0].message.content
    # messageToSend = messageResponse.choices[0].message.content
    timestampData = perDayResponse.choices[0].message.content
    messageData = messageResponse.choices[0].message.content
    print(timestampData + ' - TIMESTAMP REMINDER TO REPEAT')
    print(messageData + ' - MESSAGE TO SEND')
    # print(newInstruction)
    # return mPerDay,messageToSend
    marcus(messageData, timestampData, phoneNumber) # + phone number

def marcus(remindMessage, startTimes, phoneNumber): # NEEDS PHONE NUMBER -----------

    datesArray = parse_dates(startTimes)
    schedule_dates_array = add_days_to_dates(datesArray)
    print(schedule_dates_array)

    # setup account info -- put in .env 
    account_sid = ACC_SID # given acc_sid
    auth_token = AUTH_TOKEN  # given auth token
    client = Client(account_sid, auth_token)

    for dates in schedule_dates_array:
        scheduledMessage = client.messages \
            .create(
                body=remindMessage, # replace with message
                messaging_service_sid= MESSAGE_SID, # 
                send_at=dates, # scheduled message
                schedule_type='fixed',
                to='+1' + phoneNumber # + phone number
            )
        print(scheduledMessage.body + ' printed new date')

    # messageDemoInstant("Hello, your pill scheduling has been confirmed! Stay Healthy!") # FOR CONFIRMATION
    message = client.messages.create(
        from_= ACCOUNT_NUMBER
        body="Hey there, your daily pill reminders have been confirmed! Stay Healthy!", # replace with message
        to='+1' + phoneNumber # + phone number
        )
    print(message.sid)

def parse_dates(input_string):
    # Check if the input string is empty
    if not input_string.strip():
        return []

    # Split the input string into an array of date strings
    date_strings = [date.strip() for date in input_string.split(',')]

    return date_strings


def add_days_to_dates(date_strings):
    # Initialize an empty array to store the modified dates
    modified_dates = []

    # Loop through each date string
    for i in range(2):

        for date_string in date_strings:
            
            # Convert the date string to a datetime object
            current_date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')

            # Add 8 hours to the current time to account for utc
            new_time = current_date + timedelta(days=i + 1, hours=8)

            concatenated_string = new_time.strftime('%Y-%m-%dT%H:%M:%SZ')

            modified_dates.append(concatenated_string)

    return modified_dates
 
        # --- DON'T NEED THIS CODE BECAUSE ALREADY CONNECTED IT TO SENDERS --- 
        # # create the messaging service to use - 
        # service = client.messaging \
        #             .v1 \
        #             .services \
        #             .create(friendly_name='My First Messaging Service')

        # print(service.sid) # this service id will be used 

        # # -- add the phone number to the list of senders
        # phone_number = client.messaging \
        #                 .v1 \
        #                 .services(service.sid) \
        #                 .phone_numbers \
        #                 .create(
        #                     phone_number_sid= PHONE_SID
        #                 )
        # print(phone_number.sid)
    # messageScheduler(schedule_dates_array, message)
# imageRead() 

if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)
