import logging
import os  
import azure.functions as func
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.data.tables import TableServiceClient
import uuid 

# Import GLOBAL Variables
Sender_Domain= os.getenv("SENDER_DOMAIN")
manager_email = os.getenv("MANAGER_EMAIL")
credential=AzureKeyCredential("") #replace with your function credential 
endpoint = ("") #Replace with your endpoint
storage_string = os.getenv("AzureWebJobsStorage")


#Build the client
client = EmailClient(endpoint, credential)

#--------------- Function to populate the html template and send the email to the manager  ------------------
def send_email_to_manager(subject,email, name, start_date, end_date, message_content, recipient_email):
    # Load the HTML template from the file
    with open("leave_request_template.html", "r") as file:
        html_content = file.read()

    # Generate approve/reject URLs
    approve_url, reject_url = generate_approve_reject_urls(name, email)
    # Replace placeholders in the HTML template
    html_content = html_content.format(name=name,start_date=start_date,end_date=end_date,message_content=message_content,
        email=email,approve_link=approve_url,reject_link=reject_url)

    # Create the email message with the provided subject, content, and HTML body
    message = {
        "content": {
            "subject": subject,
            "html": html_content  # Now the HTML content is populated
        },
        "recipients": {
            "to": [
                {
                    "address": recipient_email,
                    "displayName": "Manager"
                }
            ]
        },
        "senderAddress": Sender_Domain  # Replace with your ACS sender address
    }

    try:
        # Begin sending the email
        poller = client.begin_send(message)
        result = poller.result()  # Wait for the send operation to complete
        logging.info(f"Email sent successfully, message ID: {result.message_id}")
    except HttpResponseError as e:
        logging.error(f"Failed to send email: {e.message}")


#----------------- function to parse the json file ( http request ) and send the email using previous function ---------
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
@app.route(route="http_trigger", methods=["GET", "POST"])
def email_automation_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing HTTP trigger function.')

    try:
        # Log raw request body
        raw_body = req.get_body()
        logging.info(f"Raw request body: {raw_body.decode()}")

        # Parse JSON
        try:
            req_body = req.get_json()
            logging.info(f"Parsed JSON: {req_body}")
        except ValueError as e:
            logging.error(f"Failed to parse JSON: {str(e)}")
            return func.HttpResponse(
                "Invalid JSON format in request body.",
                status_code=400
            )

        # Extract necessary fields from the form submission
        name = req_body.get('fullName')
        email = req_body.get('email')
        message_content = req_body.get('message')
        starting_date = req_body.get('startingDate') 
        ending_date = req_body.get('endingDate')

        # Log the extracted fields
        logging.info(f"Extracted fields: fullName={name}, email={email}, message={message_content}")

        # Check if all required fields are provided
        if not all([name, email, message_content, starting_date, ending_date]):
            missing_fields = []
            if not name:
                missing_fields.append('fullName')
            if not email:
                missing_fields.append('email')
            if not message_content:
                missing_fields.append('message')
            if not starting_date:
                missing_fields.append('startingDate')    
            if not ending_date:
                missing_fields.append('endingDate')                       

            logging.error(f"Missing fields: {', '.join(missing_fields)}")
            return func.HttpResponse(
                f"Missing one or more required fields: {', '.join(missing_fields)}.",
                status_code=400
            )
        logging.info(f"Form submitted: Name={name}, Email={email}, Message={message_content}")

        # Send an email to the manager with the form details
        subject = f"New form submission from {name}"
        send_email_to_manager(subject, email, name, starting_date, ending_date, message_content, manager_email)
        return func.HttpResponse(
            f"Form submission received successfully!\nName: {name}\nEmail: {email}\nMessage: {message_content} \nStartingDate: {starting_date} \nEndingDate: {ending_date}",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return func.HttpResponse(
            f"Error processing the request: {str(e)}",
            status_code=500
        )

#------------------------ Processing Managers decision and sneding email to employee ----------------
@app.route(route="http_trigger2", auth_level=func.AuthLevel.FUNCTION)
def http_trigger2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing manager's decision.")
    try:
        # Extract parameters from the query string
        status = req.params.get("status")
        name = req.params.get("name")
        email = req.params.get("email")
        token = req.params.get("token")

        # Validate required parameters
        if not status or not name or not email:
            logging.error("Missing parameters.")
            return func.HttpResponse("Missing parameters.", status_code=400)


        try:
            entity = table_client.get_entity(partition_key=email, row_key=token)
            current_status = entity.get("Status", "Pending")

            if current_status != "Pending":
                logging.info(f"Request for {name} is already processed with status: {current_status}.")
                return func.HttpResponse(f"Request already processed with status: {current_status}.", status_code=200)

        except Exception as e:
            logging.error(f"Invalid token: {e}")
            return func.HttpResponse("Invalid token.", status_code=400)
        
        # Determine the email subject and body based on the status
        if status == "approved":
            new_status = "Approved"
            subject = "Leave Request Approved"
            body = f"Hi {name},\n\nYour leave request has been approved."
        elif status == "reject":
            new_status = "Rejected"
            subject = "Leave Request Rejected"
            body = f"Hi {name},\n\nYour leave request has been rejected."
        else:
            logging.error("Invalid status parameter.")
            return func.HttpResponse("Invalid status.", status_code=400)
        
        # Update the token's status
        entity["Status"] = new_status
        table_client.upsert_entity(entity)
        
        # Prepare the email message for the employee
        email_message = {
            "senderAddress": Sender_Domain,
            "content": {"subject": subject, "plainText": body},
            "recipients": {"to": [{"address": email, "displayName": name}]},
        }

        # Send the email
        poller = client.begin_send(email_message)
        poller.result()  # Wait for the send operation to complete

        logging.info(f"Notification email sent to {name} at {email} regarding {new_status}.")
        return func.HttpResponse(f"Email sent to {name} regarding {new_status}.", status_code=200)
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse("Failed to process manager's decision.", status_code=500)


#------------------ Store manager's decision in an azure table -----------------
# Initialize the table service client
table_service_client = TableServiceClient.from_connection_string("") # replace with table connection String 
table_client = table_service_client.get_table_client(table_name="") # replace with your table name

# Function to generate unique token URLs for approve/reject
def generate_approve_reject_urls(name, email):
    # Generate a unique token for each request
    token = str(uuid.uuid4())
    
    # Store the token and status in Table Storage, unique token as the row key
    entity = {
        # Using email as the partition key
        "PartitionKey": email,"RowKey": token,"Name": name,"Status": "Pending"
    }
    table_client.upsert_entity(entity)  # Insert or update the entity in Table Storage
    # Create approve and reject URLs with the token
    approve_url = f"REPLACE{name}&email={email}&token={token}" #functionLink
    reject_url = f"REPLACEstatus=reject&name={name}&email={email}&token={token}"
    
    return approve_url, reject_url