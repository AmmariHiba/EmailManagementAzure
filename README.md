# EmailManagementAzure
A project that automates email management using Azure Functions, Azure Communication Services, and Azure Table Storage. It facilitates the approval or rejection of leave requests through dynamically generated email links.

## Features
- Email Automation: Sends emails with approve/reject links to streamline decision-making processes.
- Serverless Architecture: Uses Azure Functions for scalable and efficient execution.
- Data Storage: Leverages Azure Table Storage for lightweight and fast storage of request metadata.
- Azure Communication Services: Handles email delivery via secure and reliable infrastructure.

## Technologies Used
- Azure Functions: For implementing serverless logic.
- Azure Communication Services: To send emails.
- Azure Table Storage: To store request data (name, email, status, etc.).
- Python: Backend programming language.
- HTML: For the email templates.
- Js : backend programming attached to the form 

## How It Works
- Leave Request Submission: An employee submits a leave request.
- Unique Token Generation: A unique token is generated for the request and stored in Azure Table Storage.
- Email Notification: The system sends an email with dynamic approve/reject links to the approver/Manager.
- Action Links: Approvers click the links, which trigger Azure Functions to update the request status in storage.
- Real-Time Updates: The updated status is stored in Table Storage and can be queried later.
- Email Notification: The system sends an email with approver/Manager's Decision to the employee.

![BPMN choreography diagram](https://github.com/user-attachments/assets/d25e5f8f-193b-4a9a-aa0a-b0accd782029)

## Setup
### Prerequisites
- Azure Subscription
- Python 3.8+
- Azure CLI
- Visual Studio Code (optional, for local development)

1. Clone the Repository
2. Install Dependencies ( requirements.txt file )
3. Configure Environment Variables (Manager's email , function app keys , azureEmailDomain , Storage Account, Apis ) 
4. Deploy to Azure


