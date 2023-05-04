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
 
