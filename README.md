# Customizable chatbot

This repository provides the instructions and code needed to create a customized chatbot that can be embedded into a Qualtrics survey. You can define various model parameters to achieve the desired chatbot behavior. Additionally, the code includes an option for randomization, allowing you to use different model specifications to compare behaviors. This enables easy customization of LLMs to suit your requirements and facilitates their integration into Qualtrics for conducting experiments.

## FIRST, you'll need:
- An account with the OpenAI API.

You'll need to set up a payment method and get an API key (https://platform.openai.com/docs/api-reference/authentication).

- A mySQL database hosted online.

In this tutorial, I'll be using google cloud for hosting. It's one of the easiest ways to do it. If you want to do it the same way, you'll have to create an account and set up payment method.(https://console.cloud.google.com).
You will also need to create a database and get all its credentials (user, passoword, IP, port)
- A Streamlit account.

A free account works.
- A Github account.

You need it to launch you project in streamlit.

- A code editor installed on your computer. I recommend VSCode. 

### Step 1: Fork it
Fork this repository in your own github. This will create a copy of all these files in your own github account. 

### Step 2: OpenAI API key
Figure out your OpenAI API key and the credentials for the google cloud SQL databsabe.

### Step 3: Streamlit
Create an app on streamlit and select the forked github repo as the source.
Under your app, go to settings and set up all the secrets in there (API_KEY, sql_user, sql_password, sql_host, sql_port, sql_database).

### Step 4: Set up MySQL database on Google Cloud
Create an instance, create a database, get all your keys.

### Step 5: Qualtrics
Create a new qualtrics survey and create a Text/Graphic question.
Under "Question Behavior" select "javascript".
Paste the following code (make sure to substitute the values in [YOUR-DOMAIN] by the name of your streamlit app).

```
Qualtrics.SurveyEngine.addOnload(function() {
    // Create the iframe element
    var iframe = document.createElement('iframe');
    var userID = "${e://Field/ResponseID}";  // Fetch the ResponseID from Qualtrics

    // Set the source of the iframe to your chatbot's URL
    iframe.src = "https://conversationfriends.streamlit.app/?type=PERSON2&embedded=true&userID=${e://Field/ResponseID}";

    // Increase the height of the iframe
    iframe.style.width = '100%';  // Take the full width of the parent container
    iframe.style.height = '550px'; // Adjust the height to show more content
    iframe.style.border = 'none';  // Remove any default borders
    iframe.style.overflow = 'hidden';  // Hide overflow content

    // Find a placeholder in your Qualtrics question
    var placeholder = document.getElementById('chatbotPlaceholder');
    placeholder.style.position = 'relative';
    placeholder.style.overflow = 'hidden'; // Ensure container overflow is hidden

    // Append the iframe to the placeholder
    placeholder.appendChild(iframe);

    // Create a mask to hide the bottom 50px that contains the streamlit logo
    var maskDiv = document.createElement('div');
    maskDiv.style.position = 'absolute';
    maskDiv.style.bottom = '0';
    maskDiv.style.left = '0';
    maskDiv.style.width = '100%';
    maskDiv.style.height = '60px';  // Adjust height as needed to cover the icons
    maskDiv.style.backgroundColor = 'white';  // Match background color of your app
    maskDiv.style.zIndex = '9999';  // Ensure it sits on top of the iframe

    // Append the mask div on top of the iframe
    placeholder.appendChild(maskDiv);
});
```

In addition to the javascript, you need to add the chatbot element to html.

Go to the question where you want to display the chatbot. Click on the question to edit it and select "HTML View". Paste the following following element by the end of the text:

```
<div id="chatbotPlaceholder">&nbsp;</div>
```

### Step 6: Publish the survey and test it.
For testing, you'll chat with the chatbot. To make sure it's working:
- ensure there are no error messages;
- ensure that your data is recorded properly on your database by downloading it from google cloud and checking if all fields are filled correctly (user id, date, time, content).

### Step 7: Customize it!
Now that the app is working, customize the app. To change the chatbot behavior, there are two main things you can do:
1) change the message on "start_message", where we tell the system how to behave.
2) Changing and adding arguments to the "openai.ChatCompletion.create". There are many thing you can change (max number of tokens used, you can penalize certain words to decrease their frequency, change system temperature, etc.). You can check how to do it in https://platform.openai.com/docs/guides/gpt

And there you have it!

#### Update 06/03/24
Thanks to Conrado Eiroa Solans, now this web app works better.
Issues fixed: 
- participants can now send the message by just pressing enter
- conversation is scrolled down automatically
- appearance is better

# How to cite this
Oldemburgo de Mello, Victoria. 2024. Customizable chatbot. GitHub. github.com/vicomello/customizable_chatbot


