# python_imap_outlook365
***Description:***  
The purpose of this **Python application is to use IMAP to access a service account's mailbox via Outlook Online/Outlook 365.**  
The application looks for ***specific emails based on the subject and retreives their attachment file (Looking for specific CSV and Excel File reports).***  
From there the application uses the **DataExport class** to proceed ***with acquiring the files and then reading the files into a Pandas DataFrame and sends the data to the specified table in the Postgres Database.***  
***In my case, the Postgres Instance was via RDS service (AWS).*** **However you can use the concept to route data from excel or csv files to any database system you want (Ex: SQL Server, etc).**  
Just make sure to have the necessary driver support needed for the application to function properly. 

## Prerequisites for Working with Outlook Online
I must confess working with Microsoft Outlook Online/365 can be a real pain! Especially when you're dealing with OAuth2 for Outlook.  
Microsoft's documentation on the subject matter just provides sort of a generic overview on how to get this done. Below is the link:  
https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth

***Special thanks to my friend Juan Rosario and Codewrecks regarding the subject matter on authenticating with Imap using OAuth2!   
I could not have done this without them!*** 

Below are the prerequisites needed to make this work:
- Create an Azure App Registration (Make sure to create Client Secret and save it)
- Within API permissions via Azure App Registration do this:  
   - in **"APIs my organization uses"** search for **Office 365 Exchange Online** 
   - select **'Application permissions'** and search for **IMAP.AccessAsApp** and select it.
   - grant **"Admin consent"** within **Configured Permissions** following the previous selection
- Then you will need to connect to both Azure AD and Exchange Online via (PowerShell). ***(Make sure to install the powershell modules for Azure AD and Exchange Online)***

The following commands need to be executed via PowerShell.   **NOTE: (Make sure to be in admin mode)**
```ps1
Connect-AzureAD
$MyApp = Get-AzureADServicePrincipal -SearchString YourAzureAppName

Connect-ExchangeOnline
New-ServicePrincipal -AppId $MyApp.AppId -ServiceId $MyApp.ObjectId -DisplayName "Service Principal for IMAP APP in Azure"
Add-MailboxPermission -Identity "serviceAccount@example.com" -User $MyApp.ObjectId -AccessRights FullAccess 
```
- First thing you will need to do is sign into Azure AD using **Connect-AzureAD** command  
- Following that you will run this command: **$MyApp = Get-AzureADServicePrincipal -SearchString YourAzureAppName**  
  This command will Get the Service Principal info from the Azure App specified
  
- Next you will connect to Exchange Online using **Connect-ExchangeOnline** command
- Once connected you will proceed with creating a new Azure AD Service Principal with your newly created Azure App Registration using this:  
  **New-ServicePrincipal -AppId $MyApp.AppId -ServiceId $MyApp.ObjectId -DisplayName "Service Principal for IMAP APP in Azure"**
  
- Finally you will mailbox permissions to your app for your associated service account mailbox and grant in access rights based on what you specified:  
  **Add-MailboxPermission -Identity "serviceAccount@example.com" -User $MyApp.ObjectId -AccessRights FullAccess**
  
 Once you apply the steps mentioned above you are now ready to start using the Python application.  
 I've added a config file where you can plug in your respective values and hit the ground running. 
 
 ## Regarding the sendEmail() function via DataExport class
 ```python
  def sendEmail(self):
        custom_subject = str(self.report_name) + " " + "PostgreSQL Data Drop Complete!"
        custom_body = """
          Hi,
          
          The PostgreSQL Data Export is complete!
          
          Regards,
        """
        
        smtp_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        message = MIMEMultipart()
        message['Subject'] = custom_subject
        message['From'] = self.smtp_user
        message['To'] = self.sender
        message['Cc'] = self.smtp_cc_list
        body = custom_body
        message.attach(MIMEText(body, "plain"))

        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        smtp_server.login(self.smtp_user, self.smtp_passwd)
        smtp_server.send_message(message)
        smtp_server.quit()
        smtp_server.close()
 ```
 The objective of this function following the execution of ***reportDataDump()*** function is to proceed with **sending an email notification following the data drop of the report file to the respective SQL table in the Postgres Database.**  
 A few things to keep in mind when using SMTP with Python with an associated Outlook mailbox account. 
 - First, the account used for SMTP alerts must have the **mail settings enabled when using apps tied to it's mailbox.** 
 - Second, if **MFA is enforced on your Microsoft Tenant,** you will need to **exclude your user account for the SMTP notification via Azure Conditional Access policies.** 
 
## Docker.dockerfile and captain-definition for running on CapRover
```dockerfile
# STEP 1: Install base image. Optimized for Python.
#FROM python:3.8-slim-buster
FROM --platform=linux/amd64 python:3.8-slim-buster
# install FreeTDS and dependencies
RUN apt-get update \
 && apt-get install unixodbc -y \
 && apt-get install unixodbc-dev -y \
 && apt-get install freetds-dev -y \
 && apt-get install freetds-bin -y \
 && apt-get install tdsodbc -y \
 && apt-get install --reinstall build-essential -y \
 && apt-get -y install libpq-dev gcc \
 && pip install psycopg2

# Install dependencies for sql server drivers
RUN apt-get update \
    && apt-get install -y curl apt-transport-https \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev 


# STEP 3: Copy the source code in the current directory to the container.
# Store it in a folder named /app.
ADD . /

# STEP 4: Set working directory to /app so we can execute commands in it
WORKDIR /


# Install the rest of the requirements
RUN pip install -r requirements.txt


CMD [ "python3", "./main.py"]
```
I've included a dockerfile along with a captain-definition if you're interested in **running this application via Docker on CapRover!**  
For those not familiar with CapRover, I strongly urge you to check it out, as it's a pretty cool platform for deploying applications.  
Here's the link to get started: https://caprover.com/docs/get-started.html  

**NOTE: I added the dependencies drivers for SQL Server in the dockerfile when running on a Linux system in the event you choose to route data to a Microsoft SQL Server instance. Enjoy!**
