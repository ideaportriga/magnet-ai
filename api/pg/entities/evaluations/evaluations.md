```json
{
  "_id": {
    "$oid": "673ee4b1e8da1b2132586c50"
  },
  "job_id": "673ee4b0e8da1b2132586c4f",
  "type": "prompt_eval",
  "tool": {
    "id": "66041f6c714e34857399edfe",
    "name": "Siebel Demo - Categorize",
    "description": "Siebel Demo - Categorize",
    "system_name": "sbl_demo_categorize",
    "variant_name": "variant_1",
    "variant_object": {
      "variant": "variant_1",
      "model": "gpt-4o",
      "temperature": 0.75,
      "text": "You are the AI agent working as a customer service representative. \n\nThe user will provide you with the three inputs:\n\n{CUSTOMER EMAIL} - the content of inbound  email containing customer's request\n{SENTIMENT_LOV} - List of values for setting Sentiment value\n{REQUEST_TYPE_LOV} -  List of values for setting Request Type value\n\nYour job is to analyse {CUSTOMER EMAIL} and create a JSON object with the four parameters below. Output must be formatted as plain text, not as markdown. \n\n\"Summary\" Summarise the background of the customer enquiry. Make sure you capture all essential details about their enquire. Don't mention customer's name.\n\n\"SR Title\" Create a concise name for this customer request.\n\n\"SR Type\" Select semantically the closest value from the list provided by the user in {REQUEST_TYPE_LOV} \n\n\"Sentiment\" Classify email sentiment using the values from the list provided by the user in {SENTIMENT_LOV}\n\n\"Summary\" and \"SR Title\" should be in the English language.",
      "topP": 1,
      "id": "66041f6c714e34857399edfe",
      "sample_text": "{\n\"CUSTOMER EMAIL\":\"Dear BestTVService Team,\nI hope this finds you well.\nI have encountered an issue with logging into the customer portal. It appears that I've forgotten my password.\nCould you please advise me on the steps I need to take to reset my password and regain access?\nMany thanks\",\n\"SENTIMENT_LOV\": (\"Positive\",\"Neutral\",\"Negative\"),\n\"REQUEST_TYPE_LOV\" : (\"Account Access\",\"General Knowledge\",\"Billing and Payments\",\"Subscription Management\")\n}",
      "response_format": {
        "type": "json_object"
      }
    }
  },
  "test_sets": [
    "AIR_CASES"
  ],
  "started_at": {
    "$date": "2024-11-21T07:43:45.642Z"
  },
  "status": "completed",
  "errors": [],
  "finished_at": {
    "$date": "2024-11-21T07:43:56.230Z"
  },
  "results": [
    {
      "id": "d6566949-d7ec-417e-99a6-ecda5786e9d6",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 74,
        "prompt_tokens": 274
      },
      "latency": 1892.018,
      "generated_output": "{\n    \"Summary\": \"The customer is inquiring about the differences between adding extra check-in luggage and adding scuba equipment luggage. They also want to know the weight allowance for scuba equipment luggage.\",\n    \"SR Title\": \"Inquiry about Luggage and Scuba Equipment Allowances\",\n    \"SR Type\": \"Information Request\",\n    \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:49.318Z"
      },
      "expected_output": "",
      "user_message": "Message: Hello, I would like to ask what is the difference between adding an extra check-in luggage vs. adding a scuba equipment luggage? How heavy is the scuba equipment luggage allowed to be? Thank you very much. *FULL NAME*",
      "iteration": 1
    },
    {
      "id": "68b0a7cd-f8b7-4109-b5a2-3fbe8b555fdf",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 94,
        "prompt_tokens": 307
      },
      "latency": 2116.199,
      "generated_output": "{\n  \"Summary\": \"The customer inquires about upgrading baggage allowance from 10 kg to 20 kg for some passengers on their booking. They seek clarification on whether this involves adding extra baggage or if it results in an additional 20 kg bag on top of the existing 10 kg for each passenger.\",\n  \"SR Title\": \"Baggage Upgrade Inquiry\",\n  \"SR Type\": \"Baggage Inquiry\",\n  \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:49.538Z"
      },
      "expected_output": "",
      "user_message": "Booking Reference: *BOOKING REFERENCE* Message: Hi, I need to upgrade my baggage from 10 kg to 20 kg for some passengers on this booking. Do I do this by just adding extra baggage or does add an extra separate 20 kg bag on top of the 10 kg I already have for each passenger. Any help you could give with regards to this would be greatly appreciated.",
      "iteration": 1,
      "score": 4
    },
    {
      "id": "43bb6e64-1753-4b51-a166-ff06731ba4d9",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 62,
        "prompt_tokens": 265
      },
      "latency": 2133.6949999999997,
      "generated_output": "{\n  \"Summary\": \"The customer is inquiring about the addition of their upcoming flights to their KM rewards account and has provided their booking reference.\",\n  \"SR Title\": \"Inquiry about KM rewards account flight addition\",\n  \"SR Type\": \"Account Inquiry\",\n  \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:49.565Z"
      },
      "expected_output": "",
      "user_message": "Hi there, I just wanted to check that my upcoming flights will be added to my KM rewards account? Booking Ref *BOOKING REFERENCE* *FULL NAME* Many thanks *FIRST NAME*",
      "iteration": 1
    },
    {
      "id": "cb2ea58f-5ac0-421c-b3a7-77480e6e2bdc",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 69,
        "prompt_tokens": 280
      },
      "latency": 2285.429,
      "generated_output": "{\n\"Summary\": \"The customer is requesting an invoice for a company trip they took on a specified date. They have not yet received the invoice and are asking for it to be sent to their provided email address.\",\n\"SR Title\": \"Request for Missing Invoice\",\n\"SR Type\": \"Invoice Request\",\n\"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:49.710Z"
      },
      "expected_output": "",
      "user_message": "Message: Hello, We have travelled with our company *DATE*. our names are *FULL NAME* and *FULL NAME*. Could you please send us the invoice please, we didn't received it in *DATE* The email is *EMAIL* Thank you very much Best regards",
      "iteration": 1
    },
    {
      "id": "84e0d11d-97a7-4e0e-9969-f1dd593d8a30",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 128,
        "prompt_tokens": 348
      },
      "latency": 2995.887,
      "generated_output": "{\n  \"Summary\": \"The customer called on a specific date to address an issue with not receiving their booking code and to add hold baggage. The booking code issue was resolved, but the hold baggage was not added. Despite being informed over the phone that everything was successful, the customer still does not see hold baggage added in 'My Booking' and no payment has been deducted. The customer wants to know if the checked baggage will be credited and when.\",\n  \"SR Title\": \"Issue with Adding Hold Baggage to Booking\",\n  \"SR Type\": \"Baggage Inquiry\",\n  \"Sentiment\": \"Concerned\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:50.419Z"
      },
      "expected_output": "",
      "user_message": "Passenger Name: *FULL NAME* Booking Reference: *BOOKING REFERENCE* Message: Dear Sir or Madam, On *DATE*, I called you about not getting my booking code and adding hold baggage. The booking code was successful, but the hold baggage was not. During this call we added hold baggage over the phone and were told that everything was successful. Now, when I go to 'My Booking', I see that still no hold baggage has been added and no money has been deducted. My question is, will our checked baggage be credited and if so, when? Sincerely, *FULL NAME*",
      "iteration": 1
    },
    {
      "id": "5776395e-8849-4a82-9f8a-a1aed067237b",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 75,
        "prompt_tokens": 294
      },
      "latency": 2270.787,
      "generated_output": "{\n\"Summary\": \"The customer has had their booking canceled and has been informed that a 25% refund is being processed. They require a confirmation of the cancellation for travel insurance purposes and have requested that this confirmation be sent to their email.\",\n\"SR Title\": \"Request for Cancellation Confirmation\",\n\"SR Type\": \"Cancellation Confirmation\",\n\"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:52.778Z"
      },
      "expected_output": "",
      "user_message": "Passenger Name: *FULL NAME* Booking Reference: *BOOKING REFERENCE* Message: This booking have been cancelled and a refund (of 25%) is on its way. I do need a confirmation that this have been cancelled, though. For my travel insurance. Can you send a confirmation of the cancellation on *EMAIL*, please?",
      "iteration": 1
    },
    {
      "id": "032ba48e-ccbe-4582-8c4e-4089b4b61793",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 77,
        "prompt_tokens": 301
      },
      "latency": 2693.228,
      "generated_output": "{\n  \"Summary\": \"The customer booked a flight with luggage for a colleague but had to pay for the luggage again at the airport, resulting in a double payment. They were redirected to the airline for a refund request.\",\n  \"SR Title\": \"Double Payment for Luggage Refund Request\",\n  \"SR Type\": \"Refund Request\",\n  \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:53.201Z"
      },
      "expected_output": "",
      "user_message": "Booking Reference: *BOOKING REFERENCE* Message: Dear *AIRLINE* Team, we booked a flight with luggage for our colleague *FULL NAME* via *EMAIL*. Unfortunately, he needed to pay for his luggage again at the airport. So we paid twice for his bag. After reaching out to *EMAIL* they sent us to you. Could you please refund?",
      "iteration": 1
    },
    {
      "id": "bfa3ee1d-4ed1-44cf-b87e-c717d52c6a12",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 64,
        "prompt_tokens": 319
      },
      "latency": 2900.221,
      "generated_output": "{\n  \"Summary\": \"The customer is reaching out to reconfirm their flight details, ensuring the flight information is correct and that luggage is included in their reservation.\",\n  \"SR Title\": \"Flight and Luggage Confirmation Request\",\n  \"SR Type\": \"Booking Confirmation\",\n  \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:53.407Z"
      },
      "expected_output": "",
      "user_message": "Passenger Name: *FULL NAME* Booking Reference: *BOOKING REFERENCE* Message: *FULL NAME* *FULL NAME* *DATE* *FLIGHT CITY CODE* - *FLIGHT CITY CODE* *FLIGHT CODE* *DATE* *FLIGHT CITY CODE* - *FLIGHT CITY CODE* *FLIGHT CODE* Email: *EMAIL* I need to reconfirm that the flight is correct and the luggage included in the reservation. Best regards",
      "iteration": 1
    },
    {
      "id": "57f44589-ea05-4515-b294-bcc9ef02ff19",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 67,
        "prompt_tokens": 266
      },
      "latency": 3366.655,
      "generated_output": "{\n  \"Summary\": \"The customer is inquiring about the possibility of changing the name on one of the purchased tickets and is willing to pay an extra fee if necessary.\",\n  \"SR Title\": \"Request for Name Change on Ticket\",\n  \"SR Type\": \"Ticket Change Request\",\n  \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:53.872Z"
      },
      "expected_output": "",
      "user_message": "Booking Reference: *BOOKING REFERENCE* Message: Good morning, I would like to know if it is possible to change the name of one of the tickets purchased, even paying an extra fee.",
      "iteration": 1
    },
    {
      "id": "7a39736d-dffb-4883-903c-3a9ca566afc5",
      "model_version": "gpt-4o-2024-08-06",
      "usage": {
        "completion_tokens": 78,
        "prompt_tokens": 340
      },
      "latency": 5624.564,
      "generated_output": "{\n  \"Summary\": \"A third party is submitting a claim for compensation on behalf of passengers who traveled on the same flight. They are referencing a specific booking and flight code and have included airline and AirHelp reference numbers.\",\n  \"SR Title\": \"Compensation Claim Submission for Passengers\",\n  \"SR Type\": \"Compensation Request\",\n  \"Sentiment\": \"Neutral\"\n}",
      "test_set": "AIR_CASES",
      "evaluated_at": {
        "$date": "2024-11-21T07:43:56.142Z"
      },
      "expected_output": "",
      "user_message": "Contact Name: *COMPANY NAME* Booking Reference: *BOOKING REFERENCE* For whom this claim is submitted? I am a third party acting on behalf of some passengers on the reservation How did you reach your destination? Travelled on same flight Additional Comments: *REFERENCE NUMBER* *FULL NAME* (*BOOKING REFERENCE*) *FLIGHT CODE* - Request for payment for fellow passengers Dear *AIRLINE*, Airline case reference: *REFERENCE NUMBER* *AIRHELP REFERENCE* With regards to the claim for compensation on behalf of our client *FULL NAME*",
      "iteration": 1
    }
  ]
}
```