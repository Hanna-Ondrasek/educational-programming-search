import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google import genai
import base64
import enum
from pydantic import BaseModel

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_message_body(msg_payload):
    """
    Extracts the plain text body from a message payload.
    This function is kept as-is because it's essential for getting the raw text.
    """
    if "parts" in msg_payload:
        for part in msg_payload["parts"]:
            if part["mimeType"] == "text/plain":
                if "data" in part["body"]:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
            elif "parts" in part:  # Handle nested multipart messages
                result = get_message_body(part)
                if result:
                    return result
    elif "body" in msg_payload and "data" in msg_payload["body"]:
        return base64.urlsafe_b64decode(msg_payload["body"]["data"]).decode("utf-8")
    return None


def parseStuff(body):
    print("im a newsletter")

    class Age(enum.Enum):
        INFANT = "0-1"
        TODDLER = "1-3"
        YOUNG_CHILD = "3-6"
        CHILD = "6-11"
        ADOLESCENT = "11-14"
        TEEN = "14-18"
        YOUTH = "0-18"
        ADULT = "18-65"
        SENIOR = "65-100"

    class Rating(BaseModel):
        event_name: str
        rating: Age
        event_link: str
        event_location: str

    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Parse out any events in this newsletter {body} (return nothing if there's no events) and give them the most appropriate age rating based on the context. Also provide the link to the event (if provided, usually starts with <http) and the location.",
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Rating],
        },
    )

    print(response.text)
    # client = genai.Client()

    # response = client.models.generate_content(
    #     model="gemini-2.5-flash",
    #     contents=f"Print what in this newsletter email body {body} looks like an event/program/camp/things of that nature that people are able to attend. Print the"
    #     "date, cost, name of the program, name of the organization, short description of the program, intended ages, and link to register. If there's no events or anything "
    #     "like that, don't print anything.",
    # )
    # print(response.text)
    # print(f"body:{body}")


def determineEmailType(subject):
    print("i got within this func ")
    print(subject)
    print(type(subject))
    newsletterWords = [
        "Weekly",
        "weekly",
        "Monthly",
        "monthly",
        "Update",
        "update",
        "Newsletter",
        "newsletter",
        "Digest",
        "digest",
        "Highlights",
        "highlights",
    ]

    for word in newsletterWords:
        if word in subject:
            print("Success!")
            return True

    # if we've gotten to this point, all words have been looped thru and we haven't found one
    print("not a newsletter")
    return False


def main():
    """Shows basic usage of the Gmail API and prints the raw content of emails."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=10).execute()
        messages = results.get("messages", [])

        if not messages:
            print("No messages found.")
            return

        print("Printing raw content for the last 5 messages:")
        for message in messages:
            msg_id = message["id"]
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )

            headers = msg["payload"]["headers"]
            subject = "No Subject"
            # this separates each email entry
            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                    break

            body = get_message_body(msg["payload"])
            if determineEmailType(subject):
                print("i got here")
                parseStuff(body)

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
