function onFormSubmit(e) {
    let responses = []; // Initialize responses array
  
    if (!e) {
      Logger.log("Running in test mode.");
  
      // Open the form and fetch all responses for testing
      var form = FormApp.openById('1TX5VvJgkJ5rT7wo8Dcny1molTAkoLTsRztF2Yy-bQ2A');
      var allResponses = form.getResponses();
  
      if (allResponses.length === 0) {
        Logger.log("No form responses available for testing.");
        return;
      }
  
      // Simulate the `e.values` array from the last response
      responses = allResponses[allResponses.length - 1]
                    .getItemResponses()
                    .map(item => item.getResponse());
    } else {
      Logger.log("Processing form submission.");
  
      // Initialize an object to hold form data
      let formData = {};
  
      // Extract form responses
      if (e.response) {
        const formResponses = e.response.getItemResponses();
  
        formResponses.forEach(response => {
          const question = response.getItem().getTitle(); // Get question title
          const answer = response.getResponse(); // Get answer
          formData[question] = answer; // Map question to answer
        });
  
        // Retrieve the respondent's email address (if "Collect email addresses" is enabled)
        const email = e.response.getRespondentEmail();
        if (!email) {
          Logger.log("No email address found for the respondent.");
          return;
        }
  
        // Add the email to the formData object
        formData["Adresse e-mail"] = email;
  
        Logger.log("Form data: " + JSON.stringify(formData));
  
        // Prepare payload for Azure function
        const azurePayload = {
          email: formData["Adresse e-mail"],
          fullName: formData["Full name"],
          message: formData["Message "],
          startingDate : formData["Starting Date "],
          endingDate : formData["Ending Date"]
  
        };
  
        Logger.log("Azure payload: " + JSON.stringify(azurePayload));
  
        // Azure function endpoint
        const azureFunctionUrl = "https://emailmanagement12.azurewebsites.net/api/http_trigger?code=_1QAaVi5fED4bDgynaf1Jj58-SF39Wkd-iioUnQgrsWgAzFuWcg5sw%3D%3D";
  
        // Make an HTTP POST request to the Azure function
        const options = {
          method: "post",
          contentType: "application/json",
          payload: JSON.stringify(azurePayload)
        };
  
        try {
          const response = UrlFetchApp.fetch(azureFunctionUrl, options);
          Logger.log("Azure response: " + response.getContentText());
        } catch (error) {
          Logger.log("Error sending request to Azure: " + error.message);
        }
      } else {
        Logger.log("No response data found in event object.");
      }
    }
  }
  